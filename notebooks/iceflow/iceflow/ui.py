import pandas as pd
import ipywidgets as widgets
from datetime import datetime
import requests
from sidecar import Sidecar
from IPython.display import display
from ipyleaflet import (Map, SearchControl, AwesomeIcon, GeoJSON,
                        Marker, DrawControl, LayersControl)
from .layers import custom_layers, flight_layers, widget_projections
from .client import IceflowClient


class IceFlowUI:
    """
    UI for the IceFlow API
    """
    def __init__(self):
        self.out = widgets.Output(layout={'border': '1px solid black'})
        self.iceflow = IceflowClient()
        self.current_projection = 'north'
        self.controls = []
        self.credentials = None
        self.start_date = datetime(1993, 1, 1)
        self.end_date = datetime.now()
        slider_dates = [(date.strftime(' %Y-%m-%d '), date) for date in
                        pd.date_range(datetime(1993, 1, 1),
                                      datetime.now(),
                                      freq='D')]
        slider_index = (0, len(slider_dates) - 1)

        self.username = widgets.Text(
            value='',
            description='User:',
            placeholder='Your NASA EarthData username ',
            disabled=False
        )
        self.password = widgets.Password(
            value='',
            placeholder='Enter password',
            description='Password:',
            disabled=False
        )
        self.email = widgets.Text(
            value='',
            description='Email:',
            placeholder='Your EarthData e-mail',
            disabled=False
        )
        self.credentials_button = widgets.Button(description='Set Credentials', )
        self.projection = widgets.Dropdown(
            options=['global', 'south', 'north'],
            description='Hemisphere:',
            disabled=False,
            value='north'
        )
        self.dataset = widgets.SelectMultiple(
            options=['ILATM1B', 'BLATM1B', 'GLAH06', 'ILVIS2'],
            value=['ILATM1B'],
            rows=4,
            description='Datasets',
            disabled=False
        )
        self.itrf = widgets.Dropdown(
            options=[None, 'ITRF2000', 'ITRF2008', 'ITRF2014'],
            disabled=False,
            description='ITRF:',
            layout={'width': 'max-content',
                    'display': 'flex',
                    'description_width': 'initial'}
        )
        self.epoch = widgets.Text(
            value='',
            description='Epoch:',
            placeholder='i.e. 2008.1',
            disabled=False
        )
        self.is2 = widgets.Dropdown(
            options=['None', 'ATL03', 'ATL06', 'ATL07', 'ATL08'],
            description='ICESat 2:',
            disabled=False,
        )
        self.dates_range = widgets.SelectionRangeSlider(
            options=slider_dates,
            index=slider_index,
            continuous_update=False,
            description='Date Range',
            orientation='horizontal',
            layout={'width': '90%'})

        self.granule_count = widgets.Button(description="Get Raw Granule Count",
                                            display='flex',
                                            flex_flow='column',
                                            align_items='stretch', )
        self.granule_count.style.button_color = 'lightgreen'
        self.granule_count.layout.width = 'auto'
        self.print_parameters = widgets.Button(description="Print Current Parameters",
                                               display='flex',
                                               flex_flow='column',
                                               align_items='stretch', )
        self.print_parameters.style.button_color = 'lightgreen'
        self.print_parameters.layout.width = 'auto'
        self.post_order = widgets.Button(description="Place Data Order",
                                         display='flex',
                                         flex_flow='column',
                                         align_items='stretch', )
        self.post_order.style.button_color = 'lightblue'
        self.post_order.layout.width = 'auto'
        self.selection_buttons = widgets.HBox([self.granule_count,
                                               self.print_parameters,
                                               self.post_order])
        self.selection_controls = widgets.VBox([self.projection,
                                                self.dataset,
                                                self.itrf,
                                                self.epoch,
                                                self.is2,
                                                self.dates_range,
                                                self.selection_buttons])
        self.controls.append(self.selection_controls)
        self.layers_control = LayersControl(position='topright')
        # Map Components
        place_marker = Marker(icon=AwesomeIcon(name="check", marker_color='green', icon_color='darkgreen'))
        self.search_control = SearchControl(
            position="topleft",
            url='https://nominatim.openstreetmap.org/search?format=json&q={s}',
            zoom=5,
            marker=place_marker
        )
        self.dc = DrawControl(
            circlemarker={},
            polyline={},
            rectangle={
                "shapeOptions": {
                    "fillColor": "#cc00cc",
                    "color": "#cc00cc",
                    "fillOpacity": 0.5
                }
            })
        self.file_upload = widgets.FileUpload(
            accept='.json,.geojson,.shp',
            multiple=False  # True to accept multiple files upload else False
        )

        # Now we are going to link the controls to the relevant events
        self.dates_range.observe(self.dates_changed, 'value')
        self.projection.observe(self.hemisphere_change)
        self.credentials_button.on_click(self.set_credentials)
        self.granule_count.on_click(self.query_cmr)
        self.post_order.on_click(self.place_data_orders)
        self.print_parameters.on_click(self.get_parameters)

    def get_parameters(self, change):
        print(self.build_parameters())

    def hemisphere_change(self, change):
        if change['type'] == 'change' and change['name'] == 'value':
            self.display_map(self.map_output, hemisphere=self.projection.value)

    def dates_changed(self, change):
        if change['type'] == 'change' and change['name'] == 'value':
            start, end = change['new']
            self.start_date = start
            self.end_date = end
            # we filter the geopandas datafram to only display flights within the user range
            self.display_map(self.map_output)

    def set_credentials(self, event):
        if (self.username.value != '' and self.password.value != ''):
            self.credentials = {
                'username': self.username.value,
                'password': self.password.value,
                'email': self.email.value
            }
            self.authenticate()
        else:
            print('enter your NASA Earth login credentials')
            self.credentials = None
            return None

    def display_credentials(self, where='horizontal'):
        """
        renders the input controls to get the user's credentials
        note that theey are not enccrypted here.
        """
        if where == 'vertical':
            if not hasattr(self, 'sc'):
                self.sc = Sidecar(title='Map Widget')
            with self.sc:
                display(self.username, self.password, self.email, self.credentials_button)
        else:
            display(self.username, self.password, self.email, self.credentials_button)

    def display_controls(self, where):
        if where == 'vertical':
            if not hasattr(self, 'sc'):
                self.sc = Sidecar(title='Map Widget')
            with self.sc:
                for component in self.controls:
                    display(component)
        else:
            for component in self.controls:
                display(component)

    def display_map(self, map_output, hemisphere=None, extra_layers=True):
        """
        Will render the UI using ipyleaflet and jupyter widgets
        """
        self.map_output = map_output
        self.dc = DrawControl(
            circlemarker={},
            polyline={},
            rectangle={
                "shapeOptions": {
                    "fillColor": "#cc00cc",
                    "color": "#cc00cc",
                    "fillOpacity": 0.5
                }
            })
        if hemisphere is None:
            projection = widget_projections[self.projection.value]
        else:
            projection = widget_projections[hemisphere]

        # TODO: maybe there is a way to create the map in the constructor
        # and just update its properties to see if this is faster.
        self.map = Map(center=projection['center'],
                       zoom=projection['zoom'],
                       max_zoom=projection['max_zoom'],
                       basemap=projection['base_map'],
                       crs=projection['projection'])

        self.map.add_control(self.dc)
        self.map.add_control(self.layers_control)
        self.map.add_control(self.search_control)

        for ib_layer in flight_layers[self.projection.value]:
            self.map.add_layer(ib_layer(self.start_date, self.end_date))
        if extra_layers:
            for layer in custom_layers[self.projection.value]:
                self.map.add_layer(layer)

        # if self.dc.last_draw['geometry'] is not None:
        #     self.map.add_layer(GeoJSON(name='selected geometry', data=self.dc.last_draw))
        self.map.layout.height = '560px'
        self.out.clear_output()
        if map_output == 'vertical':
            if hasattr(self, 'sc'):
                self.sc.clear_output()
            else:
                self.sc = Sidecar(title='Map Widget')
            with self.sc:
                display(self.out)
            with self.out:
                display(self.map)
                for component in self.controls:
                    display(component)

        else:
            with self.out:
                display(self.map)
            display(self.out)

    def bounding_box(self, points):
        """
        returns a bbox array for a given polygon
        """
        x_coordinates, y_coordinates = zip(*points)
        return [(min(x_coordinates), min(y_coordinates)), (max(x_coordinates), max(y_coordinates))]

    def build_parameters(self):
        """
        returns the current selection parameters based on the widgets and map state
        """
        self.datasets_iceflow = []
        if self.dc.last_draw['geometry'] is None:
            print('You need to select an area using the bbox or polygon tools')
            return None
        coords = [list(coord) for coord in self.bounding_box(self.dc.last_draw['geometry']['coordinates'][0])]
        bbox = f'{coords[0][0]},{coords[0][1]},{coords[1][0]},{coords[1][1]}'
        start = self.dates_range.value[0].date().strftime('%Y-%m-%d')
        end = self.dates_range.value[1].date().strftime('%Y-%m-%d')
        ITRF = self.itrf.value
        epoch = self.epoch.value
        selected_datasets = self.dataset.value
        for d in selected_datasets:
            self.datasets_iceflow.append(d)
        if self.is2.value != 'None':
            self.datasets_iceflow.append(self.is2.value)
        params = {
            'start': start,
            'end': end,
            'bbox': bbox,
            'datasets': self.datasets_iceflow
        }
        if ITRF != 'None' and ITRF is not None:
            params['itrf'] = ITRF

        if epoch != 'None' and epoch != '':
            params['epoch'] = epoch
        return params

    def query_cmr(self, event=None, params=None):
        if params is None:
            params = self.build_parameters()
        granules = self.iceflow.query_cmr(params)
        return granules

    def place_data_orders(self, event=None, params=None):
        if params is None:
            params = self.build_parameters()
        orders = self.iceflow.post_data_orders(params)
        return orders

    def authenticate(self):
        user = self.credentials['username']
        password = self.credentials['password']
        email = self.credentials['email']
        session = self.iceflow.authenticate(user, password, email)
        return session

    def order_status(self, orders):
        for order in orders:
            status_url = order['response'].json()['status_url']
            status = requests.get(status_url).json()
            print(status)

