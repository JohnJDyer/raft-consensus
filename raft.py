#!/usr/bin/env python3.8

import traceback
import socket
import os
import enum
import signal
import random
import asyncio
import heapq

from collections import namedtuple
from udp_broadcast import UDPBroadcast

import raft_pb2
from util import get_ip

Server = namedtuple("Server", ["ip_addr", "pid"])


class RaftState(enum.Enum):
    FOLLOWER  = enum.auto()
    CANDIDATE = enum.auto()
    LEADER    = enum.auto()
    OFF       = enum.auto()
    ERROR     = enum.auto()


class RaftAction(enum.Enum):
    NO_OP      = enum.auto()
    TIMEOUT    = enum.auto()
    NEW_TERM   = enum.auto()
    NEW_LEADER = enum.auto()
    MAJORITY   = enum.auto()
    START      = enum.auto()
    ERROR      = enum.auto()


def ignore_stale(f):
    def out(self, message):
        assert message.term <= self.term
        if message.term < self.term:
            return
        return f(self, message)
    return out


def log_exceptions(f):
    def out(self, message):
        try:
            return f(self, message)
        except Exception as e:
            print(e)
            traceback.print_stack()
    return out


# TODO Bug: when leader changed commits have a lag
# TODO Bug: initialize msg_idx and log_idx
# TODO Bug: first commit has a delay; it must be waiting for heatbeat
# TODO: implement signal handlers.

