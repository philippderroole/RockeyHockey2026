#!/usr/bin/env python3

import argparse
import json
import socket
import sys


def main() -> int:
	parser = argparse.ArgumentParser(description="Print detected target coordinates from Rockey Hockey")
	parser.add_argument("--host", default="127.0.0.1", help="Local host to bind for UDP packets")
	parser.add_argument("--port", type=int, default=5005, help="Local port to bind for UDP packets")
	args = parser.parse_args()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((args.host, args.port))

	print(f"Listening on udp://{args.host}:{args.port}", flush=True)

	while True:
		payload, _ = sock.recvfrom(65535)
		try:
			message = json.loads(payload.decode("utf-8"))
		except Exception as exc:  # noqa: BLE001
			print(f"Dropped invalid packet: {exc}: {payload!r}", file=sys.stderr, flush=True)
			continue

		for detection in message.get("detections", []):
			print(
				f"{detection['target_name']}: ({detection['x']}, {detection['y']})",
				flush=True,
			)


if __name__ == "__main__":
	raise SystemExit(main())
