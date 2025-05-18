#!/bin/bash
set -e

# Fix permissions on Docker socket if it exists
if [ -e /var/run/docker.sock ]; then
  sudo chmod 666 /var/run/docker.sock || echo "Could not change permissions on Docker socket"
fi

# Execute the original Jenkins entrypoint
exec /usr/local/bin/jenkins.sh "$@"
