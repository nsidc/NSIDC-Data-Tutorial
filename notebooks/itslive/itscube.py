import copy
from datetime import datetime
import glob
import os
import numpy  as np
import matplotlib.pyplot as plt
import s3fs
import xarray as xr
import xarray.plot as xplt


from itslive import itslive_ui


class ITSCube:
    """
    Class to represent ITS_LIVE cube: time series of velocity pairs within a
    polygon of interest.
    """
    # String representation of Cartesian projection
    CARTESIAN_PROJECTION = '4326'
    
    S3_PREFIX = 's3://'
    HTTP_PREFIX = 'http://'
    
    # Token within granule's URL that needs to be removed to get file location within S3 bucket:
    # if URL is of the 'http://its-live-data.jpl.nasa.gov.s3.amazonaws.com/velocity_image_pair/landsat/v00.0/32628/file.nc' format,
    # S3 bucket location of the file is 's3://its-live-data.jpl.nasa.gov/velocity_image_pair/landsat/v00.0/32628/file.nc'
    PATH_URL = ".s3.amazonaws.com"
    
    NC_ENGINE = 'h5netcdf'
    
    
    def __init__(self, polygon: tuple, projection: str):
        """
        polygon: tuple
            Polygon for the tile.
        projection: str
            Projection in which polygon is defined.
        """
        self.proj_polygon = polygon
        self.polygon_coords = []
        self.projection   = projection
        
        # Convert polygon from its target projection to Cartesian coordinates 
        # (search API uses Cartesian coordinates)
        for each in polygon:
            coords = itslive_ui.transform_coord(projection, ITSCube.CARTESIAN_PROJECTION, each[0], each[1])
            self.polygon_coords.extend(coords)
       
        print(f"Longitude/latitude coords for polygon: {self.polygon_coords}")
        
        # Dictionary to store filtered (by polygon/start_date/end_date) velocities:
        # mid_date: velocity values
        self.velocities = {}
       
        self.layers = None

        
    def create(self, api_params, num_granules=None):
        """
        Create velocity cube.
        
        api_params: dict
            Search API required parameters.
        num: int
            Number of first granules to examine.
            TODO: This is a temporary solution to a very long time to open remote granules. Should not be used
                  when running the code at AWS.
        """
        # Re-set filtered velocities         
        self.velocities = {}
        self.layers = None

        # Append polygon information to API's parameters
        params = copy.deepcopy(api_params)
        params['polygon'] = ",".join([str(each) for each in self.polygon_coords])
        
        found_urls = [each['url'] for each in itslive_ui.get_granule_urls(params)]
        print("Originally found urls: ", len(found_urls))

        if len(found_urls) == 0:
            print(f"No granules are found for the search API parameters: {params}")
            return
        
        # Keep track of skipped granules due to the other than target projection
        skipped_proj_granules = []
        # Keep track of skipped granules due to the no data for the polygon of interest
        skipped_empty_granules = []

        # TODO: parallelize layer collection?
        s3 = s3fs.S3FileSystem(anon=True)
        
        # Number of granules to examine is specified (it's very slow to examine all granules sequentially)
        if num_granules:
            found_urls = found_urls[:num_granules]
            print(f"Examining only {len(found_urls)} first granules")
            
        for each_url in found_urls:
            s3_path = each_url.replace(ITSCube.HTTP_PREFIX, ITSCube.S3_PREFIX)
            s3_path = s3_path.replace(ITSCube.PATH_URL, '')
            
            with s3.open(s3_path, mode='rb') as fhandle:
                with xr.open_dataset(fhandle, engine=ITSCube.NC_ENGINE) as ds:
                    # Consider granules that have its data in the target projection only
                    if str(int(ds.UTM_Projection.spatial_epsg)) == self.projection:
                        # Filter by percent coverage for now:
