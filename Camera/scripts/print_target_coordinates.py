#!/usr/bin/env python3

import argparse
import json
import socket
import sys


def main() -> int:
	parser = argparse.ArgumentParser(description="Print detected target coordinates from Rockey Hockey")
	parser.add_argument("--detector-host", default="192.168.2.2", help="Detector host to subscribe to")
	parser.add_argument("--detector-port", type=int, default=5005, help="Detector port to subscribe to")
	parser.add_argument("--bind-host", default="0.0.0.0", help="Local host to bind for the response socket")
	parser.add_argument("--bind-port", type=int, default=0, help="Local port to bind for the response socket")
	args = parser.parse_args()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((args.bind_host, args.bind_port))
	sock.connect((args.detector_host, args.detector_port))
	sock.send(b"subscribe")

	local_host, local_port = sock.getsockname()
	print(
		f"Subscribed from udp://{local_host}:{local_port} to udp://{args.detector_host}:{args.detector_port}",
		flush=True,
	)

	while True:
		payload = sock.recv(65535)
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
