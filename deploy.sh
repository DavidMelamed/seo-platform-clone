#!/bin/bash
TARGET="${1:-railway}"
ENV="${2:-production}"

echo "Deploying to $TARGET (environment: $ENV)"

if [ -f "waypoint-configs/$TARGET.hcl" ]; then
    waypoint up -var-file="waypoint-configs/$TARGET.hcl"
else
    waypoint up -var="deploy_target=$TARGET"
fi
