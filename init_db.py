#!/usr/bin/env python3
"""Initialize the pivona database."""

import os
import sqlite3

DB_PATH = "/var/lib/pivona/traffic.db"


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

    print(f"✓ Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
