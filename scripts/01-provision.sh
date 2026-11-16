#!/usr/bin/env bash
# Resource group, Foundry resource, model deployments, RBAC and the Content Understanding default model mapping.
# Prereq: `az login` to the tenant that owns the subscription, then `source scripts/00-env.sh`.
set -euo pipefail
: "${SUB:?source scripts/00-env.sh first}"
az account set --subscription "$SUB"
ME=$(az ad signed-in-user show --query id -o tsv)

echo "== resource group =="
az group create -n "$RG" -l "$LOC" --tags $TAGS -o none

echo "== Foundry resource (AIServices). One resource serves Content Understanding AND Document Intelligence =="
az cognitiveservices account create -g "$RG" -n "$FOUNDRY" -l "$LOC" --kind AIServices --sku S0 \
  --custom-domain "$FOUNDRY" --assign-identity --tags $TAGS --yes -o none

echo "== model deployments. Content Understanding calls these for generate fields and prebuilt analyzers =="
az cognitiveservices account deployment create -g "$RG" -n "$FOUNDRY" --deployment-name gpt-4.1 \
  --model-name gpt-4.1 --model-version 2025-04-14 --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50 -o none
az cognitiveservices account deployment create -g "$RG" -n "$FOUNDRY" --deployment-name gpt-4.1-mini \
  --model-name gpt-4.1-mini --model-version 2025-04-14 --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50 -o none
az cognitiveservices account deployment create -g "$RG" -n "$FOUNDRY" --deployment-name text-embedding-3-large \
  --model-name text-embedding-3-large --model-version 1 --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50 -o none

echo "== RBAC: you (data-plane access, keyless) =="
FID=$(az cognitiveservices account show -g "$RG" -n "$FOUNDRY" --query id -o tsv)
for role in "Cognitive Services User" "Cognitive Services Contributor"; do
  az role assignment create --assignee-object-id "$ME" --assignee-principal-type User --role "$role" --scope "$FID" -o none
done
echo "Role assignments can take a few minutes to take effect. Waiting 60s before the next call..."
sleep 60

echo "== tell Content Understanding which deployments to use (one-time, per resource) =="
TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
curl -sS --fail-with-body -X PATCH "${CU_ENDPOINT}/contentunderstanding/defaults?api-version=2025-11-01" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/merge-patch+json" \
  -d '{"modelDeployments":{"gpt-4.1":"gpt-4.1","gpt-4.1-mini":"gpt-4.1-mini","text-embedding-3-large":"text-embedding-3-large"}}'
echo
echo "Done. Next: cd app && pip install -r requirements.txt, then see docs/REPLICATE.md."
