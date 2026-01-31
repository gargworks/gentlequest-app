#!/bin/bash

# Nucleus OS - The Sovereign Agent Control Plane
# Install Script

echo "🔧 Initializing Nucleus OS Installation..."

# Check for Python
if ! command -v python3 &> /dev/null
then
    echo "❌ Error: Python 3 is not installed. Please install it from https://python.org"
    exit
fi

# Check for pip
if ! command -v pip3 &> /dev/null
then
    echo "❌ Error: pip3 is not installed."
    exit
fi

echo "📦 Installing mcp-server-nucleus via PyPI..."
pip3 install mcp-server-nucleus

echo "✅ Nucleus OS successfully installed!"
echo "🚀 Run 'nucleus --help' to get started."
