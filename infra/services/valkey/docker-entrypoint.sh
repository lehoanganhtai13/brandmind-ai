#!/bin/sh
# Valkey Docker Entrypoint Script
# This script processes the valkey.conf.template file and substitutes
# environment variables before starting the Valkey server.

set -e

echo "🔧 Valkey Entrypoint: Starting configuration..."

# Check if template file exists
if [ ! -f /usr/local/etc/valkey/valkey.conf.template ]; then
    echo "❌ Error: valkey.conf.template not found!"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$VALKEY_PASSWORD" ]; then
    echo "⚠️  Warning: VALKEY_PASSWORD is not set. Using default 'password'"
    export VALKEY_PASSWORD="password"
fi

if [ -z "$VALKEY_USERNAME" ]; then
    echo "ℹ️  Info: VALKEY_USERNAME is not set. Using default 'brandmind'"
    export VALKEY_USERNAME="brandmind"
fi

echo "ℹ️  Username: $VALKEY_USERNAME"
echo "ℹ️  Password: ****** (hidden)"

# Substitute environment variables in the template using sed
# (envsubst is not available in the Valkey image, so we use sed instead)
echo "🔄 Generating valkey.conf from template..."
sed -e "s/\${VALKEY_USERNAME}/${VALKEY_USERNAME}/g" \
    -e "s/\${VALKEY_PASSWORD}/${VALKEY_PASSWORD}/g" \
    /usr/local/etc/valkey/valkey.conf.template > /tmp/valkey.conf

# Verify the generated config file
if [ ! -f /tmp/valkey.conf ]; then
    echo "❌ Error: Failed to generate valkey.conf"
    exit 1
fi

echo "✅ Configuration generated successfully at /tmp/valkey.conf"
echo "🚀 Starting Valkey server..."

# Start Valkey server with the generated configuration
exec valkey-server /tmp/valkey.conf