#                         url = each_url.replace('.nc', '')
#                         url_tokens = url.split('_')
#                         percent = int(url_tokens[-1].replace('P', ''))
#                         print(f"URL: {each_url} percent={percent}")
#                         if percent <= 50:
#                             continue

                        # Consider granules only within target projection
                        mid_date = datetime.strptime(ds.img_pair_info.date_center,'%Y%m%d')

                        # Define which points are within target polygon.
                        # TODO: for now just assume it's a "perfect" rectangle defined by 5 points.
                        mask_lon = (ds.x >= self.proj_polygon[0][0]) & (ds.x <= self.proj_polygon[1][0])
                        mask_lat = (ds.y >= self.proj_polygon[1][1]) & (ds.y <= self.proj_polygon[2][1])

                        cube_v = ds.where(mask_lon & mask_lat , drop=True).v

                        # If it's a valid velocity layer, add it to the cube.
                        if np.any(cube_v.notnull()):
                            # Add middle date as a new coordinate
                            cube_v = cube_v.assign_coords({'mid_date': mid_date})

                            # TODO: Should store mid_date within each layer for self-consistency?
                            # cube_v.attrs['mid_date'] = mid_date

                            # TODO: There might be multiple layers for the mid_date, use filename to detect which one to include
                            #       into the cube: the one in target projection. 
                            #       Filename does not seem to include the same projection value as
                            #       ds.UTM_Projection.spatial_epsg - what to look for???
                            cube_v.attrs['projection'] = str(int(ds.UTM_Projection.spatial_epsg))

                            # Add file URL as its source for traceability
                            cube_v.attrs['url'] = each_url

                            # Use granule data as cube layer
                            self.velocities[mid_date] = cube_v.copy()

                        else:
                            skipped_empty_granules.append(each_url)

                    else:
                        skipped_proj_granules.append(each_url)
                
        # Construct xarray to hold layers by concatenating layer objects along 'mid_date' dimension
        for each_index, each_date in enumerate(sorted(self.velocities.keys())):
            if each_index == 0:
                self.layers = self.velocities[each_date]
                                        
            else:
                self.layers = xr.concat([self.layers, self.velocities[each_date]], 'mid_date')
        
        print( "Skipped granules:")
        print(f"      empty data: {len(skipped_empty_granules)} ({100.0 * len(skipped_empty_granules)/len(found_urls)}%)")
        print(f"      wrong proj: {len(skipped_proj_granules)} ({100.0 * len(skipped_proj_granules)/len(found_urls)}%)")


#         print(f"      empty data: {100.0 * len(skipped_empty_granules)/len(found_urls)}")
#         print(f"      wrong proj: {100.0 * len(skipped_proj_granules)/len(found_urls)}")
        return found_urls

        
    def plot_layers(self):
        """
        Plot cube's velocities in date order. Each layer has its own x/y coordinate labels based on data values 
        present in the layer. This method provides a better insight into data variation within each layer.
        """
        num_granules = len(self.velocities)
        
        num_cols = 5
        num_rows = int(num_granules / num_cols)
        print(f"rows={num_rows} cols={num_cols}")
        
        if (num_granules % num_cols) != 0:
            num_rows += 1
        
        fig, axes = plt.subplots(ncols=num_cols, nrows=num_rows, figsize=(num_cols*4, num_rows*4))
        col_index = 0
        row_index = 0
        for each_index, each_date in enumerate(sorted(self.velocities.keys())):
            if col_index == num_cols:
                col_index = 0
                row_index += 1
                
            self.velocities[each_date].plot(ax=axes[row_index, col_index])
            axes[row_index, col_index].title.set_text(str(each_date) + ' / ' + str(self.velocities[each_date].attrs['projection']))
            col_index += 1

        plt.tight_layout()
        plt.draw()        


    def plot_num_layers(self, num):
        """
        Plot cube's velocities in date order. Each layer has its own x/y coordinate labels based on data values 
        present in the layer. This method provides a better insight into data variation within each layer.
        """
        num_granules = len(self.velocities)
        
        fig, axes = plt.subplots(ncols=num, figsize=(num*4, 4))
        col_index = 0
        for each_index, each_date in enumerate(sorted(self.velocities.keys())):
               
            self.velocities[each_date].plot(ax=axes[each_index])
            axes[each_index].title.set_text(str(each_date) + ' / ' + str(self.velocities[each_date].attrs['projection']))
            col_index += 1

        plt.tight_layout()
        plt.draw()        


        
    def plot(self):
        """
        Plot cube's layers in date order. All layers share the same x/y coordinate labels.
        """
        self.layers.plot(x='x', y = 'y', col='mid_date', col_wrap=5, levels=100)
        