// Azure Bicep template for complete infrastructure deployment

param location string = resourceGroup().location
param environment string = 'dev'
param appName string = 'improve-yourself'

var storageAccountName = '${appName}${environment}${uniqueString(resourceGroup().id)}'
var keyvaultName = '${appName}-${environment}-kv'
var cosmosDbName = '${appName}-${environment}-cosmos'
var sqlServerName = '${appName}-${environment}-sql'
var sqlDatabaseName = '${appName}db'
var appInsightsName = '${appName}-${environment}-ai'

// Storage Account
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
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyvaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
  }
}

// Cosmos DB Account
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
    }
    databaseAccountOfferType: 'Standard'
  }
}

// SQL Server
resource sqlServer 'Microsoft.Sql/servers@2021-11-01' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: 'sqladmin'
    administratorLoginPassword: keyVault.properties.vaultUri
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

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
  }
}

// Outputs
output storageAccountUrl string = storageAccount.properties.primaryEndpoints.blob
output keyVaultUrl string = keyVault.properties.vaultUri
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
output sqlServerName string = sqlServer.properties.fullyQualifiedDomainName
output appInsightsKey string = appInsights.properties.InstrumentationKey
