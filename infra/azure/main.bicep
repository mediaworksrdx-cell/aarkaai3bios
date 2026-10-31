targetScope = 'resourceGroup'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Deployment environment name (e.g. prod, staging)')
param environmentName string = 'prod'

@description('Application name prefix')
param appName string = 'aarkaai-backend'

@description('Container Image to deploy')
param containerImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

@description('Container CPU cores')
param cpuCore string = '2.0'

@description('Container Memory reservation')
param memorySize string = '4Gi'

@description('Container Port')
param containerPort int = 5000

@description('Minimum replicas (scale-to-zero supported with 0)')
param minReplicas int = 1

@description('Maximum replicas')
param maxReplicas int = 3

var uniqueSuffix = uniqueString(resourceGroup().id)
var logAnalyticsWorkspaceName = 'law-aarkaai-${environmentName}-${uniqueSuffix}'
var acrName = 'acraarkaai${uniqueSuffix}'
var appEnvName = 'cae-aarkaai-${environmentName}'
var storageAccountName = 'staa${uniqueSuffix}'
var fileShareName = 'aarkaaidata'

// 1. Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// 2. Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// 3. Azure Storage Account for persistent database and sandboxed workspace
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
  }
}

resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: fileShareName
  properties: {
    shareQuota: 50
  }
}

// 4. Container Apps Managed Environment
resource appEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: appEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// 5. Container App Environment Storage Mount (Azure Files)
resource envStorage 'Microsoft.App/managedEnvironments/storages@2023-05-01' = {
  parent: appEnv
  name: 'aarkaaistorage'
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: fileShareName
      accessMode: 'ReadWrite'
    }
  }
}

// 6. Azure Container App (AARKAAI Backend)
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  dependsOn: [
    envStorage
  ]
  properties: {
    managedEnvironmentId: appEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: containerPort
        allowInsecure: false
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'aarkaai-backend'
          image: containerImage
          resources: {
            cpu: json(cpuCore)
            memory: memorySize
          }
          env: [
            {
              name: 'AARKAAI_ENV'
              value: 'production'
            }
            {
              name: 'AARKAAI_PORT'
              value: string(containerPort)
            }
            {
              name: 'AARKAAI_SAFE_DIR'
              value: '/home/aarkaai/app/workspace'
            }
            {
              name: 'AARKAAI_LOG_LEVEL'
              value: 'INFO'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: containerPort
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              failureThreshold: 3
              timeoutSeconds: 5
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: containerPort
              }
              initialDelaySeconds: 15
              periodSeconds: 15
              failureThreshold: 3
              timeoutSeconds: 5
            }
          ]
          volumeMounts: [
            {
              volumeName: 'persistent-data'
              mountPath: '/home/aarkaai/app/data'
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling-rule'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
      volumes: [
        {
          name: 'persistent-data'
          storageType: 'AzureFile'
          storageName: 'aarkaaistorage'
        }
      ]
    }
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output acrLoginServer string = acr.properties.loginServer
output acrName string = acr.name
output storageAccount string = storageAccount.name
