#!/usr/bin/env python3.7

import asyncio
import random
import uuid
import sys
import argparse

from raft import Raft

import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.WARNING)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id',           dest="id",    type=int)
    parser.add_argument('--server_count', dest="server_count", type=int)
    args = parser.parse_args()

    id_  = args.id
    server_ids = set(range(args.server_count))

    return id_, server_ids


async def main():

    id_, server_ids = parse_args()

    def execute_callback(x):
        print(
            f"Exec {raft.execute_idx}: {raft.log[raft.execute_idx].command.decode('utf-8')} {raft.state}")

    raft = await Raft(
        id=id_,
        server_ids=server_ids,
        execute_callback=execute_callback).start()

    while True:
        await asyncio.sleep(random.uniform(1, 10) / 1)
        msg = f"{str(uuid.uuid4())[:8]} from server {id_}"
        success = await raft.send_command(msg.encode('utf-8'))


if __name__ == "__main__":
    DEBUG = True
    asyncio.run(main(), debug=DEBUG)
