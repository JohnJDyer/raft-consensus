
import enum
import signal
import random
import asyncio
import heapq
import uuid
import functools
import traceback
import socket
import os

import raft.raft_pb2 as raft_pb2

from raft.util import RaftDebugger, ignore_stale

# TODO: implement signal handlers.
# TODO: multiplex commands + logs
# TODO: create isready method to block until leader known leader OR queue up messages.
# TODO: Snapshotting. Maybe use loop.sock_sendfile()

class ACT(enum.Enum):
    NO_OP      = enum.auto()
    TIMEOUT    = enum.auto()
    NEW_TERM   = enum.auto()
    NEW_LEADER = enum.auto()
    MAJORITY   = enum.auto()
    START      = enum.auto()
    ERROR      = enum.auto()


class STATE(enum.Enum):
    FOLLOWER   = enum.auto()
    CANDIDATE  = enum.auto()
    LEADER     = enum.auto()
    OFF        = enum.auto()
    ERROR      = enum.auto()


class Raft(RaftDebugger):

    TRANSITIONS = {
        STATE.OFF: {
            ACT.START:      STATE.FOLLOWER,
        },
        STATE.FOLLOWER: {
            ACT.TIMEOUT:    STATE.CANDIDATE,
            ACT.NEW_LEADER: STATE.FOLLOWER,
            ACT.NEW_TERM:   STATE.FOLLOWER,
        },
        STATE.CANDIDATE: {
            ACT.TIMEOUT:    STATE.CANDIDATE,
            ACT.MAJORITY:   STATE.LEADER,
            ACT.NEW_LEADER: STATE.FOLLOWER,
            ACT.NEW_TERM:   STATE.FOLLOWER,
        },
        STATE.LEADER: {
            ACT.NEW_TERM:   STATE.FOLLOWER,
            # ACT.TIMEOUT:    ACT.LEADER,
        },
    }

    def __init__(
            self,
            id,
            server_ids,
            listen_address='0.0.0.0',
            send_address='<broadcast>',
            port=27182,
            debug=1,
            execute_callback=None,
            ):

        self.id = uuid.uuid4().int % (1 << 62) if id is None else id

        self.port = port
        self.listen_address = listen_address
        self.send_address = send_address

        self.term    = 0
        self.servers = {}
        self.quorum  = len(server_ids) // 2 + 1
        self.state   = STATE.OFF

        entry         = raft_pb2.LogEntries()
        entry.term    = self.term
        entry.command = "Start Up".encode('utf-8')

        self.log = [entry]
        self.execute_idx = 0  # monotonic
        self.commit_idx  = 0  # monotonic
        self.execute_callback = execute_callback

        # Do we need this:
        self.msg_idx = {s: 1 for s in server_ids}
        self.log_idx = {s: 1 for s in server_ids}

        self.new_term()
        self.election_timeout_ = 100

        self.service_task    = None
        self.heartbeat_event = asyncio.Event()
        self.command_queue   = asyncio.PriorityQueue()  # TODO We could limit features to make FIFO work.

        self.transport = None

        self.DISPATCH_TABLE = {
            STATE.FOLLOWER: {
                raft_pb2.RaftUDPMessage.HEART:   [self.handle_heartbeat],
                raft_pb2.RaftUDPMessage.POLL:    [self.handle_poll],
                raft_pb2.RaftUDPMessage.APPEND:  [self.run_append],
            },
            STATE.CANDIDATE: {
                raft_pb2.RaftUDPMessage.VOTE:    [self.handle_vote],
            },
            STATE.LEADER: {
                raft_pb2.RaftUDPMessage.COMMAND: [self.handle_status, self.handle_command],
                raft_pb2.RaftUDPMessage.STATUS:  [self.handle_status],
            },
        }

        self.SERVICES = {
            STATE.FOLLOWER : self.service_failure_detector,
            STATE.CANDIDATE: self.service_election,
            STATE.LEADER   : self.service_heartbeat}

        RaftDebugger.__init__(self, debug=debug)

    async def listen(self):

        class UDPBroadcast(asyncio.DatagramProtocol):
            def datagram_received(__, data, addr):
                self.udp_callback(data, addr)

        self.transport, _protocol = await asyncio.get_event_loop().create_datagram_endpoint(
            protocol_factory=lambda: UDPBroadcast(),
            allow_broadcast=True,
            local_addr=(self.listen_address, self.port))

    def __repr__(self):
        return f"Raft({self.state}, commited {self.commit_idx + 1} of {len(self.log)} log entries)"

    def __del__(self):
        # TODO graceful shutdown server via state transition.
        if self.transport:
            self.transport.close()

    async def start(self):
        await self.listen()
        self.transition(ACT.START)
        return self

    def new_term(self, term=0):
        self.term       = max(self.term + 1, term)
        self.vote_cast  = False
        self.leader     = None
        self.supporters = set()

    def udp_broadcast(self, message_type, log_idx=float("inf"), leader=None, command=None):
        leader = self.leader if leader is None else leader

        msg = raft_pb2.RaftUDPMessage()
        msg.type       = message_type
        msg.term       = self.term
        msg.sender     = self.id
        msg.commit_idx = self.commit_idx

        if leader is not None:
            msg.leader = leader

        msg.log_idx = min(log_idx, len(self.log))

        if command is not None:
            msg.command = command
        else:
            msg.log.extend(self.log[msg.log_idx:])

        self.transport.sendto(msg.SerializeToString(), (self.send_address, self.port))

    # ================= DATABASE ==================

    def commit(self, commit_idx):
        if commit_idx > self.commit_idx:
            self.commit_idx = min(commit_idx, len(self.log) - 1)
            self.execute()
            # TODO This feels heavy; better way?
            asyncio.create_task(self.signal_commands())

    def execute(self):
        while self.execute_idx < self.commit_idx:
            self.execute_idx += 1
            if self.execute_callback:
                self.execute_callback(self)

    # TODO This feels heavy; better way?
    async def signal_commands(self):
        while not self.command_queue.empty() and self.command_queue._queue[0][0] <= self.commit_idx:
            _, _, event = await self.command_queue.get()
            event.set()

    # ================= TRANSPORT PROTOCOLS ==================

    def udp_callback(self, data, addr):
        message = raft_pb2.RaftUDPMessage()
        message.ParseFromString(data)
        self.handle_message(message=message)

    def handle_message(self, message):
        if self.term < message.term:
            self.new_term(message.term)
            self.transition(ACT.NEW_TERM)

        for f in self.DISPATCH_TABLE.get(self.state, {}).get(message.type, []):
            action = f(message=message)
            if action: self.transition(action)

    # ================= SERVICES ==================

    async def service_failure_detector(self):
        while True:
            try:
                await asyncio.wait_for(self.heartbeat_event.wait(), timeout=1.1)
                self.heartbeat_event.clear()
            except asyncio.TimeoutError:
                self.transition(ACT.TIMEOUT)

    async def service_heartbeat(self):
        while True:
            self.udp_broadcast(raft_pb2.RaftUDPMessage.HEART)
            await asyncio.sleep(.5)

    async def service_election(self):
        while True:
            self.new_term()
            self.supporters = {self.id}
            self.udp_broadcast(raft_pb2.RaftUDPMessage.POLL, leader=self.id)
            await asyncio.sleep(random.uniform(150, 300) / 1000)

    # ================= STATE MACHINE ==================

    def transition(self, action):
        s = Raft.TRANSITIONS.get(self.state, {}).get(action, STATE.ERROR)

        if self.state != s:
            if self.service_task is not None:
                self.service_task.cancel()
            self.state = s
            service = self.SERVICES[s]
            self.service_task = asyncio.create_task(service())

    # ================= SEND MESSAGE ==================

    def send_logs(self):
        msg_idx = min(self.msg_idx.values())
        if msg_idx < len(self.log):
            self.udp_broadcast(raft_pb2.RaftUDPMessage.APPEND, log_idx=msg_idx - 1)

    # TODO: shield from cancellation?
    # TODO: retry sending message?
    # TODO: timeout?
    async def send_command(self, command, idx=-1):
        """
        Replicate command (bytes) in every server's logs at position idx. If command depends on raft.log then do:
          (1) n=len(raft.log)
          (2) message = F(raft.log)
          (3) send_command(message, idx=n)
          This guarantees the log/state machine has not changed since message calculation. Returns true when message is
          COMMITED to the local log and false if message cannot be applied at position idx. Use idx=-1 for simple
          append.
        :param command: bytes
        :param idx: int, target log index; -1 for any index
        :return: bool, True if message successfully COMMITED.
        """

        self.udp_broadcast(raft_pb2.RaftUDPMessage.COMMAND, command=command, log_idx=idx)
        event = asyncio.Event()
        self.command_queue.put_nowait((idx, command, event))
        await event.wait()
        return self.log[idx].command == command  # TODO: assumes commands are unique.

    def send_command_nowait(self, command, idx=-1):
        return asyncio.create_task(self.send_command(command, idx=idx))

    # ================ OTHER STUFF ====================

    @ignore_stale
    def handle_heartbeat(self, message):
        if self.leader is None:
            self.leader = message.leader
            return ACT.NEW_LEADER

        self.heartbeat_event.set()
        if not len(message.log):
            return
        if not self.merge_logs(message):
            self.udp_broadcast(raft_pb2.RaftUDPMessage.STATUS, log_idx=len(self.log) - 1)

    @ignore_stale
    def handle_command(self, message):
        entry = raft_pb2.LogEntries()
        entry.term = self.term
        entry.command = message.command

        if message.log_idx == -1 or message.log_idx == len(self.log):
            self.log.append(entry)
            self.msg_idx[self.id] = len(self.log)
            self.log_idx[self.id] = len(self.log)
        self.send_logs()

    @ignore_stale
    def handle_poll(self, message):
        if self.vote_cast or len(self.log) > message.log_idx:
            return
        self.vote_cast = True
        print("Vote Cast")
        self.udp_broadcast(raft_pb2.RaftUDPMessage.VOTE, leader=message.leader)

    @ignore_stale
    def handle_vote(self, message):
        if message.leader == self.id:
            self.supporters.add(message.sender)

            if len(self.supporters) >= self.quorum:
                self.leader = self.id
                return ACT.MAJORITY

    def handle_status(self, message):
        for idx, log_entry in enumerate(message.log, message.log_idx):
            if idx < len(self.log):
                if self.log[idx].term == log_entry.term:
                    self.msg_idx[message.sender] = idx + 1
                    self.log_idx[message.sender] = idx + 1

                    if self.log[idx].term == self.term and idx > self.commit_idx:
                        best_idx = heapq.nlargest(self.quorum, self.log_idx.values())[-1] - 1
                        self.commit(best_idx)
                else:
                    self.msg_idx[message.sender] = idx
                    break
            else:
                break

        if self.msg_idx.get(message.sender, 0) < len(self.log) or message.commit_idx < self.commit_idx:
            self.send_logs()

    @ignore_stale
    def run_append(self, message):
        assert len(message.log) >= 2
        self.merge_logs(message)
        self.udp_broadcast(raft_pb2.RaftUDPMessage.STATUS, log_idx=len(self.log) - 1)
        self.commit(message.commit_idx)
        return

    # ======= HELPERS =========

    def merge_logs(self, message):
        if message.log_idx >= len(self.log):
            return False

        if message.log[0].term == self.log[message.log_idx].term:
            idx = max((i for i, (a, b) in enumerate(zip(message.log, self.log[message.log_idx:])) if a.term == b.term)) + 1
            self.log = self.log[:message.log_idx + idx]
            self.log.extend(message.log[idx:])
            return message.log_idx + idx == len(self.log)
        else:
            self.log = self.log[:message.log_idx]

        return False
