# Raft Consensus

#### About Raft
 * [Raft](https://raft.github.io/ "Raft")
 * [Raft Paper](https://raft.github.io/raft.pdf "raft.pdf")
 * [Wikipedia](https://en.wikipedia.org/wiki/Raft_(algorithm) "Wikipedia")
 * [Ongaro PhD Thesis (Stanford 2014)](https://web.stanford.edu/~ouster/cgi-bin/papers/OngaroPhD.pdf "OngaroPhD")

#### Supported Features

- [x] Leader Election
- [x] Log Replication
- [ ] Persistence
- [ ] Membership Changes
- [ ] Log Compaction

#### Implementation
 * UDP Broadcast
 * Protocol Buffers
 * Python
 * Asynchronous

#### Install

```
# PYTHON3.7 REQUIRED!
# PYTHON3.8 REQUIRED for Windows (untested)
# TODO: relax dependencies.

pip install -i https://test.pypi.org/simple/ raft-consensus
```

#### Usage

```python

import asyncio
import random
import uuid

from raft import Raft


def execute_callback(raft):
    print(
        f"Exec {raft.execute_idx}: {raft.log[raft.execute_idx].command.decode('utf-8')} {raft.state}")


async def main():
    
    ID = 3 # Different for every server

    raft = await Raft(
        id=ID, 
        server_ids={0,1,2,3,4}, 
        execute_callback=execute_callback)

    await raft.start()

    while True:
        await asyncio.sleep(random.uniform(1, 10) / 1)
        msg = f"{str(uuid.uuid4())[:8]} from server {ID}"
        success = await raft.send_command(msg.encode('utf-8'))


asyncio.run(main())

```
