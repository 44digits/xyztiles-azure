# xyztiles-azure
Azure function app to generate XYZ tiles from a GeoTiff

Give a GeoTiff, uploaded as a Azure Storage blob this function generates XYZ tiles
that can be used in a GIS application such as QGIS.  
Note this app is bound to a HTTP event and therefore acts as a REST endpoint with query parameters.

### Prerequisites
- Azure CLI: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
- Azure functions core tools: https://github.com/Azure/azure-functions-core-tools/tree/v4.x
- Azurite storage emulator (for local development) https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite

### Installation
Note these instructions were created in linux.  (Todo: test in Powershell)

1. If using Azure CLI for the first time sign in to Azure:  
   `az login`
1. Clone github repository:  
   `git clone https://github.com/44digits/xyztiles-azure.git`
1. Move into repo:  
  `cd xyztiles-azure`
1. Create Azure Resource Group:  
   `az group create --name AzureXYZtiles-rg --location westus`
1. Create storage account for raw images and tiles:  
   `az storage account create --name xyztilesdatastorage --location westus --resource-group AzureXYZtiles-rg --sku Standard_LRS`
1. Create container for raw images:  
   `az storage container create --account-name xyztilesdatastorage --name raw-images --auth-mode login`
1. Create container for tiles as static web server - will create a `$web` container:  
   `az storage blob service-properties update --account-name xyztilesdatastorage --static-website --auth-mode login`
1. Create storage account for Azure function app:  
   `az storage account create --name xyztilesappstorage --location westus --resource-group AzureXYZtiles-rg --sku Standard_LRS`
1. Create Azure function:  
   `az functionapp create --resource-group AzureXYZtiles-rg --consumption-plan-location westus --runtime python --runtime-version "3.11" --functions-version 4 --name xyztiles-38296-somelongrandomname --os-type linux --storage-account xyztilesappstorage`
    - app name needs to be unique across Azure - eg: xyztiles-348129438175194857
1. Get connection string for raw images and tile output:  
   `az storage account show-connection-string --name xyztilesdatastorage --key key1`
    - update `MapStorage` setting in `local.settings.json` with this value
1. Get Endpoint URL of static web server:  
   `az storage account show --name xyztilesdatastorage --query "primaryEndpoints.web"`
    - update `WebBaseURL` in `local.settings.json` with this value
1. Deploy function to Azure:  
   `func azure functionapp publish xyztiles-38296 --publish-local-settings`
    - note the function app URL that  is displayed
1. Upload sample geotiff to Azure storage:  
   `az storage blob upload --account-name xyztilesdatastorage --container-name raw-images --file sampletiff/image.tif`
1. Test 
    - bad request: `curl -i "<function app URL>?imagepath=xxx"`
    - good request: `curl -i "<function app URL>?imagepath=image.tif&zoomstart=0&zoomend=9"`
    - note `xyz_tile_url` in response and use in GIS app

Notes:
 - choose a distinct app name instead of `xyztiles-38296` - this must be unique across Azure
 - sample tiff was derrived from Natural Earth 1:10m Natural Earth I raster data: https://www.naturalearthdata.com/downloads/10m-raster-data/10m-natural-earth-1/
