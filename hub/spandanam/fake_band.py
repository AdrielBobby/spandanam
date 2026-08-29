"""Dev stand-in for the wearable: prints incoming motor frames as bars."""
import socket, sys
from .config import MOTORS
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("0.0.0.0", int(sys.argv[1]) if len(sys.argv) > 1 else 9001))
print("fake band listening")
while True:
    d, _ = s.recvfrom(64)
    if d[:1] == b"S" and len(d) >= 9:
        print("  ".join(f"{m[:6]:>6}:{'█' * (v // 32):<8}" for m, v in zip(MOTORS, d[1:9])), end="\r")
