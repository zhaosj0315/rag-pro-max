#!/bin/bash
# RAG Pro Max - WebSSH Service (replaces 'ragss' alias)

echo "🌐 Starting WebSSH service (foreground)..."
echo "   Forwarding localhost:8501 -> https://rag-pro-max.serveousercontent.com"
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R rag-pro-max:80:localhost:8501 serveo.net
