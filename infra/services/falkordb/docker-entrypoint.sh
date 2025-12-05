#!/bin/sh
# FalkorDB Docker Entrypoint Script
# This script processes the falkordb.conf.template file and substitutes
# environment variables before starting the FalkorDB server.

set -e

echo "🔧 FalkorDB Entrypoint: Starting configuration..."

# Check if template file exists
if [ ! -f /usr/local/etc/falkordb/falkordb.conf.template ]; then
    echo "❌ Error: falkordb.conf.template not found!"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$FALKORDB_PASSWORD" ]; then
    echo "⚠️  Warning: FALKORDB_PASSWORD is not set. Using default 'password'"
    export FALKORDB_PASSWORD="password"
fi

if [ -z "$FALKORDB_USERNAME" ]; then
    echo "ℹ️  Info: FALKORDB_USERNAME is not set. Using default 'brandmind'"
    export FALKORDB_USERNAME="brandmind"
fi

echo "ℹ️  Username: $FALKORDB_USERNAME"
echo "ℹ️  Password: ****** (hidden)"

# Substitute environment variables in the template using sed
# (envsubst is not available in the FalkorDB image, so we use sed instead)
echo "🔄 Generating falkordb.conf from template..."
sed -e "s/\${FALKORDB_USERNAME}/${FALKORDB_USERNAME}/g" \
    -e "s/\${FALKORDB_PASSWORD}/${FALKORDB_PASSWORD}/g" \
    /usr/local/etc/falkordb/falkordb.conf.template > /tmp/falkordb.conf

# Verify the generated config file
if [ ! -f /tmp/falkordb.conf ]; then
    echo "❌ Error: Failed to generate falkordb.conf"
    exit 1
fi

echo "✅ Configuration generated successfully at /tmp/falkordb.conf"

# Start FalkorDB server and browser
# We need to start them separately because run.sh ignores our custom config

# Start browser in background if enabled
if [ "${BROWSER:-1}" -eq "1" ]; then
    if [ -d "${FALKORDB_BROWSER_PATH:-/var/lib/falkordb/browser}" ]; then
        echo "🌐 Starting FalkorDB Browser UI on port 3000..."
        cd "${FALKORDB_BROWSER_PATH:-/var/lib/falkordb/browser}" && HOSTNAME="0.0.0.0" node server.js &
    fi
fi

# Start FalkorDB server with our custom config and FalkorDB module
echo "🚀 Starting FalkorDB server on port 6379..."
exec redis-server /tmp/falkordb.conf --loadmodule /var/lib/falkordb/bin/falkordb.so
