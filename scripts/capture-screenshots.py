#!/usr/bin/env python3
"""Capture pivona screenshots using Playwright HTML mockups.

Usage:
    python scripts/capture-screenshots.py

Prerequisites:
    pip install playwright
    python -m playwright install chromium

Screenshots are saved to docs/screenshots/ for use in the README.
"""
from playwright.sync_api import sync_playwright
import time
import os

SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "docs/screenshots")

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pivona - Router Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; height: 100vh; display: flex; }
        .sidebar { width: 260px; background: #1e293b; padding: 20px; border-right: 1px solid #334155; }
        .logo { font-size: 20px; font-weight: 700; color: #06b6d4; margin-bottom: 32px; }
        .nav-item { padding: 12px 16px; border-radius: 8px; margin-bottom: 4px; font-size: 14px; color: #94a3b8; }
        .nav-item.active { background: #06b6d4; color: #0f172a; font-weight: 600; }
        .main { flex: 1; padding: 24px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
        .header h1 { font-size: 24px; }
        .status-badge { background: #065f46; color: #10b981; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
        .stat-card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .stat-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px; }
        .stat-value { font-size: 28px; font-weight: 700; }
        .stat-value.green { color: #10b981; }
        .stat-value.cyan { color: #06b6d4; }
        .stat-value.blue { color: #3b82f6; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .card-title { font-weight: 600; margin-bottom: 16px; font-size: 14px; }
        .interface-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #334155; }
        .interface-row:last-child { border-bottom: none; }
        .intf-name { font-weight: 500; font-family: monospace; }
        .intf-ip { color: #94a3b8; font-size: 12px; }
        .intf-status { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .up { background: #065f46; color: #10b981; }
        .down { background: #7f1d1d; color: #ef4444; }
        .bar { height: 8px; background: #334155; border-radius: 4px; margin-top: 8px; }
        .bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #10b981, #06b6d4); }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">🛜 pivona</div>
        <div class="nav-item active">📊 Dashboard</div>
        <div class="nav-item">🌐 Network Map</div>
        <div class="nav-item">📈 Traffic</div>
        <div class="nav-item">⚙️ Settings</div>
    </div>
    <div class="main">
        <div class="header"><h1>Router Dashboard</h1><span class="status-badge">✓ Online</span></div>
        <div class="stats-grid">
            <div class="stat-card"><div class="stat-label">Uptime</div><div class="stat-value green">45d 12h</div></div>
            <div class="stat-card"><div class="stat-label">Connected Devices</div><div class="stat-value cyan">18</div></div>
            <div class="stat-card"><div class="stat-label">Bandwidth</div><div class="stat-value blue">847 Mbps</div></div>
            <div class="stat-card"><div class="stat-label">Latency</div><div class="stat-value green">12ms</div></div>
        </div>
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Network Interfaces</div>
                <div class="interface-row"><div><div class="intf-name">eth0 (WAN)</div><div class="intf-ip">192.168.1.1/24</div></div><span class="intf-status up">UP</span></div>
                <div class="interface-row"><div><div class="intf-name">eth1 (LAN)</div><div class="intf-ip">10.0.0.1/24</div></div><span class="intf-status up">UP</span></div>
                <div class="interface-row"><div><div class="intf-name">wlan0</div><div class="intf-ip">10.0.1.1/24</div></div><span class="intf-status up">UP</span></div>
            </div>
            <div class="card">
                <div class="card-title">Bandwidth Usage</div>
                <div style="margin-bottom: 16px;"><div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;"><span>↓ Download</span><span style="color: #10b981;">623 Mbps</span></div><div class="bar"><div class="bar-fill" style="width: 62%"></div></div></div>
                <div><div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;"><span>↑ Upload</span><span style="color: #3b82f6;">224 Mbps</span></div><div class="bar"><div class="bar-fill" style="width: 22%"></div></div></div>
            </div>
        </div>
    </div>
</body></html>
"""

MAP_HTML = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>pivona - Network Map</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; }
        h1 { font-size: 24px; margin-bottom: 24px; }
        .map-container { background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; height: 400px; position: relative; }
        .device { position: absolute; padding: 10px 14px; border-radius: 8px; font-size: 12px; font-weight: 500; }
        .device.router { background: #0e7490; color: white; }
        .device.pc { background: #1d4ed8; color: white; }
        .device.phone { background: #7c3aed; color: white; }
        .device.tv { background: #b45309; color: white; }
        .device.iot { background: #059669; color: white; }
    </style>
</head>
<body>
    <h1>🌐 Network Map</h1>
    <div class="map-container">
        <div class="device router" style="top: 30px; left: 50%; transform: translateX(-50%);">🛜 pivona (Gateway)</div>
        <div class="device pc" style="top: 150px; left: 10%;">💻 Desktop PC</div>
        <div class="device pc" style="top: 150px; left: 35%;">💻 Laptop</div>
        <div class="device phone" style="top: 150px; left: 60%;">📱 iPhone</div>
        <div class="device phone" style="top: 150px; left: 82%;">📱 Android</div>
        <div class="device tv" style="top: 280px; left: 15%;">📺 Smart TV</div>
        <div class="device iot" style="top: 280px; left: 40%;">🌡️ Thermostat</div>
        <div class="device iot" style="top: 280px; left: 60%;">📷 Camera</div>
        <div class="device iot" style="top: 280px; left: 80%;">🔊 Speaker</div>
    </div>
</body></html>
"""

TRAFFIC_HTML = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>pivona - Traffic Monitor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; }
        h1 { font-size: 24px; margin-bottom: 24px; }
        .chart-container { background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; margin-bottom: 16px; }
        .chart-title { font-weight: 600; margin-bottom: 16px; font-size: 14px; }
        .bar-chart { display: flex; align-items: flex-end; gap: 8px; height: 180px; }
        .bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
        .bar { width: 100%; border-radius: 4px 4px 0 0; background: linear-gradient(180deg, #10b981, #06b6d4); }
        .bar-label { font-size: 10px; color: #64748b; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
        th { text-align: left; padding: 14px 16px; background: #334155; font-size: 12px; text-transform: uppercase; color: #94a3b8; }
        td { padding: 14px 16px; border-bottom: 1px solid #334155; font-size: 14px; }
    </style>
</head>
<body>
    <h1>📈 Traffic Monitor</h1>
    <div class="chart-container">
        <div class="chart-title">Bandwidth Over Time (24h)</div>
        <div class="bar-chart">
            <div class="bar-col"><div class="bar" style="height: 60%"></div><div class="bar-label">00:00</div></div>
            <div class="bar-col"><div class="bar" style="height: 45%"></div><div class="bar-label">04:00</div></div>
            <div class="bar-col"><div class="bar" style="height: 70%"></div><div class="bar-label">08:00</div></div>
            <div class="bar-col"><div class="bar" style="height: 85%"></div><div class="bar-label">12:00</div></div>
            <div class="bar-col"><div class="bar" style="height: 95%"></div><div class="bar-label">16:00</div></div>
            <div class="bar-col"><div class="bar" style="height: 100%"></div><div class="bar-label">18:00</div></div>
            <div class="bar-col"><div class="bar" style="height: 80%"></div><div class="bar-label">20:00</div></div>
            <div class="bar-col"><div class="bar" style="height: 55%"></div><div class="bar-label">22:00</div></div>
        </div>
    </div>
    <table>
        <thead><tr><th>Device</th><th>IP Address</th><th>Download</th><th>Upload</th><th>Total Today</th></tr></thead>
        <tbody>
            <tr><td>💻 Desktop PC</td><td>10.0.0.10</td><td style="color: #10b981;">124 Mbps</td><td style="color: #8b5cf6;">45 Mbps</td><td>28.4 GB</td></tr>
            <tr><td>📱 iPhone</td><td>10.0.0.25</td><td style="color: #10b981;">89 Mbps</td><td style="color: #8b5cf6;">12 Mbps</td><td>15.2 GB</td></tr>
            <tr><td>📺 Smart TV</td><td>10.0.0.30</td><td style="color: #10b981;">210 Mbps</td><td style="color: #8b5cf6;">2 Mbps</td><td>42.1 GB</td></tr>
        </tbody>
    </table>
</body></html>
"""

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def capture_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        for name, html in [("dashboard.png", DASHBOARD_HTML), ("network-map.png", MAP_HTML), ("traffic.png", TRAFFIC_HTML)]:
            print(f"Capturing {name}...")
            page.set_content(html)
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            path = os.path.join(SCREENSHOT_DIR, name)
            page.screenshot(path=path, full_page=False)
            print(f"Saved: {path} ({os.path.getsize(path):,} bytes)")
        
        browser.close()
    print("\nAll screenshots captured successfully!")

if __name__ == "__main__":
    capture_screenshots()
