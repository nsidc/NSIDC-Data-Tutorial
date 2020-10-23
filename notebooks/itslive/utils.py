import pandas as pd
from shapely.geometry import box
import ipywidgets as widgets
import itertools
from ipyleaflet import projections, basemaps, DrawControl
import numpy as np

north_3413 = {
    'name': 'EPSG:3413',
    'custom': True,
    'proj4def': '+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs',
    'origin': [-4194304, 4194304],
    'bounds': [
        [-4194304, -4194304],
        [4194304, 4194304]
    ],
    'resolutions': [
        16384.0,
        8192.0,
        4096.0,
        2048.0,
        1024.0,
        512.0,
        256.0
    ]
}

south_3031 = {
    'name': 'EPSG:3031',
    'custom': True,
    'proj4def': '+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs',
    'origin': [-4194304, 4194304],
    'bounds': [
        [-4194304, -4194304],
        [4194304, 4194304]
    ],
    'resolutions': [
        16384.0,
        8192.0,
        4096.0,
        2048.0,
        1024.0,
        512.0,
        256.0
    ]
}

projections = {
    'global': {
        'base_map': basemaps.NASAGIBS.BlueMarble,
        'projection': projections.EPSG3857,
        'center': (0,0)
    },
    'north': {
        'base_map': basemaps.NASAGIBS.BlueMarble3413,
        'projection': north_3413,
        'center': (90, 0)
    },
    'south': {
        'base_map': basemaps.NASAGIBS.BlueMarble3031,
        'projection': south_3031,
        'center': (-90, 0)
    }
}


def dates_slider_control(properties):
    slider_dates = [(date.strftime(' %Y-%m-%d '), date) for date in
                    pd.date_range(properties['start_date'],
                                  properties['end_date'],
                                  freq='D')]
    slider_index = (0, len(slider_dates)-1)
    date_slider_control = widgets.SelectionRangeSlider(
                options=slider_dates,
                index=slider_index,
                description='Date Range',
                orientation='horizontal',
                layout={'width': '100%'})
    return date_slider_control


def draw_control(properties):
    control = DrawControl(circlemarker={
                "shapeOptions": {
                    "fillColor": "#efed69",
                    "color": "#efed69",
                    "fillOpacity": 1.0
                }
            },
            polygon={},
            polyline={},
            rectangle={}
    )
    return control


def pixels_control(properties):
    valid_percentages = [str(p) for p in range(0, 100, 10)]
    valid_percentages[0] = 1
    pixels = widgets.Dropdown(
        options=valid_percentages,
        disabled=False,
        layout={'width': 'max-content',
                'display': 'flex',
                'description_width': 'initial'}
    )
    return pixels


def time_delta_control(properties):
    time_delta = widgets.Dropdown(
        options=['any', '17', '33', '67', '135', '365'],
        disabled=False,
        layout={'width': 'max-content',
                'display': 'flex',
                'description_width': 'initial'}
    )
    return time_delta


def projection_control(properties):
    control = widgets.Dropdown(
        options=['global', 'south', 'north'],
        description='Hemisphere:',
        disabled=False,
        value=properties['hemisphere']
    )
    return control


def format_polygon(geometry):
    coords = [[str(float("{:.4f}".format(coord[0]))),str(float("{:.4f}".format(coord[1])))] for coord in geometry['coordinates'][0]]
    coords = list(itertools.chain.from_iterable(coords))
    polygonstr = ','.join(coords)
    return polygonstr

def get_minimal_bbox(geometry):
    """
    a very rough approximation of a small bbox less than 1km of a given lon-lat point
    params: geometry, a geojson point geometry
    """
    lon = geometry['coordinates'][0]
    lat = geometry['coordinates'][1]
    if lon < 0.0:
        lon_offset = -0.001
    else:
        lon_offset = 0.001
    if lat < 0.0:
        lat_offset = -0.001
    else:
        lat_offset = 0.001

    bbox = box(lon - lon_offset, lat - lat_offset, lon + lon_offset, lat + lat_offset)
    coords = [[str(float("{:.4f}".format(coord[0]))),str(float("{:.4f}".format(coord[1])))] for coord in bbox.exterior.coords]
    coords = list(itertools.chain.from_iterable(coords))
    return ','.join(coords)


class Grid:
    """
    Grid specific helper functions.
    """
    
    # Supported grid sizes
    _SUPPORTED_SIZES = [60, 120, 240, 480, 960, 1920, 3840]
    
    @staticmethod
    def bounds(x_min, x_max, y_min, y_max, grid_spacing):
        """
        Define bounding box for provided coordinates.
        """
        # Check input
        # Check if requested grid size is allowable
        if grid_spacing not in Grid._SUPPORTED_SIZES:
            raise RuntimeError(f'Grid spacing shoud be one of {Grid._SUPPORTED_SIZES} to keep grids of different spacing aligned')
    
        if x_min >= x_max:
            raise RuntimeError(f'xmin ({x_min}) must be < xmax ({x_max})')
            
        elif y_min >= y_max:
            raise RuntimeError(f'y_min ({y_min}) must be < y_max ({y_max})')

        # Ddeteremine grid edges
        x0_min = np.floor(x_min/grid_spacing)*grid_spacing
        y0_min = np.floor(y_min/grid_spacing)*grid_spacing
        x0_max = np.ceil(x_max/grid_spacing)*grid_spacing
        y0_max = np.ceil(y_max/grid_spacing)*grid_spacing
        
        return x0_min, x0_max, y0_min, y0_max
    
    def create_grid(x_min, x_max, y_min, y_max, grid_spacing):
        """
        Create new grid given the spacing and bounding box for the region.
        """
        # Calculate grid bounds
        x0_min, x0_max, y0_min, y0_max = Grid.bounds(x_min, x_max, y_min, y_max, grid_spacing)

        # Generate vectors of grid centers
        # Cell center offset
        cell_center_offset = grid_spacing/2
        x = np.arange(x0_min + cell_center_offset, x0_max, grid_spacing)
        y = np.arange(y0_min + cell_center_offset, y0_max, grid_spacing)
        
        return x, y

        
        