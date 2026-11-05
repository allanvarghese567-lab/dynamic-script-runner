#!/usr/bin/env python3
"""
Network Diagnostic Script (cross-platform fallback).
Collects local IP, gateway, DNS, public IP and performs QUBIQON whitelist check.
Wi-Fi SSID/BSSID details are best-effort (full support on Windows via PowerShell version).
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

APPROVED_DEFAULT = ["103.142.31.212", "103.181.238.50"]


def get_public_ip() -> str | None:
    urls = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                ip = resp.read().decode().strip()
                if ip.count(".") == 3:
                    return ip
        except Exception:
            continue
    return None


def load_approved_ips() -> list[str]:
    candidates = [
        Path("settings.json"),
        Path("config/settings.json"),
        Path(__file__).resolve().parents[2] / "settings.json",
        Path(__file__).resolve().parents[2] / "config" / "settings.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                ips = data.get("approved_public_ips")
                if ips:
                    return list(ips)
            except Exception:
                pass
    return APPROVED_DEFAULT


def get_local_info() -> dict:
    info = {"hostname": socket.gethostname()}
    try:
        # Primary outbound interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["local_ipv4"] = s.getsockname()[0]
        s.close()
    except Exception:
        info["local_ipv4"] = "unknown"

    # Gateway / DNS (Linux)
    try:
        route = subprocess.check_output(["ip", "route", "show", "default"], text=True, timeout=3)
        parts = route.split()
        if "via" in parts:
            info["gateway"] = parts[parts.index("via") + 1]
    except Exception:
        info["gateway"] = "unknown"

    try:
        with open("/etc/resolv.conf") as f:
            dns = [line.split()[1] for line in f if line.startswith("nameserver")]
            info["dns"] = dns
    except Exception:
        info["dns"] = []

    return info


def main() -> int:
    print("Dynamic Script Runner – Network Diagnostics (Python)")
    print(f"Platform: {sys.platform}")

    local = get_local_info()
    print("\n=== Local Network ===")
    print(f"Hostname     : {local.get('hostname')}")
    print(f"Local IPv4   : {local.get('local_ipv4')}")
    print(f"Gateway      : {local.get('gateway')}")
    print(f"DNS Servers  : {', '.join(local.get('dns') or ['unknown'])}")

    print("\n=== Public IP & Whitelist ===")
    public_ip = get_public_ip()
    approved = load_approved_ips()

    if not public_ip:
        print("Public IP       : UNKNOWN (detection failed)")
        print("Whitelist Status: UNKNOWN")
    else:
        print(f"Public IP       : {public_ip}")
        if public_ip in approved:
            print("Whitelist Status: APPROVED")
        else:
            print("Whitelist Status: NOT APPROVED")
            print(f"Approved IPs    : {', '.join(approved)}")

    print("\nNote: Full Wi-Fi SSID/BSSID/signal details are available on Windows")
    print("      via the companion network-check.ps1 script.")
    print("\nDiagnostics complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
