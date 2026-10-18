#!/usr/bin/env python3
"""
pivona - Dashboard Backend
Serves the dashboard and provides API endpoints for router functions.
Run as root on a real gateway for full router control: sudo python3 app.py
Set DEMO_MODE=true for a safe local demo that needs no network privileges.
"""

import os
import random
import re
import sqlite3
import subprocess
import threading
import time

import psutil
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="template", static_folder="static")

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")
DB_PATH = os.getenv("DB_PATH", "/var/lib/pivona/traffic.db")

DEMO_STATS = {
    "cpu": 42.0,
    "mem_used": 38.0,
    "mem_total": 4096,
    "disk_used": 23.0,
    "disk_total": 64.0,
    "temp": 52.0,
    "net_rx": 8589934592,
    "net_tx": 2147483648,
    "clients": 3,
    "ext_ip": "203.0.113.1",
    "uptime": "up 2 days, 4 hours",
    "hostname": "pivona",
}

DEMO_VPNS = {
    "warp": {"name": "Cloudflare WARP", "active": True, "detail": "Connected via WARP"},
    "wireguard": {"name": "WireGuard", "active": False, "detail": "Inactive"},
    "mesh-vpn": {"name": "Mesh-VPN", "active": True, "detail": "mesh-vpn up, exit node: none"},
    "nordvpn": {"name": "NordVPN", "active": False, "detail": "Inactive"},
    "netbird": {"name": "NetBird", "active": False, "detail": "Inactive"},
    "unifi": {"name": "UniFi Teleport", "active": False, "detail": "Inactive"},
}

DEMO_CLIENTS = [
    {"expires": "86400", "mac": "02:42:ac:11:00:02", "ip": "203.0.113.10", "hostname": "laptop-demo"},
    {"expires": "86400", "mac": "02:42:ac:11:00:03", "ip": "203.0.113.11", "hostname": "phone-demo"},
    {"expires": "86400", "mac": "02:42:ac:11:00:04", "ip": "203.0.113.12", "hostname": "camera-demo"},
]

