#!/usr/bin/env bash
# ==============================================================================
# AARKAAI Production Azure Deployment Orchestrator (POSIX Bash)
# Deploys the fixed production codebase to Azure VM or Azure Container Apps
# ==============================================================================
set -euo pipefail

TARGET="${1:-vm}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-aarkaai-prod}"
LOCATION="${LOCATION:-eastus}"

echo "=========================================================="
echo "   AARKAAI Production Azure Deployment Orchestrator        "
echo "=========================================================="

if [ "$TARGET" = "vm" ]; then
    echo "[1/3] Target: Azure VM (138.91.105.85)"
    python3 scripts/deploy/deploy_latest_azure.py --backend-only
    echo "[2/3] Verification: Waiting 5s for FastAPI startup..."
    sleep 5
    echo "[3/3] Querying live /health endpoint..."
    curl -s http://138.91.105.85/health | jq . || curl -s http://138.91.105.85/health
elif [ "$TARGET" = "container-app" ]; then
    echo "[1/4] Target: Azure Container Apps"
    if ! command -v az &>/dev/null; then
        echo "Error: Azure CLI ('az') is not installed. Use GitHub Actions CI/CD or install az."
        exit 1
    fi
    echo "[2/4] Creating Resource Group: $RESOURCE_GROUP in $LOCATION"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    echo "[3/4] Deploying Bicep Template..."
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "infra/azure/main.bicep" \
        --parameters "@infra/azure/parameters.json"
    echo "[4/4] Deployment complete."
else
    echo "Usage: ./scripts/deploy_azure.sh [vm|container-app]"
    exit 1
fi
