"""
XYZtiles
Azure function to generate XYZ tiles from a GeoTiff image

Name of GeoTiff image is passes as a query parameter on the URL
along with the zoom levels.  The Azure connection details, and names
of containers are stored as AppSettings.

TODO:
    Convert from HTTP binding to ServiceBus binding
    Include parameters for projection, transformation, etc
        so does not have to be stored in GeoTiff header
    Improve memory allocation

Date: 2025 Jun 01
"""


import io
import json
import logging
import os

import azure.functions as func
import azure.storage.blob
import rasterio

import azurexyztiles


# pattern of XYX url used by gis apps
XYZ_URL_PATTERN = "{baseurl}/{directory}/{{z}}/{{x}}/{{y}}.PNG"

app = func.FunctionApp()

def getimage(
        image_blobservice: azure.storage.blob.BlobServiceClient,
        container: str,
        path: str) -> rasterio.io.DatasetReader:
    '''getimage
        pull the given image from Azure storage and return rasterio object

        Parameters
        ----------
        image_blobservice:
            Azure blob service client object
        container:
            Name of storage container
        path:
            Name and path to GeoTiff within container
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
    '''XYZtiles: Azure function to generate XYZ tiles from a GeoTiff image

    Both GeoTiff source image and output tiles are stored in Azure storage.
    The output container is assumed to be configured as a static web site.

    URL Query Parameters
    --------------------
    imagepath:
        path to source image within container
    zoomstart, zoomend:
        start and stop zoom levels for tiles

    App Settings
    ------------
    MapStorage
        Azure storage connection string
    RawContainer
        Name of container used for image uploads
    WebContainer
        Container used for tile storage.
        Usually called $web if configured as a static web site
    WebBaseURL
        Primate endpoint of static web site starting with https://
    '''

    imagepath = req.params.get('imagepath')
    zoomstart = req.params.get('zoomstart')
    zoomend = req.params.get('zoomend')
    logging.info('XYZtiles started: %s %s %s', 
            imagepath, str(zoomstart), str(zoomend))

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
        logging.info('XYZ tile url: %s', xyz_url)

        response = {
                'status': True,
                'xyz_tile_url': xyz_url}
        return func.HttpResponse(
                json.dumps(response),
                mimetype = 'application/json',
                status_code=200)

    logging.info('ERROR: missing parameter: %s %s %s',
            imagepath, str(zoomstart), str(zoomend))
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
