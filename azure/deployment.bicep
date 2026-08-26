// Azure Bicep template for complete infrastructure deployment (Phase 1 hardened)

param location string = resourceGroup().location
param environment string = 'dev'
param appName string = 'improve-yourself'

// Secure SQL admin parameters
param sqlAdminUser string = 'app_sql_admin'
@secure()
param sqlAdminPassword string

var storageAccountName = '${appName}${environment}${uniqueString(resourceGroup().id)}'
var keyvaultName = '${appName}-${environment}-kv'
var cosmosDbName = '${appName}-${environment}-cosmos'
var sqlServerName = '${appName}-${environment}-sql'
var sqlDatabaseName = '${appName}db'
var appInsightsName = '${appName}-${environment}-ai'
var logAnalyticsName = '${appName}-${environment}-law'

// Storage Account (baseline hardening)
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Key Vault (baseline hardening)
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyvaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    // Prefer RBAC over access policies
    enableRbacAuthorization: true
    // Purge protection on (soft-delete is always on with modern API versions)
    enablePurgeProtection: true
    // Intentionally not changing network ACLs in Phase 1
  }
}

// Cosmos DB Account (no network changes in Phase 1)
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: cosmosDbName
  location: location
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    databaseAccountOfferType: 'Standard'
  }
}

// SQL Server (use secure parameters)
resource sqlServer 'Microsoft.Sql/servers@2021-11-01' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: sqlAdminUser
    administratorLoginPassword: sqlAdminPassword
  }
}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2021-11-01' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

// Log Analytics Workspace (for workspace-based Application Insights)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  sku: {
    name: 'PerGB2018'
  }
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Application Insights (workspace-based)
resource appInsights 'Microsoft.Insights/components@2022-06-15' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    IngestionMode: 'ApplicationInsights'
    WorkspaceResourceId: logAnalytics.id
  }
}

// Outputs
output storageAccountUrl string = storageAccount.properties.primaryEndpoints.blob
output keyVaultUrl string = keyVault.properties.vaultUri
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
output sqlServerName string = sqlServer.properties.fullyQualifiedDomainName
output appInsightsConnectionString string = appInsights.properties.ConnectionString
