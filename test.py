#!/usr/bin/env python3.8

import asyncio
import random

from raft import Raft
from udp_broadcast import get_udp_transport


async def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    async with get_udp_transport() as transport:
        raft = Raft(transport).start()
        while True:
            await asyncio.sleep(random.uniform(1, 10) / 1)
            raft.send_command("hello world")


if __name__ == "__main__":
    DEBUG = True
    asyncio.run(main(), debug=DEBUG)
