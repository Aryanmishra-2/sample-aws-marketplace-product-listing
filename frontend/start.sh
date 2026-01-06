#!/bin/sh
set -e

echo "🚀 Starting AWS Marketplace Seller Portal..."
echo "📊 Environment: $NODE_ENV"
echo "🔧 Port: $PORT"
echo "🏠 Hostname: $HOSTNAME"

# Start the Next.js server
exec node server.js