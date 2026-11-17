#!/usr/bin/env bash
# Connect a hosted ds2agent MCP server to Claude Code over HTTP.
# Usage: connect_remote_mcp.sh <MCP_NAME> <MCP_ENDPOINT_URL>
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <MCP_NAME> <MCP_ENDPOINT_URL>" >&2
  exit 2
fi

claude mcp add --transport http "$1" "$2"
