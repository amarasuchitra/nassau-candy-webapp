"""Print the first free local port from 8000 upwards (used by the launchers).

A port counts as busy if anything answers on it (IPv4 or IPv6) or it can't be
bound — so an old server left running on 8000 is never mistaken for this app.
"""
import socket
import sys


def is_free(port: int) -> bool:
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                if s.connect_ex((host, port)) == 0:
                    return False
        except OSError:
            pass  # e.g. IPv6 not available
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
    except OSError:
        return False
    return True


if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(next((p for p in range(start, start + 100) if is_free(p)), start))
