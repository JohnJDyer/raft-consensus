import asyncio
import socket

from contextlib import asynccontextmanager


class UDPBroadcast(asyncio.DatagramProtocol):
    def __init__(self, callback):
        self.callback = callback

    def datagram_received(self, data, addr):
        self.callback(data, addr)


@asynccontextmanager
async def get_udp_transport():
    transport, _protocol = await asyncio.get_running_loop().create_datagram_endpoint(
        protocol_factory=asyncio.DatagramProtocol,
        allow_broadcast=True,
        local_addr=("0.0.0.0", 37020),
        family=socket.AF_INET,
        reuse_port=True,
        reuse_address=True,
        proto=socket.IPPROTO_UDP)

    try:
        yield transport
    finally:
        transport.close()