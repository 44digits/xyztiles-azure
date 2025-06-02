"""
AzureXYZtiles class based on rasterioxyz tiles
    https://github.com/duncanmartyn/rasterioxyz

Overloads write() method to upload to Azure storage

Date: 2025 Jun 01
"""

import pathlib
import rasterio.io
import numpy
import rasterioxyz
import azure.storage.blob


class AzureXYZtiles(rasterioxyz.Tiles):
    '''subclass of rasterioxyz.Tiles class
        used to overload write() method for Azure
    '''
    def write(self,
            output_blobservice: azure.storage.blob.BlobServiceClient,
            container: str,
            directoryname: str) -> None:
        '''Write XYZ tiles to Azure storage

        Parameters
        ----------
        output_blobservice:
            Azure blob service client object
        container:
            Name of storage container
        directoryname:
            Name of directory to create within storage container
        '''

        driver = "PNG"
        for tile in self.tiles:
            out_dir = pathlib.Path(directoryname)
            img_dir = out_dir.joinpath(str(tile.zoom), str(tile.column))
            img_path = img_dir.joinpath(f"{tile.row}.{driver}")

            if tile.data[-1].mean() == 0:
                continue

            with rasterio.io.MemoryFile() as memfile:
                with memfile.open(
                        driver=driver,
                        width=self.pixels,
                        height=self.pixels,
                        count=tile.data.shape[0],
                        dtype=numpy.uint8,
                ) as dst:
                    dst.write(tile.data)

                blob_client = output_blobservice.get_blob_client(
                        container=container,
                        blob= str(img_path))
                blob_client.upload_blob(memfile)
