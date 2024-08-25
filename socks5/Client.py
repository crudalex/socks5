import asyncio
import logging

logger = logging.getLogger(__name__)


class Client(asyncio.Protocol):

    def __init__(self) -> None:
        super().__init__()
        self.transport = None
        self.server_transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.server_transport = None
        logger.debug("Client connection made.")

    def data_received(self, data):
        logger.debug("Received data from client: %s", data)
        if self.server_transport:
            self.server_transport.write(data)

    def connection_lost(self, exc):
        if self.server_transport:
            self.server_transport.close()
        logger.debug("Client connection lost.")
