# Azure Integration Setup Guide

## Overview

This guide provides complete setup instructions for integrating your CS2 analysis platform with Azure services.

## Prerequisites

- Azure Account with active subscription
- Azure CLI (`az` command)
- Python 3.8+
- pip package manager

## Step 1: Create Azure Service Principal

```bash
# Login to Azure
az login

# Create a service principal
az ad sp create-for-rbac --name improve-yourself-sp --role Contributor

# Output will include:
# "appId": <AZURE_CLIENT_ID>
# "password": <AZURE_CLIENT_SECRET>
# "tenant": <AZURE_TENANT_ID>
```

## Step 2: Create Resource Group

```bash
az group create \
  --name improve-yourself-rg \
  --location westeurope
```

## Step 3: Deploy Azure Resources

### Option A: Using Bicep Template (Recommended)

```bash
az deployment group create \
  --resource-group improve-yourself-rg \
  --template-file azure/deployment.bicep \
  --parameters environment=dev
```

### Option B: Manual Creation

#### Create Storage Account

```bash
az storage account create \
  --name mystoragedev \
  --resource-group improve-yourself-rg \
  --location westeurope \
  --sku Standard_LRS
```

#### Create Key Vault

```bash
az keyvault create \
  --name improve-yourself-kv \
  --resource-group improve-yourself-rg \
  --location westeurope

# Grant access to service principal
az keyvault set-policy \
  --name improve-yourself-kv \
  --spn <AZURE_CLIENT_ID> \
  --secret-permissions get list set delete
```

#### Create Cosmos DB Account

```bash
az cosmosdb create \
  --name improve-yourself-cosmos \
  --resource-group improve-yourself-rg \
  --kind GlobalDocumentDB
```

#### Create SQL Server and Database

```bash
az sql server create \
  --name improve-yourself-sql \
  --resource-group improve-yourself-rg \
  --admin-user sqladmin \
  --admin-password <SECURE_PASSWORD>

az sql db create \
  --server improve-yourself-sql \
  --name improve-yourself \
  --resource-group improve-yourself-rg
```

#### Create Application Insights

```bash
az monitor app-insights component create \
  --app improve-yourself-ai \
  --resource-group improve-yourself-rg \
  --kind web
```

## Step 4: Store Secrets in Key Vault

```bash
# SQL Password
az keyvault secret set \
  --vault-name improve-yourself-kv \
  --name sql-password \
  --value <YOUR_PASSWORD>

# Database Connection String
az keyvault secret set \
  --vault-name improve-yourself-kv \
  --name db-connection-string \
  --value "your-connection-string"

# API Keys
az keyvault secret set \
  --vault-name improve-yourself-kv \
  --name api-key \
  --value <YOUR_API_KEY>
```

## Step 5: Configure Environment

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your Azure credentials
AZURE_SUBSCRIPTION_ID=<your-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-secret>
AZURE_RESOURCE_GROUP=improve-yourself-rg
AZURE_KEYVAULT_URL=https://improve-yourself-kv.vault.azure.net/
AZURE_STORAGE_ACCOUNT_URL=https://mystoragedev.blob.core.windows.net
AZURE_COSMOS_ENDPOINT=https://improve-yourself-cosmos.documents.azure.com:443/
AZURE_SQL_SERVER=improve-yourself-sql.database.windows.net
AZURE_SQL_DATABASE=improve-yourself
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

## Step 6: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-azure.txt
```

## Step 7: Test Connection

```bash
# Run main application
python azure/main.py
```

## Usage Examples

### Blob Storage

```python
from azure.main import ApplicationContext

app = ApplicationContext()

# Upload file
with open('data.csv', 'rb') as f:
    url = app.storage.upload_blob('data', 'analysis.csv', f)
    print(f"Uploaded to: {url}")

# Download file
data = app.storage.download_blob('data', 'analysis.csv')

# List files
files = app.storage.list_blobs('data')
```

### Key Vault

```python
# Store secret
app.keyvault.set_secret('my-api-key', 'secret-value')

# Retrieve secret
api_key = app.keyvault.get_secret('my-api-key')

# List secrets
secrets = app.keyvault.list_secrets()
```

### Cosmos DB

```python
# Create item
item = {'id': '1', 'name': 'Analysis', 'category': 'CS2'}
app.cosmos.create_item(item)

# Query items
results = app.cosmos.query_items(
    "SELECT * FROM c WHERE c.category = 'CS2'"
)

# Update item
item['status'] = 'completed'
app.cosmos.upsert_item(item)
```

### SQL Database

```python
# Execute query
results = app.sql.execute_query(
    "SELECT * FROM analyses WHERE category = ?",
    ('CS2',)
)

# Execute update
rows_affected = app.sql.execute_update(
    "INSERT INTO analyses (name, category) VALUES (?, ?)",
    ('New Analysis', 'CS2')
)
```

## Monitoring and Logging

Application Insights automatically collects:
- Request traces
- Exception logs
- Performance metrics
- Custom events

View in Azure Portal: `Monitor > Application Insights > improve-yourself-ai`

## Security Best Practices

1. **Never commit secrets** — Use `.env` file (in `.gitignore`)
2. **Use Managed Identity** — In Azure-hosted applications
3. **Enable RBAC** — Restrict service principal permissions
4. **Rotate credentials** — Regularly update secrets in Key Vault
5. **Use TLS/SSL** — All connections are encrypted
6. **Network Security** — Configure firewall rules for databases

## Troubleshooting

### Authentication Errors

```bash
# Test credentials
az account show

# Re-authenticate
az login --service-principal -u <AZURE_CLIENT_ID> -p <AZURE_CLIENT_SECRET> --tenant <AZURE_TENANT_ID>
```

### Connection Timeouts

- Check firewall rules on databases
- Verify network connectivity
- Review application logs in Application Insights

### Permission Errors

```bash
# Grant permissions to service principal
az role assignment create \
  --assignee <AZURE_CLIENT_ID> \
  --role Contributor \
  --scope /subscriptions/<SUBSCRIPTION_ID>
```

## Additional Resources

- [Azure SDK for Python Documentation](https://learn.microsoft.com/en-us/azure/developer/python/)
- [Azure Best Practices](https://learn.microsoft.com/en-us/azure/architecture/)
- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
