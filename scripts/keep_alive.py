#!/usr/bin/env python3
"""
Keep-Alive script for Lumina School OS (Render Free-Tier sleep prevention).
Periodically pings the backend server to maintain hot state and prevent cold starts.
Can be run locally, on a server, in Docker, or integrated with UptimeRobot.
"""

import os
import sys
import time
from datetime import datetime, timezone
import httpx

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:8000/health")
PING_INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL_SECONDS", "600"))  # Every 10 minutes


def ping_server(url: str) -> bool:
    """Sends a GET request to the target health endpoint."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        start_time = time.time()
        response = httpx.get(url, timeout=30.0)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        if response.status_code == 200:
            print(f"[{now_str}] ✓ PING SUCCESS: {url} -> HTTP {response.status_code} ({latency_ms}ms)")
            return True
        else:
            print(f"[{now_str}] ⚠ PING WARNING: {url} -> HTTP {response.status_code} ({latency_ms}ms)")
            return False
    except Exception as exc:
        print(f"[{now_str}] ✗ PING FAILED: {url} -> Error: {exc}")
        return False


def main():
    print("=" * 60)
    print(" Lumina School OS — Keep-Alive Monitor")
    print(f" Target URL: {TARGET_URL}")
    print(f" Ping Interval: {PING_INTERVAL_SECONDS}s ({PING_INTERVAL_SECONDS // 60}m)")
    print("=" * 60)

    # Initial ping
    ping_server(TARGET_URL)

    try:
        while True:
            time.sleep(PING_INTERVAL_SECONDS)
            ping_server(TARGET_URL)
    except KeyboardInterrupt:
        print("\nKeep-Alive monitor stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
