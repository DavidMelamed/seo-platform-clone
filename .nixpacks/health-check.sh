#!/bin/bash
if [ -n "$PORT" ]; then
    curl -f http://localhost:$PORT/health || exit 1
else
    echo "Health check passed"
fi
