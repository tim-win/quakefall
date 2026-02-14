#!/usr/bin/env python3
"""Q3 RCON client — send commands to a running ioq3ded server.

Usage:
    python3 tools/rcon.py status
    python3 tools/rcon.py "map qfcity1"
    python3 tools/rcon.py --password dev "titan_parts"

The server must have sv_rconPassword set (tools/server.sh sets it to 'dev').
"""

import argparse
import socket
import sys


def rcon(host: str, port: int, password: str, command: str, timeout: float = 2.0) -> str:
    """Send an RCON command and return the response text."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    # Q3 rcon wire format: \xff\xff\xff\xffrcon <password> <command>\n
    packet = b"\xff\xff\xff\xffrcon " + password.encode() + b" " + command.encode() + b"\n"
    sock.sendto(packet, (host, port))

    # Collect response packets until timeout
    response = b""
    try:
        while True:
            data, _ = sock.recvfrom(4096)
            response += data
    except socket.timeout:
        pass
    finally:
        sock.close()

    # Strip Q3 response prefix: \xff\xff\xff\xffprint\n
    prefix = b"\xff\xff\xff\xffprint\n"
    if response.startswith(prefix):
        response = response[len(prefix):]

    return response.decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description="Q3 RCON client")
    parser.add_argument("command", nargs="+", help="Command to send to server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=27960, help="Server port (default: 27960)")
    parser.add_argument("--password", default="dev", help="RCON password (default: dev)")
    parser.add_argument("--timeout", type=float, default=2.0, help="Response timeout in seconds")
    args = parser.parse_args()

    cmd = " ".join(args.command)
    result = rcon(args.host, args.port, args.password, cmd, args.timeout)

    if result:
        print(result, end="")
    else:
        print(f"No response (is server running with sv_rconPassword '{args.password}'?)",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
