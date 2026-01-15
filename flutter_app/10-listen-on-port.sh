#!/bin/sh
# Substitute $PORT in nginx config
# Cloud Run injects PORT env var

if [ -z "$PORT" ]; then
    export PORT=8080
fi

echo "Replacing port 8080 with $PORT in /etc/nginx/conf.d/default.conf"
sed -i "s/8080/$PORT/g" /etc/nginx/conf.d/default.conf
