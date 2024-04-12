import os
import gc
import copy
import configparser
import pandas as pd
from lxml import etree as et
from pymaldiproc.data_import import import_mzml, import_timstof_raw_data
from pymaldiviz.util import *
from bin.layout import *
from bin.util import *
from dash import State, callback_context, no_update, dash_table
from dash_extensions.enrich import Input, Output, DashProxy, MultiplexerTransform, Serverside, ServersideOutputTransform
import dash_bootstrap_components as dbc


# default processing parameters from config file
PREPROCESSING_PARAMS = get_preprocessing_params()

# get AutoXecute sequence path
AUTOX_SEQ = get_autox_sequence_filename()

# TODO: data directory, methods directory, and check if exists on system here
# read in AutoXecute sequence
ms1_autox = et.parse(AUTOX_SEQ).getroot()
# parse plate map
PLATE_FORMAT = get_geometry_format(ms1_autox)

BLANK_SPOTS = []

app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform(), ServersideOutputTransform()],
                external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = get_dashboard_layout(PREPROCESSING_PARAMS, PLATE_FORMAT, ms1_autox)


@app.callback(Output('plate_map', 'style_data_conditional'),
              Input('mark_spot_as_blank', 'n_clicks'),
              [State('plate_map', 'selected_cells'),
               State('plate_map', 'style_data_conditional'),
               State('plate_map', 'data')])
def mark_spots_as_blank(n_clicks, spots, cell_style, data):
    global BLANK_SPOTS
    indices = [(i['row'], i['column_id']) for i in spots]
    BLANK_SPOTS = BLANK_SPOTS + [data[i['row']][i['column_id']] for i in spots]
    return cell_style + [{'if': {'row_index': row, 'column_id': col},
                          'backgroundColor': 'green', 'color': 'white'}
                         for row, col in indices]


if __name__ == '__main__':
    app.run_server(debug=False)
