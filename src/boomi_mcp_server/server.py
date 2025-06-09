import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from .tools import mcp
from .custom_session import PatchedServerSession
from mcp import server as mcp_server


logger = logging.getLogger(__name__)


def _check_env() -> None:
    missing = [v for v in ("BOOMI_ACCOUNT", "BOOMI_USER", "BOOMI_SECRET") if v not in os.environ]
    if missing:
        msg = f"Missing Boomi credentials: {', '.join(missing)}"
        logger.error(msg)
        raise EnvironmentError(msg)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Boomi MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=8080, help="Port for SSE mode")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    for name in ("uvicorn", "fastapi"):
        logging.getLogger(name).handlers = []

    # Use patched session to gracefully handle unsupported requests
    mcp_server.session.ServerSession = PatchedServerSession

    load_dotenv()
    _check_env()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
