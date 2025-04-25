#!/bin/bash
for port in {6001..6008}; do
  echo "Starting web server on port $port"
  nohup python3 -m http.server "$port" --bind 0.0.0.0 >/dev/null 2>&1 &
done
