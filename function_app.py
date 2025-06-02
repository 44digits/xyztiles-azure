"""
XYZtiles
Azure function to create XYZ tiles for a given GeoTiff image.
Date: 2025 Jun 01
"""


import datetime
import logging
import os
import io

import azure.functions as func
import azure.storage.blob
import rasterio
import azurexyztiles


app = func.FunctionApp()

STATICWEBCONTAINER = '$web'

def getimage(
        image_blobservice: azure.storage.blob.BlobServiceClient,
        container: str, 
        path: str) -> rasterio.io.DatasetReader:
    '''getimage
        pull the given image from Azure storage and create rasterio object
    '''
    imagebytes = io.BytesIO()

    blob_client = image_blobservice.get_blob_client(
            container = container,
            blob = path)
    blob_client.download_blob().readinto(imagebytes)

    return rasterio.open(imagebytes)


@app.function_name(
        name="XYZtiles")
@app.route(
        route="xyztiles",
        auth_level=func.AuthLevel.ANONYMOUS)
def xyztiles_generate(
        req: func.HttpRequest) -> func.HttpResponse:

    imagepath = req.params.get('imagepath')
    zoomstart = req.params.get('zoomstart')
    zoomend = req.params.get('zoomend')
    logging.info(f'HTTP trigger :{imagepath}')

    if imagepath and zoomstart and zoomend:
        image_blobservice = azure.storage.blob.BlobServiceClient.from_connection_string(
                os.environ['TileContainer'])

        tiledirectory = imagepath + '-tiles'
        img = getimage(image_blobservice, 'raw-images', imagepath)
        tiles = azurexyztiles.AzureXYZtiles(
                image=img, 
                zooms=range(16), 
                pixels=512, 
                resampling="bilinear")
        tiles.write(image_blobservice, STATICWEBCONTAINER, tiledirectory)

        logging.info(f'Image directory: {tiledirectory}')
        return func.HttpResponse(
                f'Image directory: {tiledirectory}',
                status_code=200)

    logging.info(f'ERROR: missing parameter: {imagepath} {zoomstart} {zoomend}')
    return func.HttpResponse(
            f'ERROR: missing parameter: {imagepath} {zoomstart} {zoomend}',
            status_code=400)
