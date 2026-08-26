// Azure Bicep template for complete infrastructure deployment (Phase 2 design hardened)

param location string = resourceGroup().location
param environment string = 'dev'
param appName string = 'improve-yourself'

// Secure SQL admin parameters (from Phase 1)
param sqlAdminUser string = 'app_sql_admin'
@secure()
param sqlAdminPassword string

// Phase 2 design — toggles (defaults safe/no-op)
param enableDiagnostics bool = true
param enablePrivateEndpoints bool = false
param privateEndpointSubnetId string = '' // Resource ID of a subnet to host private endpoints

// Control public network access per service (kept enabled by default to avoid breaking existing flows)
param enablePublicNetworkStorage bool = true
param enablePublicNetworkKeyVault bool = true
param enablePublicNetworkCosmos bool = true
param enablePublicNetworkSql bool = true

// Optional Private DNS zone IDs to bind to each private endpoint (no zone creation in P2)
param privateDnsZoneIds_storage array = []     // e.g., [/subscriptions/.../resourceGroups/.../providers/Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net]
param privateDnsZoneIds_keyvault array = []    // e.g., .../privatelink.vaultcore.azure.net
param privateDnsZoneIds_cosmos array = []      // e.g., .../privatelink.documents.azure.com
param privateDnsZoneIds_sql array = []         // e.g., .../privatelink.database.windows.net

// Optional SQL security diagnostics (workspace routing only; not enabling Defender pricing)
param enableSqlSecurityDiagnostics bool = false

var storageAccountName = '${appName}${environment}${uniqueString(resourceGroup().id)}'
var keyvaultName = '${appName}-${environment}-kv'
var cosmosDbName = '${appName}-${environment}-cosmos'
var sqlServerName = '${appName}-${environment}-sql'
var sqlDatabaseName = '${appName}db'
var appInsightsName = '${appName}-${environment}-ai'
var logAnalyticsName = '${appName}-${environment}-law'

// Storage Account (baseline + PNPA control)
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
    // Use network ACLs to simulate PNPA off without assuming version-specific publicNetworkAccess property
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: enablePublicNetworkStorage ? 'Allow' : 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}

// Key Vault (baseline + PNPA control)
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyvaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enablePurgeProtection: true
    publicNetworkAccess: enablePublicNetworkKeyVault ? 'Enabled' : 'Disabled'
  }
}

// Cosmos DB Account (PNPA control; no topology changes in P2)
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
    publicNetworkAccess: enablePublicNetworkCosmos ? 'Enabled' : 'Disabled'
  }
}

// SQL Server (use secure parameters + PNPA control)
resource sqlServer 'Microsoft.Sql/servers@2021-11-01' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: sqlAdminUser
    administratorLoginPassword: sqlAdminPassword
    publicNetworkAccess: enablePublicNetworkSql ? 'Enabled' : 'Disabled'
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

// Diagnostics — route platform logs/metrics to Log Analytics (toggle)
@description('Diagnostic settings for Storage Account -> LAW')
resource diag_storage 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableDiagnostics) {
  name: 'to-law-storage'
  scope: storageAccount
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      { category: 'StorageRead', enabled: true }
      { category: 'StorageWrite', enabled: true }
      { category: 'StorageDelete', enabled: true }
    ]
    metrics: [ { category: 'AllMetrics', enabled: true } ]
  }
}

@description('Diagnostic settings for Key Vault -> LAW')
resource diag_kv 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableDiagnostics) {
  name: 'to-law-keyvault'
  scope: keyVault
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      { category: 'AuditEvent', enabled: true }
      { category: 'AzurePolicyEvaluationDetails', enabled: true }
    ]
    metrics: [ { category: 'AllMetrics', enabled: true } ]
  }
}

@description('Diagnostic settings for Cosmos DB -> LAW')
resource diag_cosmos 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableDiagnostics) {
  name: 'to-law-cosmos'
  scope: cosmosDbAccount
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      { category: 'DataPlaneRequests', enabled: true }
      { category: 'QueryRuntimeStatistics', enabled: true }
    ]
    metrics: [ { category: 'AllMetrics', enabled: true } ]
  }
}

