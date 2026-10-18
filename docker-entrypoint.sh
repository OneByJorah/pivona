#!/bin/bash
# pivona Docker Entrypoint
# Handles first-run setup and credential onboarding
# Auto-generates defaults when running non-interactively (no TTY)

set -e

# If .env doesn't exist, run setup wizard
if [ ! -f /app/.env ]; then
    echo "============================================"
    echo "  pivona — First Run"
    echo "============================================"
    echo ""

    # Generate random secret
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    ADMIN_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

    # Check if running interactively
    if [ -t 0 ]; then
        # Interactive mode
        read -p "Admin username [admin]: " ADMIN_USER
        ADMIN_USER=${ADMIN_USER:-admin}

        read -s -p "Admin password (leave blank for random): " ADMIN_PASS_INPUT
        echo ""
        ADMIN_PASS=${ADMIN_PASS_INPUT:-$ADMIN_PASS}

        read -p "Port [5000]: " PORT
        PORT=${PORT:-5000}

        read -p "WAN interface [eth0]: " WAN_IF
        WAN_IF=${WAN_IF:-eth0}

        read -p "Collect interval (seconds) [60]: " COLLECT_INT
        COLLECT_INT=${COLLECT_INT:-60}
    else
        # Non-interactive mode — use defaults
        echo "Non-interactive mode — using auto-generated defaults"
        ADMIN_USER="admin"
        PORT=5000
        WAN_IF="eth0"
        COLLECT_INT=60
    fi

    # Write .env
    cat > /app/.env <<EOF
SECRET_KEY=${SECRET}
ADMIN_USER=${ADMIN_USER}
ADMIN_PASS=${ADMIN_PASS}
PORT=${PORT}
WAN_INTERFACE=${WAN_IF}
COLLECT_INTERVAL_SECONDS=${COLLECT_INT}
DATABASE_PATH=/app/data/router.db
LOG_LEVEL=INFO
EOF

    echo ""
    echo "✅ Configuration saved to /app/.env"
    echo "   Admin user: ${ADMIN_USER}"
    echo "   Admin pass: ${ADMIN_PASS}"
    echo ""
    echo "⚠️  Save these credentials — they won't be shown again."
    echo "============================================"
fi

# Source .env
export $(grep -v '^#' /app/.env | xargs)

# Initialize database
python3 init_db.py 2>/dev/null || true

echo "Starting pivona..."
exec "$@"
