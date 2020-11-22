import socket
import inspect
import functools


class RaftDebugger:
    def __init__(self, debug):
        self.debug = debug
        self.summary_snap   = {}

        if self.debug:

            for n, f in inspect.getmembers(self):
                if inspect.ismethod(f) and n not in RaftDebugger.__dict__.keys():
                    if True:
                        setattr(self, n, self.method_wrapper(f))

            self.summary_snap = self.summarize()

    def method_wrapper(self, f):
        @functools.wraps(f)
        def _f(*args, **kwargs):
            #print(f"{f.__qualname__}")

            out = f(*args, **kwargs)

            # for k, v in summary_snap.items():
            #     _v = self.summary_snap.get(k, None)
            #     if v != _v:
            #         print(f"  {k}: {_v} -> {v}")

            # if self.raft_state.get("supporters", set()) != raft_state["supporters"]:
            #     print(f"Tally Votes {raft.supporters}")

            # self.summary_snap = self.summarize()

            return out
        return _f

    # TODO: log exceptions.

    def summarize(self):
        # return {n: v for n, v in self.__dict__.items() if type(v) in {int, bool}}
        return {"execute_idx": self.execute_idx}


def ignore_stale(f):
    @functools.wraps(f)
    def out(self, message):
        assert message.term <= self.term
        if message.term < self.term:
            return
        return f(self, message)
    return out