class Raft:

    TRANSITIONS = {
        RaftState.OFF: {
            RaftAction.START: RaftState.FOLLOWER,
        },
        RaftState.FOLLOWER: {
            RaftAction.TIMEOUT:    RaftState.CANDIDATE,
            RaftAction.NEW_LEADER: RaftState.FOLLOWER,
            RaftAction.NEW_TERM:   RaftState.FOLLOWER,
        },
        RaftState.CANDIDATE: {
            RaftAction.TIMEOUT:    RaftState.CANDIDATE,
            RaftAction.MAJORITY:   RaftState.LEADER,
            RaftAction.NEW_LEADER: RaftState.FOLLOWER,
            RaftAction.NEW_TERM:   RaftState.FOLLOWER,
        },
        RaftState.LEADER: {
            RaftAction.NEW_TERM:   RaftState.FOLLOWER,
            # RaftAction.TIMEOUT:    RaftState.LEADER,
        },
    }

    def __init__(self, transport):
        self.me          = Server(ip_addr=socket.inet_aton(get_ip()), pid=os.getpid())
        self.term       = 0
        self.quorum      = 3

        entry         = raft_pb2.LogEntries()
        entry.term    = self.term
        entry.command = "Start Up".encode('utf-8')

        self.log = [entry]
        self.execute_idx = 0  # monotonic
        self.commit_idx  = 0  # monotonic

        # Do we need this:
        self.msg_idx = {}  # TODO: should initialize
        self.log_idx = {}  # TODO: must initialize

        self.new_term()
        self.election_timeout_ = 100

        self.service_task    = None
        self.heartbeat_event = asyncio.Event()

        self.state = RaftState.OFF

        self.transport = transport
        self.transport.set_protocol(UDPBroadcast(self.udp_callback))

        self.DISPATCH_TABLE = {
            RaftState.FOLLOWER: {
                raft_pb2.RaftUDPMessage.HEART:  [self.handle_heartbeat],
                raft_pb2.RaftUDPMessage.POLL:   [self.handle_poll],
                raft_pb2.RaftUDPMessage.APPEND: [self.run_append],
            },
            RaftState.CANDIDATE: {
                raft_pb2.RaftUDPMessage.VOTE:  [self.handle_vote],
            },
            RaftState.LEADER: {
                raft_pb2.RaftUDPMessage.COMMAND: [self.handle_status, self.handle_command],
                raft_pb2.RaftUDPMessage.STATUS:  [self.handle_status],
            },
        }

        self.SERVICES = {
            RaftState.FOLLOWER : self.service_failure_detector,
            RaftState.CANDIDATE: self.service_election,
            RaftState.LEADER   : self.service_heartbeat}

        self.SIGNAL_CALLBACKS = {
            RaftState.FOLLOWER:  {
                signal.SIGINT:  None,
                signal.SIGTERM: None,
            },
            RaftState.CANDIDATE: {
                signal.SIGINT:  None,
                signal.SIGTERM: None,
            },
            RaftState.LEADER:    {
                signal.SIGINT:  None,
                signal.SIGTERM: None,
            },
        }

        print(f"I am {self.me}")

    def start(self):
        self.transition(RaftAction.START)
        return self

    def new_term(self):
        self.term      = self.term + 1
        self.vote_cast  = False
        self.leader     = None
        self.supporters = set()

    def udp_broadcast(self, message_type, log_idx=float("inf"), leader=None, command=None):
        leader = self.leader if leader is None else leader

        msg = raft_pb2.RaftUDPMessage()
        msg.message_type    = message_type
        msg.term            = self.term
        msg.sender.pid      = self.me.pid
        msg.sender.ip_addr  = self.me.ip_addr
        msg.commit_idx      = self.commit_idx

        if leader is not None:
            msg.leader.pid     = leader.pid
            msg.leader.ip_addr = leader.ip_addr

        if command is not None:
            msg.command = command.encode('utf-8')

        msg.log_idx = min(log_idx, len(self.log))
        msg.log.extend(self.log[msg.log_idx:])

        self.transport.sendto(msg.SerializeToString(), ('<broadcast>', 37020))

    # ================= DATABASE ==================

    def commit(self, commit_idx):
        if commit_idx > self.commit_idx:
            self.commit_idx = min(commit_idx, len(self.log) - 1)
            self.execute()

    def execute(self):
        while self.execute_idx < self.commit_idx:
            self.execute_idx += 1
            print(f"Applied {self.execute_idx}: {self.log[self.execute_idx].command}")

    # ================= TRANSPORT PROTOCOLS ==================

    def udp_callback(self, data, addr):
        message = raft_pb2.RaftUDPMessage()
        message.ParseFromString(data)
        self.handle_message(message)

    def handle_message(self, message):
        if self.term < message.term:
            self.new_term()
            self.transition(RaftAction.NEW_TERM)

        # This guys should no longer be allowed to transition
        for f in self.DISPATCH_TABLE.get(self.state, {}).get(message.message_type, []):
            action = f(message=message)
            if action: self.transition(action)

    # ================= SERVICES ==================

    async def service_failure_detector(self):
        while True:
            try:
                await asyncio.wait_for(self.heartbeat_event.wait(), timeout=1.)
                self.heartbeat_event.clear()
            except asyncio.TimeoutError:
                self.transition(RaftAction.TIMEOUT)

    async def service_heartbeat(self):
        while True:
            self.udp_broadcast(raft_pb2.RaftUDPMessage.HEART)
            await asyncio.sleep(.01)

    async def service_election(self):
        while True:
            self.new_term()
            self.supporters = {self.me}
            self.udp_broadcast(raft_pb2.RaftUDPMessage.POLL, leader=self.me)
            await asyncio.sleep(random.uniform(150, 300) / 1000)

    # ================= STATE MACHINE ==================

    def transition(self, action):
        s = Raft.TRANSITIONS.get(self.state, {}).get(action, RaftState.ERROR)

        if self.state != s:
            print(f"{self.state} -> {s}")
            if self.service_task is not None:
                self.service_task.cancel()
            self.state = s
            service = self.SERVICES[s]
            self.service_task = asyncio.create_task(service())

    # ================= SEND MESSAGE ==================

    def send_logs(self):
        msg_idx = min(self.msg_idx.values(), default=1)

        # TODO: when would this not be true?
        if msg_idx < len(self.log):
            print(f"ORDER APPEND {self.msg_idx.values()} {msg_idx}")
            self.udp_broadcast(raft_pb2.RaftUDPMessage.APPEND, log_idx=msg_idx - 1)

    def send_command(self, command):
        self.udp_broadcast(raft_pb2.RaftUDPMessage.COMMAND, command=command)

    # ================ OTHER STUFF ====================

    @ignore_stale
    def handle_heartbeat(self, message):
        if self.leader is None:
            leader = Server(ip_addr=message.leader.ip_addr, pid=message.leader.pid)
            self.leader = leader
            return RaftAction.NEW_LEADER

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
        self.log.append(entry)
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
        supporter = Server(ip_addr=message.sender.ip_addr, pid=message.sender.pid)
        leader    = Server(ip_addr=message.leader.ip_addr, pid=message.leader.pid)

        if leader == self.me:
            self.supporters.add(supporter)
            print(f"Tally Votes {len(self.supporters)}")
            if len(self.supporters) >= self.quorum:
                self.leader = self.me
                return RaftAction.MAJORITY

    def handle_status(self, message):
        sender = Server(ip_addr=message.sender.ip_addr, pid=message.sender.pid)

        for idx, log_entry in enumerate(message.log, message.log_idx):
            if idx < len(self.log):
                if self.log[idx].term == log_entry.term:
                    self.msg_idx[sender] = idx + 1
                    self.log_idx[sender] = idx + 1

                    if self.log[idx].term == self.term and idx > self.commit_idx:
                        best_idx = heapq.nlargest(self.quorum, self.log_idx.values())[-1] - 1
                        self.commit(best_idx)

                else:
                    self.msg_idx[sender] = idx
                    break
            else:
                break

        if self.msg_idx.get(sender, 0) < len(self.log) or message.commit_idx < self.commit_idx:
            self.send_logs()

    @log_exceptions
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
