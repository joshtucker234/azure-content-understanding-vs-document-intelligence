#!/usr/bin/env bash
# Delete everything the lab created. Deleting the resource group removes the Foundry resource, deployments and role assignments.
# Azure keeps a deleted AI Services account in "soft delete" for a few days (no charge). To reuse the same name sooner, purge it:
#   az cognitiveservices account purge -g "$RG" -n "$FOUNDRY" -l "$LOC"
set -euo pipefail
: "${RG:?source scripts/00-env.sh first}"
read -r -p "Delete resource group $RG and everything in it? Type the group name to confirm: " ans
[ "$ans" = "$RG" ] || { echo "Cancelled."; exit 1; }
az group delete -n "$RG" --yes --no-wait
echo "Deletion started. Check with: az group exists -n $RG"
