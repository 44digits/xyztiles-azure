"""
XYZtiles
Azure function to create XYZ tiles for a given GeoTiff image.
Date: 2025 Jun 01
"""


import datetime
import logging
import os
import io
import json

import azure.functions as func
import azure.storage.blob
import rasterio
import azurexyztiles

XYZ_URL_PATTERN = "{baseurl}/{directory}/{{z}}/{{x}}/{{y}}.PNG"

app = func.FunctionApp()

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
    logging.info(f'XYZtiles started: {imagepath} {zoomstart} {zoomend}')

    if imagepath and zoomstart and zoomend:
        zoomstart = int(zoomstart)
        zoomend = int(zoomend)
        map_storage_connection = os.environ['MapStorage']
        raw_image_container = os.environ['RawContainer']
        tile_container = os.environ['WebContainer']
        baseurl = os.environ['WebBaseURL']

        image_blobservice = azure.storage.blob.BlobServiceClient.from_connection_string(
                map_storage_connection)

        tiledirectory = imagepath + '-tiles'
        img = getimage(image_blobservice, raw_image_container, imagepath)
        tiles = azurexyztiles.AzureXYZtiles(
                image=img, 
                zooms=range(zoomstart, zoomend), 
                pixels=512, 
                resampling="bilinear")
        tiles.write(image_blobservice, tile_container, tiledirectory)

        xyz_url = XYZ_URL_PATTERN.format(
                baseurl = baseurl,
                directory = tiledirectory)
        logging.info(f'XYZ tile url: {xyz_url}')

        response = {
                'status': True,
                'xyz_tile_url': xyz_url}
        return func.HttpResponse(
                json.dumps(response),
                mimetype = 'application/json',
                status_code=200)

    logging.info(f'ERROR: missing parameter: {imagepath} {zoomstart} {zoomend}')
    response = {
            'status': False,
            'message': 'ERROR: missing parameters',
            'parameters': {
                'imagepath': imagepath,
                'zoomstart': zoomstart,
                'zoomend': zoomend }}
    return func.HttpResponse(
            json.dumps(response),
            mimetype = 'application/json',
            status_code=400)
