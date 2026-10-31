<#
.SYNOPSIS
    Deploys the fixed AARKAAI backend to Azure.
.DESCRIPTION
    Provides automated deployment options:
    1. Direct push to active Azure VM (138.91.105.85) via SSH/SCP.
    2. Provisioning & deployment to Azure Container Apps (ACA) using Bicep.
.PARAMETER Target
    Deployment target: 'vm' (default) or 'container-app'.
#>
[CmdletBinding()]
param(
    [ValidateSet('vm', 'container-app')]
    [string]$Target = 'vm',
    [string]$ResourceGroup = 'rg-aarkaai-prod',
    [string]$Location = 'eastus'
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AARKAAI Production Azure Deployment Orchestrator        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if ($Target -eq 'vm') {
    Write-Host "[1/3] Selected Target: Azure Production VM (138.91.105.85)" -ForegroundColor Green
    Write-Host "[2/3] Executing automated package, SCP upload, and PM2 reload..." -ForegroundColor Yellow
    python scripts/deploy/deploy_latest_azure.py --backend-only
    Write-Host "[3/3] Deployment complete. Validating /health..." -ForegroundColor Green
    Start-Sleep -Seconds 3
    $health = Invoke-RestMethod -Uri "http://138.91.105.85/health" -Method Get -TimeoutSec 10
    Write-Host "Live Health Status: $($health.status) | Version: $($health.version)" -ForegroundColor Green
}
elseif ($Target -eq 'container-app') {
    Write-Host "[1/4] Selected Target: Azure Container Apps (ACA)" -ForegroundColor Green
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        Write-Error "Azure CLI ('az') is not installed or not in PATH. Please install Azure CLI or deploy via GitHub Actions."
    }

    Write-Host "[2/4] Ensuring Resource Group '$ResourceGroup' in '$Location'..." -ForegroundColor Yellow
    az group create --name $ResourceGroup --location $Location

    Write-Host "[3/4] Deploying Infrastructure via Bicep (infra/azure/main.bicep)..." -ForegroundColor Yellow
    $deployment = az deployment group create `
        --resource-group $ResourceGroup `
        --template-file "infra/azure/main.bicep" `
        --parameters "@infra/azure/parameters.json" `
        --output json | ConvertFrom-Json

    $fqdn = $deployment.properties.outputs.fqdn.value
    Write-Host "[4/4] Container App deployed at: https://$fqdn" -ForegroundColor Green
    Write-Host "Testing health endpoint: https://$fqdn/health..." -ForegroundColor Yellow
    Invoke-RestMethod -Uri "https://$fqdn/health" -Method Get
}
