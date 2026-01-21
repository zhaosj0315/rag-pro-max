#!/bin/bash
# RAG Pro Max - Quick Start (replaces 'rag' alias)
# Cleans ports, starts WebSSH (bg), starts Streamlit (fg)

echo "🧹 Cleaning ports 8501, 8502, 8899..."
# Kill processes on these ports safely
lsof -ti:8501,8502,8899 | xargs kill -9 2>/dev/null || true

echo "🌐 Starting WebSSH service (background)..."
# Start SSH tunnel
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R rag-pro-max:80:localhost:8501 serveo.net > /dev/null 2>&1 &
SSH_PID=$!

# Ensure SSH process is killed when this script exits
trap "echo '🛑 Stopping WebSSH...'; kill $SSH_PID 2>/dev/null" EXIT

echo "🚀 Starting Streamlit App (foreground)..."
export PYTHONPATH="${PWD}:${PYTHONPATH}"
streamlit run src/apppro.py --server.port 8501