# ─── DATABASE SETUP ────────────────────────────────────────────────────────────


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS traffic (
        ts      INTEGER PRIMARY KEY,
        rx      INTEGER,
        tx      INTEGER,
        clients INTEGER,
        cpu     REAL,
        mem     REAL,
        temp    REAL,
        vpn     TEXT
    )"""
    )
    conn.commit()
    conn.close()


def record_traffic():
    """Called every minute by background thread."""
    while True:
        try:
            if DEMO_MODE:
                rx = DEMO_STATS["net_rx"] + random.randint(0, 100_000_000)
                tx = DEMO_STATS["net_tx"] + random.randint(0, 50_000_000)
                cpu = max(0.0, min(100.0, DEMO_STATS["cpu"] + random.uniform(-5, 5)))
                mem = max(0.0, min(100.0, DEMO_STATS["mem_used"] + random.uniform(-3, 3)))
                temp = max(0.0, DEMO_STATS["temp"] + random.uniform(-2, 2))
                clients = DEMO_STATS["clients"]
                vpn = "WARP,Mesh-VPN"
            else:
                net = psutil.net_io_counters(pernic=True)
                rx = sum(n.bytes_recv for n in net.values())
                tx = sum(n.bytes_sent for n in net.values())
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent
                temp_raw, _ = run_cmd("vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp")
                try:
                    temp = float(temp_raw.replace("temp=", "").replace("'C", ""))
                    if temp > 100:
                        temp = temp / 1000
                except Exception:
                    temp = 0.0
                clients_raw, _ = run_cmd("cat /var/lib/misc/dnsmasq.leases 2>/dev/null | wc -l")
                clients = int(clients_raw or 0)
                active_vpns = []
                for svc, cmd in [
                    ("WARP", "warp-cli status"),
                    ("WireGuard", "wg show wg0 2>/dev/null"),
                    ("Mesh-VPN", "mesh-vpn status"),
                    ("NordVPN", "nordvpn status"),
                    ("NetBird", "netbird status 2>/dev/null"),
                ]:
                    _, ok = run_cmd(cmd)
                    if ok:
                        active_vpns.append(svc)
                vpn = ",".join(active_vpns)

            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "INSERT OR REPLACE INTO traffic VALUES (?,?,?,?,?,?,?,?)",
                (int(time.time()), rx, tx, clients, cpu, mem, round(temp, 1), vpn),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        time.sleep(60)


# ─── HELPERS ───────────────────────────────────────────────────────────────────


def run_cmd(cmd):
    if DEMO_MODE:
        return "", False
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return r.stdout.strip(), r.returncode == 0
    except Exception:
        return "", False


VPN_SERVICES = {
    "warp": {"name": "Cloudflare WARP", "icon": "cloud", "color": "#f97316", "check": "warp-cli status", "start": "warp-cli connect", "stop": "warp-cli disconnect"},
    "wireguard": {"name": "WireGuard", "icon": "shield", "color": "#ef4444", "check": "wg show wg0 2>/dev/null", "start": "wg-quick up wg0", "stop": "wg-quick down wg0"},
    "mesh-vpn": {"name": "Mesh-VPN", "icon": "network", "color": "#10b981", "check": "mesh-vpn status", "start": "mesh-vpn up", "stop": "mesh-vpn down"},
    "nordvpn": {"name": "NordVPN", "icon": "lock", "color": "#8b5cf6", "check": "nordvpn status", "start": "nordvpn connect", "stop": "nordvpn disconnect"},
    "netbird": {"name": "NetBird", "icon": "router", "color": "#f59e0b", "check": "netbird status 2>/dev/null", "start": "netbird up", "stop": "netbird down"},
    "unifi": {"name": "UniFi Teleport", "icon": "wifi", "color": "#3b82f6", "check": "wg show unifi 2>/dev/null", "start": "wg-quick up unifi", "stop": "wg-quick down unifi"},
}


def get_vpn_status():
    if DEMO_MODE:
        return {k: {**v, "icon": VPN_SERVICES[k]["icon"], "color": VPN_SERVICES[k]["color"]} for k, v in DEMO_VPNS.items()}
    status = {}
    for key, cfg in VPN_SERVICES.items():
        out, ok = run_cmd(cfg["check"])
        status[key] = {**cfg, "active": ok, "detail": out[:100] if ok else "Inactive"}
    return status


def get_system_stats():
    if DEMO_MODE:
        return {**DEMO_STATS, "timestamp": int(time.time())}
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    temp_raw, _ = run_cmd("vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp")
    try:
        temp = float(temp_raw.replace("temp=", "").replace("'C", ""))
        if temp > 100:
            temp = temp / 1000
    except Exception:
        temp = 0.0
    net = psutil.net_io_counters()
    clients_raw, _ = run_cmd("cat /var/lib/misc/dnsmasq.leases 2>/dev/null | wc -l")
    ext_ip, _ = run_cmd("curl -s --max-time 3 ifconfig.me")
    uptime_raw, _ = run_cmd("uptime -p")
    hostname, _ = run_cmd("hostname")
    return {
        "cpu": round(cpu, 1),
        "mem_used": round(mem.percent, 1),
        "mem_total": round(mem.total / 1024 / 1024),
        "disk_used": round(disk.percent, 1),
        "disk_total": round(disk.total / 1024 / 1024 / 1024, 1),
        "temp": round(temp, 1),
        "net_rx": net.bytes_recv,
        "net_tx": net.bytes_sent,
        "clients": int(clients_raw or 0),
        "ext_ip": ext_ip or "Unknown",
        "uptime": uptime_raw,
        "hostname": hostname or "pivona",
        "timestamp": int(time.time()),
    }


def get_traffic_history(period="24h"):
    if DEMO_MODE:
        now = int(time.time())
        if period == "24h":
            since = now - 86_400
            bucket = 900
            count = 97
        elif period == "3d":
            since = now - 259_200
            bucket = 3600
            count = 73
        else:  # 7d
            since = now - 604_800
            bucket = 7200
            count = 85
        result = []
        for i in range(count):
            ts = since + i * bucket
            rx_mb = max(0.1, random.uniform(0.5, 8.0) + (i % 12) * 0.3)
            tx_mb = max(0.05, random.uniform(0.2, 4.0))
            cpu = max(5.0, min(95.0, DEMO_STATS["cpu"] + random.uniform(-8, 8)))
            mem = max(10.0, min(90.0, DEMO_STATS["mem_used"] + random.uniform(-5, 5)))
            temp = max(30.0, min(70.0, DEMO_STATS["temp"] + random.uniform(-4, 4)))
            result.append({
                "ts": ts,
                "rx_mb": round(rx_mb, 2),
                "tx_mb": round(tx_mb, 2),
                "cpu": round(cpu, 1),
                "mem": round(mem, 1),
                "temp": round(temp, 1),
                "clients": DEMO_STATS["clients"],
            })
        return result

    now = int(time.time())
    if period == "24h":
        since = now - 86_400
        bucket = 900  # 15-min buckets
    elif period == "3d":
        since = now - 259_200
        bucket = 3600  # 1-hour buckets
    else:  # 7d
        since = now - 604_800
        bucket = 7200  # 2-hour buckets

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM traffic WHERE ts >= ? ORDER BY ts ASC", (since,)).fetchall()
    conn.close()

    buckets = {}
    for row in rows:
        bk = (row["ts"] // bucket) * bucket
        if bk not in buckets:
            buckets[bk] = {"rx": [], "tx": [], "cpu": [], "mem": [], "temp": [], "clients": []}
        buckets[bk]["rx"].append(row["rx"])
        buckets[bk]["tx"].append(row["tx"])
        buckets[bk]["cpu"].append(row["cpu"])
        buckets[bk]["mem"].append(row["mem"])
        buckets[bk]["temp"].append(row["temp"])
        buckets[bk]["clients"].append(row["clients"])

    result = []
    sorted_keys = sorted(buckets.keys())
    for i, k in enumerate(sorted_keys):
        b = buckets[k]
        rx_delta = 0
        if i > 0 and b["rx"] and buckets[sorted_keys[i - 1]]["rx"]:
            rx_delta = max(0, b["rx"][-1] - buckets[sorted_keys[i - 1]]["rx"][-1])
        tx_delta = 0
        if i > 0 and b["tx"] and buckets[sorted_keys[i - 1]]["tx"]:
            tx_delta = max(0, b["tx"][-1] - buckets[sorted_keys[i - 1]]["tx"][-1])
        result.append({
            "ts": k,
            "rx_mb": round(rx_delta / 1024 / 1024, 2),
            "tx_mb": round(tx_delta / 1024 / 1024, 2),
            "cpu": round(sum(b["cpu"]) / len(b["cpu"]), 1),
            "mem": round(sum(b["mem"]) / len(b["mem"]), 1),
            "temp": round(sum(b["temp"]) / len(b["temp"]), 1),
            "clients": round(sum(b["clients"]) / len(b["clients"])),
        })
    return result


def get_connected_clients():
    if DEMO_MODE:
        return DEMO_CLIENTS
    leases_raw, ok = run_cmd("cat /var/lib/misc/dnsmasq.leases 2>/dev/null")
    if not ok or not leases_raw:
        return []
    clients = []
    for line in leases_raw.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 4:
            clients.append({
                "expires": parts[0],
                "mac": parts[1],
                "ip": parts[2],
                "hostname": parts[3] if parts[3] != "*" else "Unknown",
            })
    return clients


def get_mesh_vpn_exit_nodes():
    if DEMO_MODE:
        return [
            {"id": "nyc", "name": "nyc-office"},
            {"id": "ams", "name": "ams-vps-01"},
            {"id": "best", "name": "best-available"},
        ]
    out, _ = run_cmd("mesh-vpn exit-node list 2>/dev/null")
    nodes = []
    for line in out.strip().split("\n"):
        parts = line.split()
        if parts and not line.startswith("#") and len(parts) >= 2:
            nodes.append({"id": parts[0], "name": parts[1] if len(parts) > 1 else parts[0]})
    return nodes


# ─── ROUTES ────────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "demo": DEMO_MODE}), 200


@app.route("/api/stats")
def api_stats():
    return jsonify({
        "stats": get_system_stats(),
        "vpns": get_vpn_status(),
    })


@app.route("/api/traffic")
def api_traffic():
    period = request.args.get("period", "24h")
    return jsonify({"data": get_traffic_history(period), "period": period})


@app.route("/api/clients")
def api_clients():
    return jsonify({"clients": get_connected_clients()})


@app.route("/api/vpn/<action>/<service>", methods=["POST"])
def vpn_control(action, service):
    if service not in VPN_SERVICES or action not in ("start", "stop"):
        return jsonify({"ok": False, "output": "Unknown"})
    if DEMO_MODE:
        return jsonify({"ok": True, "output": "Connected" if action == "start" else "Disconnected"})
    cmd = "sudo " + VPN_SERVICES[service][action]
    out, ok = run_cmd(cmd)
    return jsonify({"ok": ok, "output": out or ("Connected" if action == "start" else "Disconnected")})


@app.route("/api/mesh-vpn/exit-nodes")
def ts_exit_nodes():
    return jsonify({"nodes": get_mesh_vpn_exit_nodes()})


@app.route("/api/mesh-vpn/set-exit", methods=["POST"])
def ts_set_exit():
    node = request.json.get("node", "")
    if DEMO_MODE:
        return jsonify({"ok": True, "output": f"Exit node set to {node}"})
    if node == "best":
        out, ok = run_cmd("/usr/local/bin/mesh-vpn-best-exit.sh")
    elif node == "none":
        out, ok = run_cmd("mesh-vpn set --exit-node=")
    elif re.fullmatch(r"[A-Za-z0-9._-]{1,64}", node):
        out, ok = run_cmd(f"mesh-vpn set --exit-node={node}")
    else:
        return jsonify({"ok": False, "output": "Invalid exit node id"})
    return jsonify({"ok": ok, "output": out})


@app.route("/api/speedtest")
def api_speedtest():
    if DEMO_MODE:
        return jsonify({"ok": True, "download": 187.5, "upload": 94.2})
    out, ok = run_cmd("python3 -c \"import speedtest; s=speedtest.Speedtest(); s.get_best_server(); dl=s.download()/1e6; ul=s.upload()/1e6; print(f'{dl:.1f},{ul:.1f}')\" 2>/dev/null")
    if ok and "," in out:
        dl, ul = out.split(",")
        return jsonify({"ok": True, "download": float(dl), "upload": float(ul)})
    return jsonify({"ok": False, "output": "speedtest-cli not installed. Run: pip3 install speedtest-cli"})


@app.route("/api/reboot", methods=["POST"])
def api_reboot():
    if DEMO_MODE:
        return jsonify({"ok": True, "output": "Reboot simulated in demo mode"})
    run_cmd("sleep 2 && sudo reboot &")
    return jsonify({"ok": True})


@app.route("/api/logs", methods=["GET", "POST"])
def api_logs():
    """View service logs"""
    svc = request.args.get("service", request.form.get("service", "system"))

    if DEMO_MODE:
        demo_logs = {
            "system": ["[demo] pivona dashboard started", "[demo] traffic collector running", "[demo] health endpoint ok"],
            "warp": ["[demo] warp-cli status: Connected", "[demo] tunnel ok"],
            "wireguard": ["[demo] WireGuard tunnel inactive"],
            "mesh-vpn": ["[demo] mesh-vpn up, exit node: none"],
            "nordvpn": ["[demo] NordVPN disconnected"],
            "netbird": ["[demo] NetBird disconnected"],
        }
        return jsonify({"lines": demo_logs.get(svc, ["[demo] no log sample available"]), "service": svc})

    log_files = {
        "system": "/var/log/syslog",
        "warp": "~/.config/cloudflare/warp.log",
        "wireguard": "/var/log/wireguard/wg0.log",
        "mesh-vpn": "/var/log/mesh-vpn/log.txt",
        "nordvpn": "~/.nordvpn/nordvpn.log",
        "netbird": "/var/log/netbird.log",
    }

    lines = []
    if svc in log_files:
        try:
            result = subprocess.run(["sudo", "tail", "-n", "200", log_files[svc]], capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split("\n")[-50:]
        except Exception as e:
            lines = [f"Error: {e!s}"]

    return jsonify({"lines": lines, "service": svc})


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=record_traffic, daemon=True)
    t.start()
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
