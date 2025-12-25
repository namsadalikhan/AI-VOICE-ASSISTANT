from __future__ import annotations

import ipaddress
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterable

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

MAX_HOSTS = 1024


@dataclass
class PingResult:
    host: str
    alive: bool


def ping_host(host: str) -> PingResult:
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return PingResult(host=host, alive=result.returncode == 0)
    except FileNotFoundError:
        return PingResult(host=host, alive=False)


def expand_hosts(ip: str, prefix: int) -> Iterable[str]:
    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
    return [str(host) for host in network.hosts()]


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/ping", methods=["POST"])
def ping() -> tuple:
    payload = request.get_json(silent=True) or {}
    ip = (payload.get("ip") or "").strip()
    subnet = (payload.get("subnet") or "").strip()

    if not ip or not subnet:
        return jsonify({"error": "IP address and subnet are required."}), 400

    try:
        prefix = int(subnet)
    except ValueError:
        return jsonify({"error": "Subnet must be a number like 24."}), 400

    try:
        hosts = expand_hosts(ip, prefix)
    except ValueError:
        return jsonify({"error": "Invalid IP address or subnet."}), 400

    if len(hosts) > MAX_HOSTS:
        return (
            jsonify(
                {
                    "error": f"Subnet too large ({len(hosts)} hosts)."
                    " Please use a smaller subnet."
                }
            ),
            400,
        )

    with ThreadPoolExecutor(max_workers=min(64, len(hosts) or 1)) as executor:
        results = list(executor.map(ping_host, hosts))

    alive_results = [result for result in results if result.alive]

    return (
        jsonify(
            {
                "network": f"{ip}/{prefix}",
                "results": [
                    {"host": result.host, "alive": result.alive}
                    for result in alive_results
                ],
                "alive_count": len(alive_results),
                "scanned": len(hosts),
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
