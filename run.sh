#!/bin/bash

# Force Git Bash path conversion
HOST_PATH=$(cygpath -w "$(pwd)")
UNIX_PATH="/app"

# Auto-build if missing
if ! docker image inspect py310-base > /dev/null 2>&1; then
  echo "Building Docker image py310-base..."
  docker build -t py310-base .
fi

# Run Docker with proper working directory
docker run --rm \
  -v "$HOST_PATH:$UNIX_PATH" \
  -w "$UNIX_PATH" \
  py310-base \
  python "./src/$@"
