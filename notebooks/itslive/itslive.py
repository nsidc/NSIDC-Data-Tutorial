import requests
from joblib import Parallel, delayed
from datetime import datetime
from ipyleaflet import Map
import ipywidgets as widgets
import xarray as xr
import os
import glob
import pyproj
from collections import defaultdict

from utils import (north_3413, south_3031, projections, draw_control,
                   projection_control, dates_slider_control, pixels_control,
                   time_delta_control, format_polygon, get_minimal_bbox)


class itslive_ui:

    def __init__(self, hemisphere):
        self.properties = {
            'start_date': datetime(1984, 1, 1),
            'end_date': datetime(2020, 1, 1),
            'pixels': 1,
            'time_delta': 0,
            'polygon': '',
            'hemisphere': hemisphere
        }

        self.projections = projections
        self.h = projection_control(self.properties)
        self.dc = draw_control(self.properties)
        self.date_range = dates_slider_control(self.properties)
        self.pixels = pixels_control(self.properties)
        self.pixels_control = widgets.HBox([
            widgets.Label('Minimum % of valid pixels per image pair:'),
            self.pixels])
        self.time_delta = time_delta_control(self.properties)
        self.time_delta_control = widgets.HBox([
            widgets.Label('Maximum days of separation between image pairs:'),
            self.time_delta])

        self.components = [self.h,
                           self.pixels_control,
                           self.time_delta_control,
                           self.date_range]

    def render(self):
        self.map = Map(center=self.projections[self.h.value]['center'],
                       zoom=1,
                       basemap=self.projections[self.h.value]['base_map'],
                       crs=self.projections[self.h.value]['projection'])

        self.map.add_control(self.dc)
        self.map.layout.height = '600px'
        for component in self.components:
            display(component)
        display(self.map)

    def update_coverages(self):
        base_url = 'https://staging.itslive-search.apps.nsidc.org/velocities/coverage/'
        params = self.build_params()
        resp = requests.get(base_url, params=params, verify=False)
        self.coverage = resp.json()
        return self.coverage

    @staticmethod
    def get_granule_urls(params):
        base_url = 'https://staging.itslive-search.apps.nsidc.org/velocities/urls/'
        resp = requests.get(base_url, params=params, verify=False)
        return resp.json()
#         return self.urls

    def get_url_size(self, url, sizes):
        size = 0
        try:
            resp = requests.head(url)
            size = float("{:.2f}".format(int(resp.headers['Content-Length'])/1024))
        except IOError:
            sizes.append(size)
            return
        sizes.append(size)

    def calculate_file_sizes(self, urls, max_urls):
        file_sizes = []
        Parallel(n_jobs=8, backend="threading")(
            delayed(self.get_url_size)(url['url'],file_sizes) for url in urls[0:max_urls]
        )
        return file_sizes

    def build_params(self):
        if self.dc.last_draw['geometry'] is None:
            print('You need to select an area using the box tool or the polygon drawing tool')
            return None
        if self.dc.last_draw['geometry']['type'] == 'Point':
            polygon_coords = get_minimal_bbox(self.dc.last_draw['geometry'])
        else:
            polygon_coords = format_polygon(self.dc.last_draw['geometry'])
        start = self.date_range.value[0].date().strftime('%Y-%m-%d')
        end = self.date_range.value[1].date().strftime('%Y-%m-%d')
        pixels = self.pixels.value

        params = {
            'polygon': polygon_coords,
            'start': start,
            'end': end,
            'percent_valid_pixels': pixels,
        }
        if self.time_delta.value != 'any':
            params['time_delta'] = self.time_delta.value
        return params

    @staticmethod
    def _get_temporal_coverage(url):
        file_name = url.split('/')[-1].replace('.nc', '')
        file_components = file_name.split('_')
        start_date = datetime.strptime(file_components[3], "%Y%m%d").date()
        end_date = datetime.strptime(file_components[4], "%Y%m%d").date()
        mid_date = start_date + (end_date - start_date) / 2

        coverage = {
            'url': url,
            'start': start_date,
            'end': end_date,
            'mid_date': mid_date
        }
        return coverage

    @staticmethod
    def filter_urls(urls, max_files_per_year, months):
        # LE07_L1TP_008012_20030417_20170125_01_T1_X_LE07_L1TP_008012_20030401_20170126_01_T1_G0240V01_P095.nc
        filtered_urls = []
        files_by_year = {}
        
        for url in urls:
            coverage = itslive_ui._get_temporal_coverage(url)
            
            if coverage['mid_date'].month in months:
                year_urls = files_by_year.setdefault(coverage['mid_date'].year, [])
  
                if len(year_urls) >= max_files_per_year:
                    continue

                year_urls.append(url)
                filtered_urls.append(url)

#                 print(f"year: {coverage['mid_date'].year} month: {coverage['mid_date'].month}")
#                 if coverage['mid_date'].year in files_by_year:
#                     if len(files_by_year[coverage['mid_date'].year]) < max_files_per_year:
#                         files_by_year[coverage['mid_date'].year].append(url)
#                         filtered_urls.append(url)
#                 else:
#                     files_by_year[coverage['mid_date'].year].append(url)
#                     filtered_urls.append(url)

        print("URL years: ", files_by_year)
        return filtered_urls

    def download_velocity_pairs(self, urls, start, end):
        file_paths = []
        Parallel(n_jobs=8, backend="threading")(
            delayed(self.download_file)(url, file_paths) for url in urls[start:end]
        )
        return file_paths

    def download_file(self, url, file_paths):
        local_filename = url.split('/')[-1]
        # NOTE the stream=True parameter below
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            if not os.path.exists(f'data/{local_filename}'):
                with open('data/' + local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            file_paths.append(local_filename)
        return local_filename

    def load_velocity_pairs(self, directory):
        velocity_pairs = []
        for file in glob.glob(directory + '/*.nc'):
            ds = xr.open_dataset(file)
            velocity_pairs.append(ds)
        return velocity_pairs

    @staticmethod
    def transform_coord(proj1, proj2, lon, lat):
        """Transform coordinates from proj1 to proj2 (EPSG num)."""
        # Set full EPSG projection strings
        proj1 = pyproj.Proj("+init=EPSG:"+proj1)
        proj2 = pyproj.Proj("+init=EPSG:"+proj2)
        # Convert coordinates
        return pyproj.transform(proj1, proj2, lon, lat)

