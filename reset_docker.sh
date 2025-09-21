#!/bin/bash

# Script to clean up Docker environment (containers, images, volumes, networks)
# Usage: ./docker-cleanup.sh

# Use explicit Docker path
DOCKER_PATH="/usr/bin/docker"

# Stop all running containers
$DOCKER_PATH stop $($DOCKER_PATH ps -q) 2>/dev/null

# Remove all containers
$DOCKER_PATH rm -f $($DOCKER_PATH ps -a -q) 2>/dev/null

# Remove all images
$DOCKER_PATH rmi -f $($DOCKER_PATH images -q) 2>/dev/null

# Remove all volumes
$DOCKER_PATH volume rm $($DOCKER_PATH volume ls -q) 2>/dev/null

# Remove unused networks (ignore errors for default networks)
$DOCKER_PATH network rm $($DOCKER_PATH network ls -q) 2>/dev/null

# Prune everything
$DOCKER_PATH system prune -a --volumes -f 2>/dev/null

echo "Docker environment cleaned."
~                                   
