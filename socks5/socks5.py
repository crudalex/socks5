import logging
import argparse
import asyncio
from socks5 import Server


async def run_proxy_server(listen_address, listen_port, timeout):
    loop = asyncio.get_event_loop()

    coro = loop.create_server(
        lambda: Server(timeout=timeout), listen_address, listen_port
    )
    server = await asyncio.wait_for(coro, timeout=timeout)

    logging.info("Server listening on %s:%s...", listen_address, listen_port)
    logging.info("Connection timeout: %s seconds", timeout)

    try:
        await server.serve_forever()
    except (KeyboardInterrupt, Exception) as e:
        logging.info("Server shutdown initiated by %s.", type(e).__name__)
        if not isinstance(e, KeyboardInterrupt):
            logging.error("Server error: %s", e)
    finally:
        server.close()
        await server.wait_closed()


def main():

    parser = argparse.ArgumentParser(description="SOCKS5 Proxy Server")
    parser.add_argument(
        "-l", "--listen_address", default="0.0.0.0", help="Address to listen on"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=1080, help="Port to listen on"
    )
    parser.add_argument(
        "-t", "--timeout", type=int, default=5, help="Connection timeout in seconds"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s | %(levelname)s | %(funcName)s | %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(funcName)s | %(message)s",
        )

    asyncio.run(run_proxy_server(args.listen_address, args.port, args.timeout))
