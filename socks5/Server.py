import asyncio
import logging
import socket
from struct import pack, unpack
from .Client import Client

logger = logging.getLogger(__name__)


class Server(asyncio.Protocol):
    INIT, HOST, DATA = 0, 1, 2

    def __init__(self, timeout):
        self.timeout = timeout
        self.transport = None
        self.client_transport = None
        self.state = None

    def connection_made(self, transport):
        peername = transport.get_extra_info("peername")
        logger.debug("Connection from: %s", peername)
        self.transport = transport
        self.state = self.INIT

    def connection_lost(self, exc):
        if self.transport:
            self.transport.close()
        logger.debug("Server connection lost.")

    def data_received(self, data):
        logger.debug("Received data from client: %s", data)
        if self.state == self.INIT:
            assert data[0] == 0x05
            self.transport.write(
                pack(
                    "!BB",
                    # SOCKS5 (\x05)
                    0x05,
                    # "no authentication required" (\x00)
                    0x00,
                )
            )

            self.state = self.HOST
            logger.debug("Sent no-auth response to client.")

        elif self.state == self.HOST:
            ver, cmd, _, atype = data[:4]
            assert ver == 0x05 and cmd == 0x01

            if atype == 3:  # The address is a domain name.
                # the length of the domain is stored at the 5th byte (data[4]).
                length = data[4]
                hostname, nxt = (
                    # hostname is set to the domain name
                    data[5 : 5 + length],
                    # nxt is updated to point to the byte after the domain name.
                    5 + length,
                )
            elif atype == 1:  # The address is an IPv4 address
                # the next 4 bytes (data[4:8]) are converted to a human-readable IP address using socket.inet_ntop
                hostname, nxt = socket.inet_ntop(socket.AF_INET, data[4:8]), 8

            elif atype == 4:  # The address is an IPv6 address
                # the next 16 bytes (data[4:20]) are converted to a human-readable IP address using socket.inet_ntop
                hostname, nxt = socket.inet_ntop(socket.AF_INET6, data[4:20]), 20

            port = unpack(
                # The !H format string indicates a big-endian unsigned short (2 bytes).
                "!H",
                # port number is extracted from the next 2 bytes after the address
                data[nxt : nxt + 2],
            )[0]

            logger.debug("Target: %s:%s", hostname, port)
            asyncio.ensure_future(self.connect(hostname, port))
            self.state = self.DATA

        elif self.state == self.DATA:
            if self.client_transport:
                self.client_transport.write(data)
                logger.debug("Forwarded data to target server.")

    async def connect(self, hostname, port):
        try:
            loop = asyncio.get_event_loop()

            target_transport, target_client = await asyncio.wait_for(
                loop.create_connection(Client, hostname, port), timeout=self.timeout
            )

            # allows the target server to send data back to the client
            target_client.server_transport = self.transport

            # allows the client to send data to the target server
            self.client_transport = target_transport

            # ^ enable bidirectional communication between the client and the target server

            # retrieves the local socket's IP address and port number.
            hostip, port = target_transport.get_extra_info("sockname")

            host = unpack(
                # converts the 4-byte binary format into an unsigned integer. The !I format string specifies a big-endian unsigned integer.
                "!I",
                # converts the IP address from its string representation (e.g., "127.0.0.1") to a 4-byte packed binary format
                socket.inet_aton(hostip),
            )[0]
            # creates a binary response using the specified format string.
            response = pack(
                # ! - Network (big-endian) byte order.
                "!BBBBIH",
                # BBBB - Four unsigned bytes.
                0x05,
                0x00,
                0x00,
                0x01,
                # I - One unsigned integer
                host,
                # H - One unsigned short
                port,
            )
            self.transport.write(response)
            logger.debug("Sent connection established response to client.")

        except asyncio.TimeoutError:
            logger.error("Connection to %s:%s timed out", hostname, port)
            self.transport.close()

        except OSError as e:
            logger.error("Failed to connect to %s:%s due to %s", hostname, port, e)
            self.transport.close()

        except Exception as e:
            logger.error("Unexpected error: %s", e)
            self.transport.close()