@description('Diagnostic settings for SQL Server -> LAW')
resource diag_sql_server 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableDiagnostics) {
  name: 'to-law-sql-server'
  scope: sqlServer
  properties: {
    workspaceId: logAnalytics.id
    logs: [ { category: 'DevOpsOperationsAudit', enabled: true } ]
    metrics: [ { category: 'AllMetrics', enabled: true } ]
  }
}

@description('Diagnostic settings for SQL Database -> LAW (security audit events)')
resource diag_sql_db 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableDiagnostics && enableSqlSecurityDiagnostics) {
  name: 'to-law-sql-db'
  scope: sqlDatabase
  properties: {
    workspaceId: logAnalytics.id
    logs: [ { category: 'SQLSecurityAuditEvents', enabled: true } ]
    metrics: [ { category: 'AllMetrics', enabled: true } ]
  }
}

// Private Endpoints (optional, single subnet param; DNS zone group bindings optional)
var hasPeSubnet = (length(privateEndpointSubnetId) > 0)

resource pe_storage 'Microsoft.Network/privateEndpoints@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet) {
  name: '${storageAccountName}-pe-blob'
  location: location
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [
      {
        name: 'blob'
        properties: {
          privateLinkServiceId: storageAccount.id
          groupIds: [ 'blob' ]
        }
      }
    ]
  }
}

resource pe_storage_dns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet && length(privateDnsZoneIds_storage) > 0) {
  name: 'default'
  parent: pe_storage
  properties: {
    privateDnsZoneConfigs: [ for zoneId in privateDnsZoneIds_storage: {
      name: guid(zoneId)
      properties: {
        privateDnsZoneId: zoneId
      }
    }]
  }
}

resource pe_kv 'Microsoft.Network/privateEndpoints@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet) {
  name: '${keyvaultName}-pe'
  location: location
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [
      {
        name: 'vault'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: [ 'vault' ]
        }
      }
    ]
  }
}

resource pe_kv_dns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet && length(privateDnsZoneIds_keyvault) > 0) {
  name: 'default'
  parent: pe_kv
  properties: {
    privateDnsZoneConfigs: [ for zoneId in privateDnsZoneIds_keyvault: {
      name: guid(zoneId)
      properties: { privateDnsZoneId: zoneId }
    }]
  }
}

resource pe_cosmos 'Microsoft.Network/privateEndpoints@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet) {
  name: '${cosmosDbName}-pe'
  location: location
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [
      {
        name: 'sql'
        properties: {
          privateLinkServiceId: cosmosDbAccount.id
          groupIds: [ 'Sql' ]
        }
      }
    ]
  }
}

resource pe_cosmos_dns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet && length(privateDnsZoneIds_cosmos) > 0) {
  name: 'default'
  parent: pe_cosmos
  properties: {
    privateDnsZoneConfigs: [ for zoneId in privateDnsZoneIds_cosmos: {
      name: guid(zoneId)
      properties: { privateDnsZoneId: zoneId }
    }]
  }
}

resource pe_sql 'Microsoft.Network/privateEndpoints@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet) {
  name: '${sqlServerName}-pe'
  location: location
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [
      {
        name: 'sqlserver'
        properties: {
          privateLinkServiceId: sqlServer.id
          groupIds: [ 'sqlServer' ]
        }
      }
    ]
  }
}

resource pe_sql_dns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = if (enablePrivateEndpoints && hasPeSubnet && length(privateDnsZoneIds_sql) > 0) {
  name: 'default'
  parent: pe_sql
  properties: {
    privateDnsZoneConfigs: [ for zoneId in privateDnsZoneIds_sql: {
      name: guid(zoneId)
      properties: { privateDnsZoneId: zoneId }
    }]
  }
}

// Outputs
output storageAccountUrl string = storageAccount.properties.primaryEndpoints.blob
output keyVaultUrl string = keyVault.properties.vaultUri
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
output sqlServerName string = sqlServer.properties.fullyQualifiedDomainName
output appInsightsConnectionString string = appInsights.properties.ConnectionString
