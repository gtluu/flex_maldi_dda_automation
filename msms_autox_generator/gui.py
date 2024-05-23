import toml
from lxml import etree as et
from pymaldiproc.data_import import import_timstof_raw_data
from pymaldiproc.preprocessing import get_feature_matrix
from pymaldiviz.util import *
from msms_autox_generator.layout import *
from msms_autox_generator.util import *
from msms_autox_generator.tmpdir import FILE_SYSTEM_BACKEND
from dash import State, callback_context, no_update, MATCH, ALL
from dash_extensions.enrich import (Input, Output, DashProxy, MultiplexerTransform, Serverside,
                                    ServersideOutputTransform, FileSystemBackend)
import dash_bootstrap_components as dbc
from plotly_resampler import FigureResampler

# TODO: figure out Dash data store instead of using all these global vars
# default processing parameters from config file
PREPROCESSING_PARAMS = get_preprocessing_params()
PREPROCESSING_PARAMS['TRIM_SPECTRUM']['run'] = False
PREPROCESSING_PARAMS['TRANSFORM_INTENSITY']['run'] = False
PREPROCESSING_PARAMS['SMOOTH_BASELINE']['run'] = False
PREPROCESSING_PARAMS['REMOVE_BASELINE']['run'] = False
PREPROCESSING_PARAMS['NORMALIZE_INTENSITY']['run'] = False
PREPROCESSING_PARAMS['BIN_SPECTRUM']['run'] = False
"""config = configparser.ConfigParser()
config.read(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'etc', 'preprocessing.cfg'))
PREPROCESSING_PARAMS['ALIGN_SPECTRA'] = {'run': False,
                                         'method': config['align_spectra']['method'],
                                         'inter': config['align_spectra']['inter'],
                                         'n': config['align_spectra']['n'],
                                         'scale': None,
                                         'coshift_preprocessing': config['align_spectra'].getboolean(
                                             'coshift_preprocessing'),
                                         'coshift_preprocessing_max_shift': None,
                                         'fill_with_previous': config['align_spectra'].getboolean('fill_with_previous'),
                                         'average2_multiplier': int(config['align_spectra']['average2_multiplier'])}"""
PREPROCESSING_PARAMS['PRECURSOR_SELECTION'] = {'top_n': 10,
                                               'use_exclusion_list': True,
                                               'exclusion_list_tolerance': 0.05}
# Copies of PREPROCESSING_PARAMS for logging
BLANK_PARAMS_LOG = {}
SAMPLE_PARAMS_LOG = {}

# get AutoXecute sequence path
AUTOX_SEQ = get_autox_sequence_filename()

# read in AutoXecute sequence
MS1_AUTOX = et.parse(AUTOX_SEQ).getroot()
# parse plate map
PLATE_FORMAT = get_geometry_format(MS1_AUTOX)
# parse raw data and method paths
AUTOX_PATH_DICT = {index: {'sample_name': spot_group.attrib['sampleName'],
                           'raw_data_path': f"{os.path.join(MS1_AUTOX.attrib['directory'], spot_group.attrib['sampleName'])}.d",
                           'method_path': spot_group.attrib['acqMethod']}
                   for index, spot_group in enumerate(MS1_AUTOX)}

INDEXED_DATA = {}
BLANK_SPOTS = []
SPOT_GROUPS = {}

app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform(),
                            ServersideOutputTransform(backends=[FileSystemBackend(cache_dir=FILE_SYSTEM_BACKEND)])],
                external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = get_dashboard_layout(PREPROCESSING_PARAMS, PLATE_FORMAT, AUTOX_PATH_DICT, MS1_AUTOX)


@app.callback([Output({'type': 'raw_data_path_input', 'index': MATCH}, 'value'),
               Output({'type': 'raw_data_path_input', 'index': MATCH}, 'valid'),
               Output({'type': 'raw_data_path_input', 'index': MATCH}, 'invalid')],
              [Input({'type': 'raw_data_path_button', 'index': MATCH}, 'n_clicks'),
               Input({'type': 'raw_data_path_button', 'index': MATCH}, 'id')])
def update_raw_data_path(n_clicks, button_id):
    """
    Dash callback to update the raw data path during AutoXecute sequence data path validation.

    :param n_clicks: Input signal when a given raw_data_path_button button is clicked.
    :param button_id: ID of the raw_data_path_button clicked.
    :return: Tuple of the updated Bruker .d directory path, whether the path is valid, and whether the path is invalid.
    """
    global AUTOX_PATH_DICT
    dirname = get_path_name()
    if (dirname.endswith('.d') and
            os.path.exists(dirname) and
            os.path.splitext(os.path.split(dirname)[-1])[0] == AUTOX_PATH_DICT[button_id['index']]['sample_name']):
        AUTOX_PATH_DICT[button_id['index']]['raw_data_path'] = dirname
        return dirname, True, False
    else:
        return dirname, False, True


@app.callback([Output({'type': 'method_path_input', 'index': MATCH}, 'value'),
               Output({'type': 'method_path_input', 'index': MATCH}, 'valid'),
               Output({'type': 'method_path_input', 'index': MATCH}, 'invalid')],
              [Input({'type': 'method_path_button', 'index': MATCH}, 'n_clicks'),
               Input({'type': 'method_path_button', 'index': MATCH}, 'id')])
def update_method_path(n_clicks, button_id):
    """
    Dash callback to update the method path during AutoXecute sequence method path validation.

    :param n_clicks: Input signal when a given method_path_button button is clicked.
    :param button_id: ID of the method_path_button clicked.
    :return: Tuple of the updated Bruker .m directory path, whether the path is valid, and whether the path is invalid.
    """
    global AUTOX_PATH_DICT
    dirname = get_path_name()
    if dirname.endswith('.m') and os.path.exists(dirname):
        AUTOX_PATH_DICT[button_id['index']]['method_path'] = dirname
        return dirname, True, False
    else:
        return dirname, False, True


@app.callback(Output('autox_validation_modal', 'is_open'),
              Input('autox_validation_modal_close', 'n_clicks'),
              [State({'type': 'raw_data_path_input', 'index': ALL}, 'value'),
               State({'type': 'raw_data_path_input', 'index': ALL}, 'valid'),
               State({'type': 'method_path_input', 'index': ALL}, 'valid'),
               State('autox_validation_modal', 'is_open')])
def toggle_autox_validation_modal_close(n_clicks, raw_data_path_input, raw_data_path_input_valid,
                                        method_path_input_valid, is_open):
    """
    Dash callback to toggle the AutoXecute sequence data/method validation modal window. Data is imported when all
    data and method paths are valid and the modal window is closed.

    :param n_clicks: Input signal if the autox_validation_modal_close button is clicked.
    :param raw_data_path_input: List of paths of all the raw data to be loaded.
    :param raw_data_path_input_valid: List of booleans stating whether the raw data paths are valid or not.
    :param method_path_input_valid: List of booleans stating whether the method paths are valid or not.
    :param is_open: State signal to determine whether the autox_validation_modal modal window is open.
    :return: Output signal to determine whether the autox_validation_modal modal window is open.
    """
    global INDEXED_DATA
    if n_clicks:
        for i, j in zip(raw_data_path_input_valid, method_path_input_valid):
            if not i or not j:
                return is_open
        for path in raw_data_path_input:
            data = import_timstof_raw_data(path, mode='profile')
            for spectrum in data:
                INDEXED_DATA[spectrum.coord] = spectrum
        return not is_open
    return is_open


@app.callback([Output('plate_map', 'style_data_conditional'),
               Output('plate_map_legend', 'style_data_conditional'),
               Output('plate_map_legend', 'data'),
               Output('new_group_name_modal', 'is_open'),
               Output('new_group_name_modal_input_value', 'value'),
               Output('plate_map', 'selected_cells'),
               Output('plate_map', 'active_cell'),
               Output('group_spots_error_modal', 'is_open')],
              [Input('group_spots', 'n_clicks'),
               Input('new_group_name_modal_save', 'n_clicks'),
               Input('group_spots_error_modal_close', 'n_clicks')],
              [State('plate_map', 'selected_cells'),
               State('plate_map', 'style_data_conditional'),
               State('plate_map', 'data'),
               State('plate_map_legend', 'style_data_conditional'),
               State('plate_map_legend', 'data'),
               State('new_group_name_modal_input_value', 'value'),
               State('new_group_name_modal_input_value', 'valid'),
               State('new_group_name_modal', 'is_open'),
               State('group_spots_error_modal', 'is_open')])
def group_spots(n_clicks_group_spots, n_clicks_new_group_name_modal_save, n_clicks_group_spots_error_modal_close, spots,
                plate_map_cell_style, plate_map_data, plate_map_legend_cell_style, plate_map_legend_data,
                new_group_name, new_group_name_valid, new_group_name_modal_is_open,
                group_name_spots_error_modal_is_open):
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    global BLANK_SPOTS
    global SPOT_GROUPS
    if changed_id == 'group_spots.n_clicks':
        if spots:
            error = False
            for spot in spots:
                spot = plate_map_data[spot['row']][spot['column_id']]
                if spot in BLANK_SPOTS or spot in [i for value in SPOT_GROUPS.values() for i in value]:
                    error = True
            if not error:
                return plate_map_cell_style, plate_map_legend_cell_style, plate_map_legend_data, not new_group_name_modal_is_open, '', spots, None, group_name_spots_error_modal_is_open
            elif error:
                return plate_map_cell_style, plate_map_legend_cell_style, plate_map_legend_data, new_group_name_modal_is_open, '', spots, None, not group_name_spots_error_modal_is_open
    elif changed_id == 'new_group_name_modal_save.n_clicks' and new_group_name_valid and \
            new_group_name not in pd.DataFrame(plate_map_legend_data)['Category'].values.tolist():
        gray_indices = [(style_dict['if']['row_index'], style_dict['if']['column_id'])
                        for style_dict in plate_map_cell_style
                        if 'if' in style_dict.keys() and 'backgroundColor' in style_dict.keys()
                        if style_dict['backgroundColor'] == 'gray'
                        if 'row_index' in style_dict['if'].keys() and 'column_id' in style_dict['if'].keys()]
        indices = [(i['row'], i['column_id']) for i in spots]
        indices = [i for i in indices if i not in gray_indices]
        SPOT_GROUPS[new_group_name] = [plate_map_data[i[0]][i[1]] for i in indices]
        color = get_rgb_color()
        plate_map_cell_style = plate_map_cell_style + [{'if': {'row_index': row, 'column_id': col},
                                                        'backgroundColor': color, 'color': 'white'}
                                                       for row, col in indices]
        plate_map_legend_df = pd.concat([pd.DataFrame(plate_map_legend_data),
                                         pd.DataFrame({'Category': [new_group_name]})], ignore_index=True)
        plate_map_legend_cell_style = plate_map_legend_cell_style + [{'if': {'row_index': plate_map_legend_df.shape[0]-1},
                                                                      'backgroundColor': color, 'color': 'white'}]
        return plate_map_cell_style, plate_map_legend_cell_style, plate_map_legend_df.to_dict('records'), not new_group_name_modal_is_open, '', [], None, group_name_spots_error_modal_is_open
    elif changed_id == 'group_spots_error_modal_close.n_clicks':
        return plate_map_cell_style, plate_map_legend_cell_style, plate_map_legend_data, new_group_name_modal_is_open, '', spots, None, not group_name_spots_error_modal_is_open
    else:
        return plate_map_cell_style, plate_map_legend_cell_style, plate_map_legend_data, new_group_name_modal_is_open, '', [], None, group_name_spots_error_modal_is_open


@app.callback([Output('new_group_name_modal_input_value', 'valid'),
               Output('new_group_name_modal_input_value', 'invalid')],
              Input('new_group_name_modal_input_value', 'value'),
              [State('new_group_name_modal_input_value', 'value'),
               State('plate_map_legend', 'data')])
def check_if_new_group_name_valid(input_value, state_value, plate_map_legend_data):
    if state_value != '' and state_value not in pd.DataFrame(plate_map_legend_data)['Category'].values.tolist():
        return True, False
    return False, True


@app.callback([Output('plate_map', 'style_data_conditional'),
               Output('plate_map', 'selected_cells'),
               Output('plate_map', 'active_cell'),
               Output('group_spots_error_modal', 'is_open')],
              [Input('mark_spot_as_blank', 'n_clicks'),
               Input('group_spots_error_modal_close', 'n_clicks')],
              [State('plate_map', 'selected_cells'),
               State('plate_map', 'style_data_conditional'),
               State('plate_map', 'data'),
               State('group_spots_error_modal', 'is_open')])
def mark_spots_as_blank(n_clicks_mark_spot_as_blank, n_clicks_group_spots_error_modal_close, spots, cell_style, data,
                        is_open):
    """
    Dash callback to mark a selected spot in the plate map as a 'blank' spot by changing the cell style and adding the
    cell ID to the global variable BLANK_SPOTS.

    :param n_clicks: Input signal if the mark_spot_as_blank button is clicked.
    :param spots: Currently selected cells in the plate map.
    :param cell_style: Current style of the selected cells in the plate map.
    :param data: State signal containing plate map data.
    :return: Style data with the updated blank spot style for the selected cells appended.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    global BLANK_SPOTS
    global SPOT_GROUPS
    if changed_id == 'mark_spot_as_blank.n_clicks':
        error = False
        for spot in spots:
            spot = data[spot['row']][spot['column_id']]
            if spot in BLANK_SPOTS or spot in [i for value in SPOT_GROUPS.values() for i in value]:
                error = True
        if not error:
            gray_indices = [(style_dict['if']['row_index'], style_dict['if']['column_id'])
                            for style_dict in cell_style
                            if 'if' in style_dict.keys() and 'backgroundColor' in style_dict.keys()
                            if style_dict['backgroundColor'] == 'gray'
                            if 'row_index' in style_dict['if'].keys() and 'column_id' in style_dict['if'].keys()]
            indices = [(i['row'], i['column_id']) for i in spots]
            indices = [i for i in indices if i not in gray_indices]
            BLANK_SPOTS = BLANK_SPOTS + [data[i[0]][i[1]] for i in indices if data[i[0]][i[1]] not in BLANK_SPOTS]
            return cell_style + [{'if': {'row_index': row, 'column_id': col},
                                  'backgroundColor': 'green', 'color': 'white'}
                                 for row, col in indices], [], None, is_open
        elif error:
            return cell_style, [], None, not is_open
    elif changed_id == 'group_spots_error_modal_close.n_clicks':
        return cell_style, [], None, not is_open


@app.callback([Output('plate_map', 'style_data_conditional'),
               Output('plate_map_legend', 'style_data_conditional'),
               Output('plate_map_legend', 'data')],
              Input('clear_blanks_and_groups', 'n_clicks'))
def clear_blanks_and_groups(n_clicks):
    """
    Dash callback to remove all blank spot and spot group styling from the plate map, remove all blank spot IDs from
    the global variable BLANK_SPOTS, and remove all spot groups from the global variable SPOT_GROUPS.

    :param n_clicks: Input signal if the clear_blank_spots button is clicked.
    :return: Default style data for the plate map.
    """
    global BLANK_SPOTS
    global SPOT_GROUPS
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'clear_blanks_and_groups.n_clicks':
        BLANK_SPOTS = []
        SPOT_GROUPS = {}
        for key, spectrum in INDEXED_DATA.items():
            spectrum.undo_all_processing()
        return (get_plate_map_style(get_plate_map(PLATE_FORMAT), MS1_AUTOX),
                [{'if': {'row_index': 1},
                  'backgroundColor': 'green', 'color': 'white'},
                 {'if': {'row_index': 2},
                  'backgroundColor': 'gray', 'color': 'white'}],
                get_plate_map_legend().to_dict('records'))


@ app.callback([Output('exclusion_list', 'data'),
                Output('view_exclusion_list_spectra', 'style')],
               Input('generate_exclusion_list_from_blank_spots', 'n_clicks'))
def generate_exclusion_list_from_blank_spots(n_clicks):
    """
    Dash callback to perform preprocessing using parameters defined in the Edit Preprocessing Parameters modal window
    on blank spots marked on the plate map and generate an exclusion list to be displayed in the exclusion list table
    and used during sample precursor selection.

    :param n_clicks: Input signal if the generate_exclusion_list_from_blank_spots button is clicked.
    :return: Tuple of updated exclusion list data table data and style data to make the view_exclusion_list_spectra
        button visible.
    """
    global INDEXED_DATA
    global BLANK_SPOTS
    global PREPROCESSING_PARAMS
    global BLANK_PARAMS_LOG
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'generate_exclusion_list_from_blank_spots.n_clicks':
        blank_spectra = [INDEXED_DATA[spot] for spot in BLANK_SPOTS]
        params = copy.deepcopy(PREPROCESSING_PARAMS)
        BLANK_PARAMS_LOG = copy.deepcopy(PREPROCESSING_PARAMS)
        # preprocessing
        if params['TRIM_SPECTRUM']['run']:
            del params['TRIM_SPECTRUM']['run']
            for spectrum in blank_spectra:
                spectrum.trim_spectrum(**params['TRIM_SPECTRUM'])
        if params['TRANSFORM_INTENSITY']['run']:
            del params['TRANSFORM_INTENSITY']['run']
            for spectrum in blank_spectra:
                spectrum.transform_intensity(**params['TRANSFORM_INTENSITY'])
        if params['SMOOTH_BASELINE']['run']:
            del params['SMOOTH_BASELINE']['run']
            for spectrum in blank_spectra:
                spectrum.smooth_baseline(**params['SMOOTH_BASELINE'])
        if params['REMOVE_BASELINE']['run']:
            del params['REMOVE_BASELINE']['run']
            for spectrum in blank_spectra:
                spectrum.remove_baseline(**params['REMOVE_BASELINE'])
        if params['NORMALIZE_INTENSITY']['run']:
            del params['NORMALIZE_INTENSITY']['run']
            for spectrum in blank_spectra:
                spectrum.normalize_intensity(**params['NORMALIZE_INTENSITY'])
        if params['BIN_SPECTRUM']['run']:
            del params['BIN_SPECTRUM']['run']
            for spectrum in blank_spectra:
                spectrum.bin_spectrum(**params['BIN_SPECTRUM'])
        """# TODO: will need to ensure spectra are binned before alignment
        if params['ALIGN_SPECTRA']['run']:
            del params['ALIGN_SPECTRA']['run']
            blank_spectra = align_spectra(blank_spectra, **params['ALIGN_SPECTRA'])"""
        # peak picking
        for spectrum in blank_spectra:
            spectrum.peak_picking(**params['PEAK_PICKING'])
        # generate feature matrix
        blank_feature_matrix = get_feature_matrix(blank_spectra, missing_value_imputation=False)
        # get exclusion list and return as df.to_dict('records')
        exclusion_list_df = pd.DataFrame(data={'m/z': np.unique(blank_feature_matrix['mz'].values)})
        return exclusion_list_df.to_dict('records'), {'margin': '20px', 'display': 'flex'}


@app.callback([Output('exclusion_list_blank_spectra_modal', 'is_open'),
               Output('exclusion_list_blank_spectra_id', 'options'),
               Output('exclusion_list_blank_spectra_id', 'value'),
               Output('exclusion_list_blank_spectra_figure', 'figure')],
              [Input('view_exclusion_list_spectra', 'n_clicks'),
               Input('exclusion_list_blank_spectra_modal_close', 'n_clicks')],
              State('exclusion_list_blank_spectra_modal', 'is_open'))
def view_exclusion_list_spectra(n_clicks_view, n_clicks_close, is_open):
    """
    Dash callback to view the preprocessed blank spot spectra that were used to generate the exclusion list.

    :param n_clicks_view: Input signal if the view_exclusion_list_spectra button is clicked.
    :param n_clicks_close: Input signal if the exclusion_list_blank_spectra_modal_close button is clicked.
    :param is_open: State signal to determine whether the exclusion_list_blank_spectra_modal modal window is open.
    :return: Tuple of the output signal to determine whether the exclusion_list_blank_spectra_modal modal window is
        open, the list of blank spectra IDs to populate the dropdown menu options, the list of blank spectra IDs to
        populate the dropdown menu values, and a blank figure to serve as a placeholder in the modal window body.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'view_exclusion_list_spectra.n_clicks':
        # populate dropdown menu
        dropdown_options = [{'label': i, 'value': i} for i in INDEXED_DATA.keys() if i in BLANK_SPOTS]
        dropdown_value = [i for i in INDEXED_DATA.keys() if i in BLANK_SPOTS]
        return not is_open, dropdown_options, dropdown_value, blank_figure()
    if changed_id == 'exclusion_list_blank_spectra_modal_close.n_clicks':
        return not is_open, [], [], blank_figure()
    return is_open, [], [], blank_figure()


@app.callback([Output('exclusion_list_blank_spectra_figure', 'figure'),
               Output('store_plot', 'data')],
              Input('exclusion_list_blank_spectra_id', 'value'))
def update_blank_spectrum(value):
    """
    Dash callback to plot the spectrum selected from the exclusion_list_blank_spectra_id dropdown using plotly.express
    and plotly_resampler.FigureResampler.

    :param value: Input signal exclusion_list_blank_spectra_id used as the key in INDEXED_DATA.
    :return: Tuple of spectrum figure as a plotly.express.line plot and data store for plotly_resampler.
    """
    global INDEXED_DATA
    fig = get_spectrum(INDEXED_DATA[value])
    cleanup_file_system_backend()
    return fig, Serverside(fig)


@app.callback([Output('exclusion_list', 'data'),
               Output('exclusion_list_csv_error_modal', 'is_open')],
              Input('upload_exclusion_list_from_csv', 'n_clicks'),
              [State('exclusion_list', 'data'),
               State('exclusion_list_csv_error_modal', 'is_open')])
def upload_exclusion_list_from_csv(n_clicks, exclusion_list, exclusion_list_csv_error_modal_is_open):
    """
    Dash callback to load an exclusion list from a single column CSV file containing the single column header 'm/z' and
    populate the exclusion list table.

    :param n_clicks: Input signal if the upload_exclusion_list_from_csv button is clicked.
    :param exclusion_list: State signal to provide the current exclusion list data.
    :param exclusion_list_csv_error_modal_is_open: State signal to determine whether the exclusion_list_csv_error_modal
        modal window is open.
    :return: Tuple of exclusion list data and output signal to determine whether the exclusion_list_csv_error_modal
        modal window is open.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'upload_exclusion_list_from_csv.n_clicks':
        main_tk_window = tkinter.Tk()
        main_tk_window.attributes('-topmost', True, '-alpha', 0)
        filename = askopenfilename(filetypes=[('Comma Separated Value', '*.csv')])
        main_tk_window.destroy()
        exclusion_list_df = pd.read_csv(filename).sort_values(by='m/z')
        if exclusion_list_df.shape[1] == 1 and exclusion_list_df.columns[0] == 'm/z':
            return exclusion_list_df.to_dict('records'), exclusion_list_csv_error_modal_is_open
        else:
            return exclusion_list, True


@app.callback(Output('exclusion_list_csv_error_modal', 'is_open'),
              Input('exclusion_list_csv_error_modal_close', 'n_clicks'),
              State('exclusion_list_csv_error_modal', 'is_open'))
def toggle_exclusion_list_csv_error_modal(n_clicks, is_open):
    """
    Dash callback to toggle the CSV exclusion list upload error message modal window.

    :param n_clicks: Input signal if the exclusion_list_csv_error_modal_close button is clicked.
    :param is_open: State signal to determine whether the exclusion_list_csv_error_modal modal window is open.
    :return: Output signal to determine whether the exclusion_list_csv_error_modal modal window is open.
    """
    if n_clicks:
        return not is_open
    return is_open


@app.callback([Output('exclusion_list', 'data'),
               Output('view_exclusion_list_spectra', 'style')],
              Input('clear_exclusion_list', 'n_clicks'))
def clear_exclusion_list(n_clicks):
    """
    Dash callback to clear the current exclusion list and hide the View Exclusion List Spectra button.

    :param n_clicks: Input signal if the clear_exclusion_list button is clicked.
    :return: Tuple of exclusion list data and style data to hide the view_exclusion_list_spectra button.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'clear_exclusion_list.n_clicks':
        # undo preprocessing
        for key, spectrum in INDEXED_DATA.items():
            spectrum.undo_all_processing()
        return pd.DataFrame(columns=['m/z']).to_dict('records'), {'margin': '20px', 'display': 'none'}


@app.callback(Output('edit_processing_parameters_modal', 'is_open'),
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('edit_processing_parameters_save', 'n_clicks'),
               Input('edit_processing_parameters_cancel', 'n_clicks'),
               Input('trim_spectrum_checkbox', 'value'),
               Input('trim_spectrum_lower_mass_range_value', 'value'),
               Input('trim_spectrum_upper_mass_range_value', 'value'),
               Input('transform_intensity_checkbox', 'value'),
               Input('transform_intensity_method', 'value'),
               Input('smooth_baseline_checkbox', 'value'),
               Input('smooth_baseline_method', 'value'),
               Input('smooth_baseline_window_length_value', 'value'),
               Input('smooth_baseline_polyorder_value', 'value'),
               Input('smooth_baseline_delta_mz_value', 'value'),
               Input('smooth_baseline_diff_thresh_value', 'value'),
               Input('remove_baseline_checkbox', 'value'),
               Input('remove_baseline_method', 'value'),
               Input('remove_baseline_min_half_window_value', 'value'),
               Input('remove_baseline_max_half_window_value', 'value'),
               Input('remove_baseline_decreasing', 'value'),
               Input('remove_baseline_smooth_half_window_value', 'value'),
               Input('remove_baseline_filter_order_value', 'value'),
               Input('remove_baseline_sigma_value', 'value'),
               Input('remove_baseline_increment_value', 'value'),
               Input('remove_baseline_max_hits_value', 'value'),
               Input('remove_baseline_window_tol_value', 'value'),
               Input('remove_baseline_lambda__value', 'value'),
               Input('remove_baseline_porder_value', 'value'),
               Input('remove_baseline_repetition_value', 'value'),
               Input('remove_baseline_degree_value', 'value'),
               Input('remove_baseline_gradient_value', 'value'),
               Input('normalize_intensity_checkbox', 'value'),
               Input('normalize_intensity_method', 'value'),
               Input('bin_spectrum_checkbox', 'value'),
               Input('bin_spectrum_n_bins_value', 'value'),
               Input('bin_spectrum_lower_mass_range_value', 'value'),
               Input('bin_spectrum_upper_mass_range_value', 'value'),
               #Input('align_spectra_checkbox', 'value'),
               #Input('align_spectra_method', 'value'),
               #Input('align_spectra_inter', 'value'),
               #Input('align_spectra_inter_nint_value', 'value'),
               #Input('align_spectra_n', 'value'),
               #Input('align_spectra_n_integer_value', 'value'),
               #Input('align_spectra_coshift_preprocessing', 'value'),
               #Input('align_spectra_coshift_preprocessing_max_shift_value', 'value'),
               #Input('align_spectra_fill_with_previous', 'value'),
               #Input('align_spectra_average2_multiplier_value', 'value'),
               Input('peak_picking_method', 'value'),
               Input('peak_picking_snr_value', 'value'),
               Input('peak_picking_widths_value', 'value'),
               Input('peak_picking_deisotope', 'value'),
               Input('peak_picking_deisotope_fragment_tolerance_value', 'value'),
               Input('peak_picking_deisotope_fragment_unit_ppm', 'value'),
               Input('peak_picking_deisotope_min_charge_value', 'value'),
               Input('peak_picking_deisotope_max_charge_value', 'value'),
               Input('peak_picking_deisotope_keep_only_deisotoped', 'value'),
               Input('peak_picking_deisotope_min_isopeaks_value', 'value'),
               Input('peak_picking_deisotope_max_isopeaks_value', 'value'),
               Input('peak_picking_deisotope_make_single_charged', 'value'),
               Input('peak_picking_deisotope_annotate_charge', 'value'),
               Input('peak_picking_deisotope_annotate_iso_peak_count', 'value'),
               Input('peak_picking_deisotope_use_decreasing_model', 'value'),
               Input('peak_picking_deisotope_start_intensity_check_value', 'value'),
               Input('peak_picking_deisotope_add_up_intensity', 'value'),
               Input('precursor_selection_top_n_value', 'value'),
               Input('precursor_selection_use_exclusion_list', 'value'),
               Input('precursor_selection_exclusion_list_tolerance_value', 'value')],
              State('edit_processing_parameters_modal', 'is_open'))
def toggle_edit_preprocessing_parameters_modal(n_clicks_button,
                                               n_clicks_save,
                                               n_clicks_cancel,
                                               trim_spectrum_checkbox,
                                               trim_spectrum_lower_mass_range,
                                               trim_spectrum_upper_mass_range,
                                               transform_intensity_checkbox,
                                               transform_intensity_method,
                                               smooth_baseline_checkbox,
                                               smooth_baseline_method,
                                               smooth_baseline_window_length,
                                               smooth_baseline_polyorder,
                                               smooth_baseline_delta_mz,
                                               smooth_baseline_diff_thresh,
                                               remove_baseline_checkbox,
                                               remove_baseline_method,
                                               remove_baseline_min_half_window,
                                               remove_baseline_max_half_window,
                                               remove_baseline_decreasing,
                                               remove_baseline_smooth_half_window,
                                               remove_baseline_filter_order,
                                               remove_baseline_sigma,
                                               remove_baseline_increment,
                                               remove_baseline_max_hits,
                                               remove_baseline_window_tol,
                                               remove_baseline_lambda_,
                                               remove_baseline_porder,
                                               remove_baseline_repetition,
                                               remove_baseline_degree,
                                               remove_baseline_gradient,
                                               normalize_intensity_checkbox,
                                               normalize_intensity_method,
                                               bin_spectrum_checkbox,
                                               bin_spectrum_n_bins,
                                               bin_spectrum_lower_mass_range,
                                               bin_spectrum_upper_mass_range,
                                               #align_spectra_checkbox,
                                               #align_spectra_method,
                                               #align_spectra_inter,
                                               #align_spectra_inter_nint_value,
                                               #align_spectra_n,
                                               #align_spectra_n_integer_value,
                                               #align_spectra_coshift_preprocessing,
                                               #align_spectra_coshift_preprocessing_max_shift_value,
                                               #align_spectra_fill_with_previous,
                                               #align_spectra_average2_multiplier_value,
                                               peak_picking_method,
                                               peak_picking_snr,
                                               peak_picking_widths,
                                               peak_picking_deisotope,
                                               peak_picking_fragment_tolerance,
                                               peak_picking_fragment_unit_ppm,
                                               peak_picking_min_charge,
                                               peak_picking_max_charge,
                                               peak_picking_keep_only_deisotoped,
                                               peak_picking_min_isopeaks,
                                               peak_picking_max_isopeaks,
                                               peak_picking_make_single_charged,
                                               peak_picking_annotate_charge,
                                               peak_picking_annotate_iso_peak_count,
                                               peak_picking_use_decreasing_model,
                                               peak_picking_start_intensity_check,
                                               peak_picking_add_up_intensity,
                                               precursor_selection_top_n_value,
                                               precursor_selection_use_exclusion_list,
                                               precursor_selection_exclusion_list_tolerance_value,
                                               is_open):
    """
    Dash callback to toggle the preprocessing parameters modal window, populate the current preprocessing parameters
    saved in the global variable PREPROCESSING_PARAMS, and save any modified preprocessing parameters to
    PREPROCESSING_PARAMS if the Save button is clicked.

    :param n_clicks_button: Input signal if the edit_preprocessing_parameters button is clicked.
    :param n_clicks_save: Input signal if the edit_preprocessing_parameters_save button is clicked.
    :param n_clicks_cancel: Input signal if the edit_preprocessing_parameters_cancel button is clicked.
    :param trim_spectrum_checkbox: Whether to perform spectrum trimming during preprocessing.
    :param trim_spectrum_lower_mass_range: Mass in daltons to use for the lower mass range during spectrum trimming.
    :param trim_spectrum_upper_mass_range: Mass in Daltons to use for the upper mass range during spectrum trimming.
    :param transform_intensity_checkbox: Whether to perform intensity transformation during preprocessing.
    :param transform_intensity_method: Method to use for intensity transformation. Either square root ('sqrt'), natural
        log ('log'), log2 ('log2'), or log10 ('log10') transformation.
    :param smooth_baseline_checkbox: Whether to perform baseline smoothing during preprocessing.
    :param smooth_baseline_method: Method to use for baseline smoothing. Either Savitzky Golay ('SavitzkyGolay'),
        apodization ('apodization'), rebin ('rebin'), fast change ('fast_change'), or median ('median').
    :param smooth_baseline_window_length: The length of the filter window (i.e. number of coefficients).
    :param smooth_baseline_polyorder: The order of the polynomial used to fit the samples. Must be less than
        window_length.
    :param smooth_baseline_delta_mz: New m/z dimension bin width.
    :param smooth_baseline_diff_thresh: Numeric change to remove.
    :param remove_baseline_checkbox: Whether to perform baseline removal during preprocessing.
    :param remove_baseline_method: Method to use for baseline removal. Either statistics-sensitive non-linear iterative
        peak-clipping ('SNIP'), TopHat ('TopHat'), median ('Median'), ZhangFit ('ZhangFit'), modified polynomial
        fit ('ModPoly'), or improved modified polynomial fit ('IModPoly').
    :param remove_baseline_min_half_window: The minimum half window size used for morphological operations.
    :param remove_baseline_max_half_window: The maximum number of iterations/maximum half window size used for
        morphological operations. Should be (w-1)/2 where w is the index-based width of feature or peak.
    :param remove_baseline_decreasing: If False, will iterate through window sizes from 1 to max_half_window. If True,
        will reverse the order and iterate from max_half_window to 1 (gives smoother baseline).
    :param remove_baseline_smooth_half_window: The half window to use for smoothing the data. If greater than 0, will
        perform a moving average smooth on the data for each window to give better results for noisy data.
    :param remove_baseline_filter_order: If the measured data has a more complicated baseline consisting of other
        elements such as Compton edges, thena  higher filter_order should be selected.
    :param remove_baseline_sigma: The standard deviation of the smoothing Gaussian kernal. If None, uses
        (2 * smooth_half_window + 1) / 6.
    :param remove_baseline_increment: The step size for iterating half windows.
    :param remove_baseline_max_hits: The number of consecutive half windows that must produce the same morphological
        opening before accepting the half window as the optimum value.
    :param remove_baseline_window_tol: The tolerance value for considering two morphological openings as equivalent.
    :param remove_baseline_lambda_: Affects smoothness of the resulting background. The larger the lambda, the smoother
        the background.
    :param remove_baseline_porder: Adaptive iteratively reweighted penalized least squares for baseline fitting.
    :param remove_baseline_repetition: How many iterations to run.
    :param remove_baseline_degree: Polynomial degree.
    :param remove_baseline_gradient: Gradient for polynomial loss. Measures incremental gain over each iteration. If
        gain in any iteration is less than this, further improvement will stop.
    :param normalize_intensity_checkbox: Whether to perform intensity normalization during preprocessing.
    :param normalize_intensity_method: Method to use for normalizaton. Either total ion count ('tic'), root mean
        squared ('rms'), median absolute deviation ('mad'), or square root ('sqrt').
    :param bin_spectrum_checkbox: Whether to perform spectrum binning during preprocessing.
    :param bin_spectrum_n_bins: Number of bins to use.
    :param bin_spectrum_lower_mass_range: Mass in daltons to use for the lower mass range during spectrum binning.
    :param bin_spectrum_upper_mass_range: Mass in Daltons to use for the upper mass range during spectrum binning.
    :param peak_picking_method: Method to use for peak picking. Either local maxima ('locmax') or continuous wavelet
        transformation ('cwt').
    :param peak_picking_snr: Minimum signal-to-noise ratio required to consider peak.
    :param peak_picking_widths: Required width of peaks in samples. If using 'cwt' method, used for calculating the CWT
        matrix. Range should cover the expected width of peaks of interest.
    :param peak_picking_deisotope: Whether to perform deisotoping/ion deconvolution. Deisotoping performed using
        pyopenms.Deisotoper.
    :param peak_picking_fragment_tolerance: The tolerance used to match isotopic peaks.
    :param peak_picking_fragment_unit_ppm: Whether ppm or m/z is used as tolerance.
    :param peak_picking_min_charge: The minimum charge considered.
    :param peak_picking_max_charge: The maximum charge considered.
    :param peak_picking_keep_only_deisotoped: If True, only monoisotopic peaks of fragments with isotopic pattern are
        retained.
    :param peak_picking_min_isopeaks: The minimum number of isotopic peaks (at least 2) required for an isotopic
        cluster.
    :param peak_picking_max_isopeaks: The maximum number of isotopic peaks (at least 2) required for an isotopic
        cluster.
    :param peak_picking_make_single_charged: Whether to convert deisotoped monoisotopic peak to single charge.
    :param peak_picking_annotate_charge: Whether to annotate the charge to the peaks in
        pyopenms.MSSpectrum.IntegerDataArray: 'charge'.
    :param peak_picking_annotate_iso_peak_count: Whether to annotate the number of isotopic peaks in a pattern for each
        monoisotopic peak in pyopenms.MSSpectrum.IntegerDataArray: 'iso_peak_count'.
    :param peak_picking_use_decreasing_model: Whether to use a simple averagine model that expects heavier isotopes to
        have less intensity. If False, no intensity checks are applied.
    :param peak_picking_start_intensity_check: Number of the isotopic peak from which the decreasing model should be
        applied. <= 1 will force the monoisotopic peak to be most intense. 2 will allow the monoisotopic peak to be
        less intense than the 2nd peak. 3 will allow the monoisotopic peak and the 2nd peak to be less intense than the
        3rd, etc. A number higher than max_isopeaks will effectively disable use_decreasing_model completely.
    :param peak_picking_add_up_intensity: Whether to sum up the total intensity of each isotopic pattern into the
        intensity of the reported monoisotopic peak.
    :param precursor_selection_top_n_value: Number of desired precursors selected for MS/MS acquisition.
    :param precursor_selection_use_exclusion_list: Whether to use exclusion list during precursor selection.
    :param precursor_selection_exclusion_list_tolerance_value: Tolerance in daltons to use when comparing peak lists to
        the exclusion list during peak picking and precursor selection.
    :param is_open: State signal to determine whether the edit_preprocessing_parameters_modal modal window is open.
    :return: Output signal to determine whether the edit_preprocessing_parameters_modal modal window is open.
    """
    global PREPROCESSING_PARAMS
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if (changed_id == 'edit_preprocessing_parameters.n_clicks' or
            changed_id == 'edit_processing_parameters_save.n_clicks' or
            changed_id == 'edit_processing_parameters_cancel.n_clicks'):
        if changed_id == 'edit_processing_parameters_save.n_clicks':
            PREPROCESSING_PARAMS['TRIM_SPECTRUM']['run'] = trim_spectrum_checkbox
            PREPROCESSING_PARAMS['TRIM_SPECTRUM']['lower_mass_range'] = trim_spectrum_lower_mass_range
            PREPROCESSING_PARAMS['TRIM_SPECTRUM']['upper_mass_range'] = trim_spectrum_upper_mass_range
            PREPROCESSING_PARAMS['TRANSFORM_INTENSITY']['run'] = transform_intensity_checkbox
            PREPROCESSING_PARAMS['TRANSFORM_INTENSITY']['method'] = transform_intensity_method
            PREPROCESSING_PARAMS['SMOOTH_BASELINE']['run'] = smooth_baseline_checkbox
            PREPROCESSING_PARAMS['SMOOTH_BASELINE']['method'] = smooth_baseline_method
            PREPROCESSING_PARAMS['SMOOTH_BASELINE']['window_length'] = smooth_baseline_window_length
            PREPROCESSING_PARAMS['SMOOTH_BASELINE']['polyorder'] = smooth_baseline_polyorder
            PREPROCESSING_PARAMS['SMOOTH_BASELINE']['delta_mz'] = smooth_baseline_delta_mz
            PREPROCESSING_PARAMS['SMOOTH_BASELINE']['diff_thresh'] = smooth_baseline_diff_thresh
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['run'] = remove_baseline_checkbox
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['method'] = remove_baseline_method
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['min_half_window'] = remove_baseline_min_half_window
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['max_half_window'] = remove_baseline_max_half_window
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['decreasing'] = remove_baseline_decreasing
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['smooth_half_window'] = remove_baseline_smooth_half_window
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['filter_order'] = remove_baseline_filter_order
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['sigma'] = remove_baseline_sigma
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['increment'] = remove_baseline_increment
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['max_hits'] = remove_baseline_max_hits
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['window_tol'] = remove_baseline_window_tol
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['lambda_'] = remove_baseline_lambda_
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['porder'] = remove_baseline_porder
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['repetition'] = remove_baseline_repetition
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['degree'] = remove_baseline_degree
            PREPROCESSING_PARAMS['REMOVE_BASELINE']['gradient'] = remove_baseline_gradient
            PREPROCESSING_PARAMS['NORMALIZE_INTENSITY']['run'] = normalize_intensity_checkbox
            PREPROCESSING_PARAMS['NORMALIZE_INTENSITY']['method'] = normalize_intensity_method
            PREPROCESSING_PARAMS['BIN_SPECTRUM']['run'] = bin_spectrum_checkbox
            PREPROCESSING_PARAMS['BIN_SPECTRUM']['n_bins'] = bin_spectrum_n_bins
            PREPROCESSING_PARAMS['BIN_SPECTRUM']['lower_mass_range'] = bin_spectrum_lower_mass_range
            PREPROCESSING_PARAMS['BIN_SPECTRUM']['upper_mass_range'] = bin_spectrum_upper_mass_range
            """PREPROCESSING_PARAMS['ALIGN_SPECTRA']['run'] = align_spectra_checkbox
            PREPROCESSING_PARAMS['ALIGN_SPECTRA']['method'] = align_spectra_method
            if align_spectra_inter == 'whole' or align_spectra_inter == 'ndata':
                PREPROCESSING_PARAMS['ALIGN_SPECTRA']['inter'] = align_spectra_inter
            elif align_spectra_inter == 'nint':
                PREPROCESSING_PARAMS['ALIGN_SPECTRA']['inter'] = align_spectra_inter_nint_value
            if align_spectra_n == 'f' or align_spectra_n == 'b':
                PREPROCESSING_PARAMS['ALIGN_SPECTRA']['n'] = align_spectra_n
            elif align_spectra_n == 'integer':
                PREPROCESSING_PARAMS['ALIGN_SPECTRA']['n'] = align_spectra_n_integer_value
            PREPROCESSING_PARAMS['ALIGN_SPECTRA']['coshift_preprocessing'] = align_spectra_coshift_preprocessing
            PREPROCESSING_PARAMS['ALIGN_SPECTRA'][
                'coshift_preprocessing_max_shift'] = align_spectra_coshift_preprocessing_max_shift_value
            PREPROCESSING_PARAMS['ALIGN_SPECTRA']['fill_with_previous'] = align_spectra_fill_with_previous
            PREPROCESSING_PARAMS['ALIGN_SPECTRA']['average2_multiplier'] = align_spectra_average2_multiplier_value"""
            PREPROCESSING_PARAMS['PEAK_PICKING']['method'] = peak_picking_method
            PREPROCESSING_PARAMS['PEAK_PICKING']['snr'] = peak_picking_snr
            PREPROCESSING_PARAMS['PEAK_PICKING']['widths'] = peak_picking_widths
            PREPROCESSING_PARAMS['PEAK_PICKING']['deisotope'] = peak_picking_deisotope
            PREPROCESSING_PARAMS['PEAK_PICKING']['fragment_tolerance'] = peak_picking_fragment_tolerance
            PREPROCESSING_PARAMS['PEAK_PICKING']['fragment_unit_ppm'] = peak_picking_fragment_unit_ppm
            PREPROCESSING_PARAMS['PEAK_PICKING']['min_charge'] = peak_picking_min_charge
            PREPROCESSING_PARAMS['PEAK_PICKING']['max_charge'] = peak_picking_max_charge
            PREPROCESSING_PARAMS['PEAK_PICKING']['keep_only_deisotoped'] = peak_picking_keep_only_deisotoped
            PREPROCESSING_PARAMS['PEAK_PICKING']['min_isopeaks'] = peak_picking_min_isopeaks
            PREPROCESSING_PARAMS['PEAK_PICKING']['max_isopeaks'] = peak_picking_max_isopeaks
            PREPROCESSING_PARAMS['PEAK_PICKING']['make_single_charged'] = peak_picking_make_single_charged
            PREPROCESSING_PARAMS['PEAK_PICKING']['annotate_charge'] = peak_picking_annotate_charge
            PREPROCESSING_PARAMS['PEAK_PICKING']['annotate_iso_peak_count'] = peak_picking_annotate_iso_peak_count
            PREPROCESSING_PARAMS['PEAK_PICKING']['use_decreasing_model'] = peak_picking_use_decreasing_model
            PREPROCESSING_PARAMS['PEAK_PICKING']['start_intensity_check'] = peak_picking_start_intensity_check
            PREPROCESSING_PARAMS['PEAK_PICKING']['add_up_intensity'] = peak_picking_add_up_intensity
            PREPROCESSING_PARAMS['PRECURSOR_SELECTION']['top_n'] = precursor_selection_top_n_value
            PREPROCESSING_PARAMS['PRECURSOR_SELECTION']['use_exclusion_list'] = precursor_selection_use_exclusion_list
            PREPROCESSING_PARAMS['PRECURSOR_SELECTION']['exclusion_list_tolerance'] = precursor_selection_exclusion_list_tolerance_value
        return not is_open
    return is_open


@app.callback(Output('edit_processing_parameters_modal_saved', 'is_open'),
              [Input('edit_processing_parameters_save', 'n_clicks'),
               Input('edit_processing_parameters_modal_saved_close', 'n_clicks')],
              State('edit_processing_parameters_modal_saved', 'is_open'))
def toggle_edit_processing_parameters_saved_modal(n_clicks_save, n_clicks_close, is_open):
    """
    Dash callback to toggle the preprocessing parameters save confirmation message modal window.

    :param n_clicks_save: Input signal if the edit_preprocessing_parameters_save button is clicked.
    :param n_clicks_close: Input signal if the edit_preprocessing_parameters_close button is clicked.
    :param is_open: State signal to determine whether the edit_preprocessing_parameters_modal_saved modal window is
        open.
    :return: Output signal to determine whether the edit_preprocessing_parameters_modal_saved modal window is open.
    """
    if n_clicks_save or n_clicks_close:
        return not is_open
    return is_open


@app.callback([Output('trim_spectrum_lower_mass_range', 'style'),
               Output('trim_spectrum_upper_mass_range', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('trim_spectrum_checkbox', 'value')])
def toggle_trim_spectrum_parameters(n_clicks, value):
    """
    Dash callback to toggle whether spectrum trimming parameters are visible depending on whether spectrum trimming is
    enabled or disabled in the preprocessing parameters modal window.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param value: Input signal to determine whether spectrum trimming is enabled or disabled.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if value:
        return [copy.deepcopy(SHOWN),
                copy.deepcopy(SHOWN)]
    elif not value:
        return [copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN)]


@app.callback([Output('transform_intensity_method_label', 'style'),
               Output('transform_intensity_method', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('transform_intensity_checkbox', 'value')])
def toggle_transform_intensity_parameters(n_clicks, value):
    """
    Dash callback to toggle whether intensity transformation parameters are visible depending on whether intensity
    transformation is enabled or disabled in the preprocessing parameters modal window.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param value: Input signal to determine whether intensity transformation is enabled or disabled.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if value:
        return [copy.deepcopy(SHOWN),
                copy.deepcopy(SHOWN)]
    elif not value:
        return [copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN)]


@app.callback([Output('smooth_baseline_method_label', 'style'),
               Output('smooth_baseline_method', 'style'),
               Output('smooth_baseline_window_length', 'style'),
               Output('smooth_baseline_polyorder', 'style'),
               Output('smooth_baseline_delta_mz', 'style'),
               Output('smooth_baseline_diff_thresh', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('smooth_baseline_checkbox', 'value'),
               Input('smooth_baseline_method', 'value')])
def toggle_smooth_baseline_method_parameters(n_clicks, smooth_baseline_checkbox, smooth_baseline_method):
    """
    Dash callback to toggle whether baseline smoothing parameters are visible depending on whether baseline smoothing
    is enabled or disabled in the preprocessing parameters modal window. Also toggles which baseline smoothing
    parameters are visible depending on the baseline smoothing method selected in the preprocessing parameters modal
    window.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param smooth_baseline_checkbox: Input signal to determine whether baseline smoothing is enabled or disabled.
    :param smooth_baseline_method: Input signal to obtain the currently selected baseline smoothing method.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if smooth_baseline_checkbox:
        if smooth_baseline_method == 'SavitzkyGolay':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_savitzky_golay_style()
        elif smooth_baseline_method == 'apodization':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_apodization_style()
        elif smooth_baseline_method == 'rebin':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_rebin_style()
        elif smooth_baseline_method == 'fast_change':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_fast_change_style()
        elif smooth_baseline_method == 'median':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_smoothing_median_style()
    elif not smooth_baseline_checkbox:
        return [copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN)]


@app.callback([Output('remove_baseline_method_label', 'style'),
               Output('remove_baseline_method', 'style'),
               Output('remove_baseline_min_half_window', 'style'),
               Output('remove_baseline_max_half_window', 'style'),
               Output('remove_baseline_decreasing', 'style'),
               Output('remove_baseline_smooth_half_window', 'style'),
               Output('remove_baseline_filter_order', 'style'),
               Output('remove_baseline_sigma', 'style'),
               Output('remove_baseline_increment', 'style'),
               Output('remove_baseline_max_hits', 'style'),
               Output('remove_baseline_window_tol', 'style'),
               Output('remove_baseline_lambda_', 'style'),
               Output('remove_baseline_porder', 'style'),
               Output('remove_baseline_repetition', 'style'),
               Output('remove_baseline_degree', 'style'),
               Output('remove_baseline_gradient', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('remove_baseline_checkbox', 'value'),
               Input('remove_baseline_method', 'value')])
def toggle_remove_baseline_method_parameters(n_clicks, remove_baseline_checkbox, remove_baseline_method):
    """
    Dash callback to toggle whether baseline removal parameters are visible depending on whether baseline removal
    is enabled or disabled in the preprocessing parameters modal window. Also toggles which baseline removal
    parameters are visible depending on the baseline removal method selected in the preprocessing parameters modal
    window.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param remove_baseline_checkbox: Input signal to determine whether baseline removal is enabled or disabled.
    :param remove_baseline_method: Input signal to obtain the currently selected baseline removal method.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if remove_baseline_checkbox:
        if remove_baseline_method == 'SNIP':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_snip_style()
        elif remove_baseline_method == 'TopHat':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_tophat_style()
        elif remove_baseline_method == 'Median':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_removal_median_style()
        elif remove_baseline_method == 'ZhangFit':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_zhangfit_style()
        elif remove_baseline_method == 'ModPoly':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_modpoly_style()
        elif remove_baseline_method == 'IModPoly':
            return [copy.deepcopy(SHOWN), copy.deepcopy(SHOWN)] + toggle_imodpoly_style()
    elif not remove_baseline_checkbox:
        return [copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN)]


@app.callback([Output('normalize_intensity_method_label', 'style'),
               Output('normalize_intensity_method', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('normalize_intensity_checkbox', 'value')])
def toggle_normalize_intensity_parameters(n_clicks, value):
    """
    Dash callback to toggle whether intensity normalization parameters are visible depending on whether intensity
    normalization is enabled or disabled in the preprocessing parameters modal window.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param value: Input signal to determine whether intensity normalization is enabled or disabled.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if value:
        return [copy.deepcopy(SHOWN),
                copy.deepcopy(SHOWN)]
    elif not value:
        return [copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN)]


@app.callback([Output('bin_spectrum_n_bins', 'style'),
               Output('bin_spectrum_lower_mass_range', 'style'),
               Output('bin_spectrum_upper_mass_range', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('bin_spectrum_checkbox', 'value')])
def toggle_bin_spectrum_parameters(n_clicks, value):
    """
    Dash callback to toggle whether spectrum binning parameters are visible depending on whether spectrum binning is
    enabled or disabled in the preprocessing parameters modal window.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param value: Input signal to determine whether spectrum binning is enabled or disabled.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if value:
        return [copy.deepcopy(SHOWN),
                copy.deepcopy(SHOWN),
                copy.deepcopy(SHOWN)]
    elif not value:
        return [copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN),
                copy.deepcopy(HIDDEN)]


"""@app.callback([Output('align_spectra_method_label', 'style'),
               Output('align_spectra_method', 'style'),
               Output('align_spectra_inter_label', 'style'),
               Output('align_spectra_inter', 'style'),
               Output('align_spectra_inter_nint', 'style'),
               Output('align_spectra_n_label', 'style'),
               Output('align_spectra_n', 'style'),
               Output('align_spectra_n_integer', 'style'),
               Output('align_spectra_coshift_preprocessing', 'style'),
               Output('align_spectra_coshift_preprocessing_max_shift', 'style'),
               Output('align_spectra_fill_with_previous', 'style'),
               Output('align_spectra_average2_multiplier', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('align_spectra_checkbox', 'value'),
               Input('align_spectra_method', 'value'),
               Input('align_spectra_inter', 'value'),
               Input('align_spectra_n', 'value')])
def toggle_align_spectra_parameters(n_clicks, align_spectra_checkbox, align_spectra_method, align_spectra_inter,
                                    align_spectra_n):
    default_hidden = [copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN),
                      copy.deepcopy(HIDDEN)]
    default_shown = [copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN),
                     copy.deepcopy(SHOWN)]
    if align_spectra_checkbox:
        if align_spectra_method == 'average' or align_spectra_method == 'median' or align_spectra_method == 'max':
            default_shown[11] = HIDDEN
        if align_spectra_inter == 'whole' or align_spectra_inter == 'ndata':
            default_shown[4] = HIDDEN
        if align_spectra_n == 'f' or align_spectra_n == 'b':
            default_shown[7] = HIDDEN
        return default_shown
    elif not align_spectra_checkbox:
        return default_hidden"""


@app.callback([Output('peak_picking_snr', 'style'),
               Output('peak_picking_widths', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('peak_picking_method', 'value')])
def toggle_peak_picking_method_parameters(n_clicks, value):
    """
    Dash callback to toggle which peak picking parameters are visible depending on the peak picking method selected in
    the preprocessing parameters modal window.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param value: Input signal to obtain the currently selected peak picking method.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if value == 'locmax':
        return toggle_locmax_style()
    elif value == 'cwt':
        return toggle_cwt_style()


@app.callback([Output('peak_picking_deisotope_fragment_tolerance', 'style'),
               Output('peak_picking_deisotope_fragment_unit_ppm_label', 'style'),
               Output('peak_picking_deisotope_fragment_unit_ppm', 'style'),
               Output('peak_picking_deisotope_min_charge', 'style'),
               Output('peak_picking_deisotope_max_charge', 'style'),
               Output('peak_picking_deisotope_keep_only_deisotoped', 'style'),
               Output('peak_picking_deisotope_min_isopeaks', 'style'),
               Output('peak_picking_deisotope_max_isopeaks', 'style'),
               Output('peak_picking_deisotope_make_single_charged', 'style'),
               Output('peak_picking_deisotope_annotate_charge', 'style'),
               Output('peak_picking_deisotope_annotate_iso_peak_count', 'style'),
               Output('peak_picking_deisotope_use_decreasing_model', 'style'),
               Output('peak_picking_deisotope_start_intensity_check', 'style'),
               Output('peak_picking_deisotope_add_up_intensity', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('peak_picking_deisotope', 'value')])
def toggle_peak_picking_deisotope_parameters(n_clicks, value):
    """
    Dash callback to toggle whether deisotoping parameters are visible.

    :param n_clicks: Input signal if the edit_preprocessing_parameters button is clicked.
    :param value: Input signal to obtain the current status of whether deisotoping is enabled or disabled.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if value:
        return toggle_deisotope_on_style()
    elif not value:
        return toggle_deisotope_off_style()


@app.callback([Output('preview_precursor_list_modal', 'is_open'),
               Output('preview_id', 'options'),
               Output('preview_id', 'value'),
               Output('preview_figure', 'figure')],
              [Input('preview_precursor_list', 'n_clicks'),
               Input('preview_precursor_list_modal_back', 'n_clicks'),
               Input('preview_precursor_list_modal_run', 'n_clicks')],
              [State('preview_precursor_list_modal', 'is_open'),
               State('exclusion_list', 'data')])
def preview_precursor_list(n_clicks_preview,
                           n_clicks_modal_back,
                           n_clicks_modal_run,
                           is_open,
                           exclusion_list):
    """
    Dash callback to preprocess sample spectra based on current preprocessing parameters and view the spectra in a
    modal window. In the modal window, going Back will reset and undo all preprocessing, while continuing to generate
    the MS/MS AutoXecute sequences closes the preview_precursor_list_modal modal window.

    :param n_clicks_preview: Input signal if the preview_precursor_list button is clicked.
    :param n_clicks_modal_back: Input signal if the preview_precursor_list_modal_back button is clicked.
    :param n_clicks_modal_run: Input signal if the preview_precursor_list_modal_run button is clicked.
    :param is_open: State signal to determine whether the preview_precursor_list_modal modal window is open
    :param exclusion_list: State signal to provide the current exclusion list data.
    :return: Tuple of output signal to determine whether the preview_precursor_list_modal modal window is open, the
        list of spectra IDs to populate the dropdown menu options, the list of spectra IDs to populate the dropdown
        menu values, and a blank figure to serve as a placeholder in the modal window body.
    """
    global INDEXED_DATA
    global SPOT_GROUPS
    global PREPROCESSING_PARAMS
    global BLANK_SPOTS
    global SAMPLE_PARAMS_LOG
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'preview_precursor_list.n_clicks':
        params = copy.deepcopy(PREPROCESSING_PARAMS)
        SAMPLE_PARAMS_LOG = copy.deepcopy(PREPROCESSING_PARAMS)
        # preprocessing
        if params['TRIM_SPECTRUM']['run']:
            del params['TRIM_SPECTRUM']['run']
            for key, spectrum in INDEXED_DATA.items():
                spectrum.trim_spectrum(**params['TRIM_SPECTRUM'])
        if params['TRANSFORM_INTENSITY']['run']:
            del params['TRANSFORM_INTENSITY']['run']
            for key, spectrum in INDEXED_DATA.items():
                spectrum.transform_intensity(**params['TRANSFORM_INTENSITY'])
        if params['SMOOTH_BASELINE']['run']:
            del params['SMOOTH_BASELINE']['run']
            for key, spectrum in INDEXED_DATA.items():
                spectrum.smooth_baseline(**params['SMOOTH_BASELINE'])
        if params['REMOVE_BASELINE']['run']:
            del params['REMOVE_BASELINE']['run']
            for key, spectrum in INDEXED_DATA.items():
                spectrum.remove_baseline(**params['REMOVE_BASELINE'])
        if params['NORMALIZE_INTENSITY']['run']:
            del params['NORMALIZE_INTENSITY']['run']
            for key, spectrum in INDEXED_DATA.items():
                spectrum.normalize_intensity(**params['NORMALIZE_INTENSITY'])
        if params['BIN_SPECTRUM']['run']:
            del params['BIN_SPECTRUM']['run']
            for key, spectrum in INDEXED_DATA.items():
                spectrum.bin_spectrum(**params['BIN_SPECTRUM'])
        # peak picking
        for key, spectrum in INDEXED_DATA.items():
            spectrum.peak_picking(**params['PEAK_PICKING'])
        # groups have been defined
        if len(SPOT_GROUPS.keys()) > 0:
            # process groups
            spots_in_group = [i for value in SPOT_GROUPS.values() for i in value]
            for group, list_of_spots in SPOT_GROUPS.items():
                group_spectra = [INDEXED_DATA[spot] for spot in list_of_spots]
                group_feature_matrix = get_feature_matrix(group_spectra, missing_value_imputation=False)
                group_feature_matrix.to_csv('C:\\Users\\bass\\data\\group_feature_matrix.csv')
                group_consensus_df = pd.DataFrame(data={'m/z': np.unique(group_feature_matrix['mz'].values),
                                                        'Intensity': group_feature_matrix.loc[:, group_feature_matrix.columns != 'mz'].mean(axis=1)})
                # remove peaks found in exclusion list
                if params['PRECURSOR_SELECTION']['use_exclusion_list']:
                    exclusion_list = pd.DataFrame(exclusion_list)
                    if not exclusion_list.empty:
                        merged_df = pd.merge_asof(group_consensus_df,
                                                  exclusion_list.rename(columns={'m/z': 'exclusion_list'}),
                                                  left_on='m/z',
                                                  right_on='exclusion_list',
                                                  tolerance=params['PRECURSOR_SELECTION']['exclusion_list_tolerance'],
                                                  direction='nearest')
                        group_consensus_df = merged_df.drop(merged_df.dropna().index)
                group_consensus_df = group_consensus_df.sort_values(by='Intensity', ascending=False).reset_index(drop=True)[:params['PRECURSOR_SELECTION']['top_n']]
                group_consensus_df = group_consensus_df.sort_values(by='Intensity', ascending=True).reset_index(drop=True)
                feature_dict = {}
                for index, row in group_consensus_df.iterrows():
                    single_feature_df = pd.DataFrame({'m/z': [row['m/z']]})
                    single_feature_merged_df = []
                    for group_spectrum in group_spectra:
                        group_spectrum_df = pd.DataFrame(data={'m/z': group_spectrum.peak_picked_mz_array,
                                                               'Intensity': group_spectrum.peak_picked_intensity_array,
                                                               'Indices': group_spectrum.peak_picking_indices,
                                                               'Spot': group_spectrum.coord})
                        single_feature_merged_df.append(pd.merge_asof(single_feature_df,
                                                                      group_spectrum_df,
                                                                      tolerance=params['PRECURSOR_SELECTION']['exclusion_list_tolerance'],
                                                                      direction='nearest').sort_values(by='Intensity', ascending=False).reset_index(drop=True))
                    single_feature_merged_df = pd.concat(single_feature_merged_df, ignore_index=True).sort_values(by='Intensity', ascending=False).reset_index(drop=True)
                    mz = single_feature_merged_df.values.tolist()[0][0]
                    intensity = single_feature_merged_df.values.tolist()[0][1]
                    array_index = single_feature_merged_df.values.tolist()[0][2]
                    spot = single_feature_merged_df.values.tolist()[0][3]
                    if spot not in feature_dict.keys():
                        feature_dict[spot] = {}
                        feature_dict[spot]['mz'] = [mz]
                        feature_dict[spot]['intensity'] = [intensity]
                        feature_dict[spot]['index'] = [int(array_index)]
                    elif spot in feature_dict.keys():
                        feature_dict[spot]['mz'].append(mz)
                        feature_dict[spot]['intensity'].append(intensity)
                        feature_dict[spot]['index'].append(int(array_index))
                for spot in list_of_spots:
                    INDEXED_DATA[spot].peak_picked_mz_array = None
                    INDEXED_DATA[spot].peak_picked_intensity_array = None
                    INDEXED_DATA[spot].peak_picking_indices = None
                for spot, values in feature_dict.items():
                    INDEXED_DATA[spot].peak_picked_mz_array = np.array(values['mz'])
                    INDEXED_DATA[spot].peak_picked_intensity_array = np.array(values['intensity'])
                    INDEXED_DATA[spot].peak_picking_indices = np.array(values['index'])
            # process all other spots not found in a group
            # remove peaks found in exclusion list
            if params['PRECURSOR_SELECTION']['use_exclusion_list']:
                exclusion_list = pd.DataFrame(exclusion_list)
                if not exclusion_list.empty:
                    for key, spectrum in INDEXED_DATA.items():
                        if key not in spots_in_group:
                            spectrum_df = pd.DataFrame(data={'m/z': spectrum.peak_picked_mz_array,
                                                             'Intensity': spectrum.peak_picked_intensity_array,
                                                             'Indices': spectrum.peak_picking_indices})
                            merged_df = pd.merge_asof(spectrum_df,
                                                      exclusion_list.rename(columns={'m/z': 'exclusion_list'}),
                                                      left_on='m/z',
                                                      right_on='exclusion_list',
                                                      tolerance=params['PRECURSOR_SELECTION'][
                                                          'exclusion_list_tolerance'],
                                                      direction='nearest')
                            merged_df = merged_df.drop(merged_df.dropna().index)
                            spectrum.peak_picked_mz_array = merged_df['m/z'].values
                            spectrum.peak_picked_intensity_array = merged_df['Intensity'].values
                            spectrum.peak_picking_indices = merged_df['Indices'].values
            # subset peak picked peaks to only include top n peaks
            for key, spectrum in INDEXED_DATA.items():
                if key not in spots_in_group:
                    top_n_indices = np.argsort(spectrum.peak_picked_intensity_array)[::-1][:params['PRECURSOR_SELECTION']['top_n']]
                    spectrum.peak_picked_mz_array = spectrum.peak_picked_mz_array[top_n_indices]
                    spectrum.peak_picked_intensity_array = spectrum.peak_picked_intensity_array[top_n_indices]
                    spectrum.peak_picking_indices = spectrum.peak_picking_indices[top_n_indices]
        # no groups defined
        else:
            # remove peaks found in exclusion list
            if params['PRECURSOR_SELECTION']['use_exclusion_list']:
                exclusion_list = pd.DataFrame(exclusion_list)
                if not exclusion_list.empty:
                    for key, spectrum in INDEXED_DATA.items():
                        spectrum_df = pd.DataFrame(data={'m/z': spectrum.peak_picked_mz_array,
                                                         'Intensity': spectrum.peak_picked_intensity_array,
                                                         'Indices': spectrum.peak_picking_indices})
                        merged_df = pd.merge_asof(spectrum_df,
                                                  exclusion_list.rename(columns={'m/z': 'exclusion_list'}),
                                                  left_on='m/z',
                                                  right_on='exclusion_list',
                                                  tolerance=params['PRECURSOR_SELECTION']['exclusion_list_tolerance'],
                                                  direction='nearest')
                        merged_df = merged_df.drop(merged_df.dropna().index)
                        spectrum.peak_picked_mz_array = merged_df['m/z'].values
                        spectrum.peak_picked_intensity_array = merged_df['Intensity'].values
                        spectrum.peak_picking_indices = merged_df['Indices'].values
            # subset peak picked peaks to only include top n peaks
            for key, spectrum in INDEXED_DATA.items():
                top_n_indices = np.argsort(spectrum.peak_picked_intensity_array)[::-1][:params['PRECURSOR_SELECTION']['top_n']]
                spectrum.peak_picked_mz_array = spectrum.peak_picked_mz_array[top_n_indices]
                spectrum.peak_picked_intensity_array = spectrum.peak_picked_intensity_array[top_n_indices]
                spectrum.peak_picking_indices = spectrum.peak_picking_indices[top_n_indices]
        # populate dropdown menu
        dropdown_options = [{'label': i, 'value': i} for i in INDEXED_DATA.keys() if i not in BLANK_SPOTS]
        dropdown_value = [i for i in INDEXED_DATA.keys() if i not in BLANK_SPOTS]
        return not is_open, dropdown_options, dropdown_value, blank_figure()
    if changed_id == 'preview_precursor_list_modal_back.n_clicks':
        for key, spectrum in INDEXED_DATA.items():
            spectrum.undo_all_processing()
        return not is_open, [], [], blank_figure()
    if changed_id == 'preview_precursor_list_modal_run.n_clicks':
        return not is_open, [], [], blank_figure()
    return is_open, [], [], blank_figure()


@app.callback([Output('preview_figure', 'figure'),
               Output('store_plot', 'data')],
              Input('preview_id', 'value'))
def update_preview_spectrum(value):
    """
    Dash callback to plot the spectrum selected from the preview_id dropdown using plotly.express and
    plotly_resampler.FigureResampler.

    :param value: Input signal preview_id used as the key in INDEXED_DATA.
    :return: Tuple of spectrum figure as a plotly.express.line plot and data store for plotly_resampler.
    """
    global INDEXED_DATA
    if INDEXED_DATA[value].peak_picking_indices is None:
        label_peaks = False
    else:
        label_peaks = True
    fig = get_spectrum(INDEXED_DATA[value], label_peaks)
    cleanup_file_system_backend()
    return fig, Serverside(fig)


@app.callback([Output('run_modal', 'is_open'),
               Output('run_success_modal', 'is_open')],
              [Input('preview_precursor_list_modal_run', 'n_clicks'),
               Input('run_button', 'n_clicks')],
              [State('run_modal', 'is_open'),
               State('run_success_modal', 'is_open'),
               State('run_output_directory_value', 'value'),
               State('run_method_value', 'value'),
               State('run_method_checkbox', 'value'),
               State('exclusion_list', 'data')])
def toggle_run_modal(preview_run_n_clicks, run_n_clicks, run_is_open, success_is_open, outdir, method, method_checkbox,
                     exclusion_list):
    """
    Dash callback to toggle the run_modal modal window and create the new MS/MS AutoXecute sequence. A new modal window
    displaying a success message and the output directory of the resulting AutoXecute sequence will be shown upon
    success.

    :param preview_run_n_clicks: Input signal if the preview_precursor_list_modal_run button is clicked.
    :param run_n_clicks: Input signal if the run_button button is clicked.
    :param run_is_open: State signal to determine whether the run_modal modal window is open.
    :param success_is_open: State signal to determine whether the run_success_modal modal window is open.
    :param outdir: Path to folder in which to write the output AutoXecute sequence. Will also be used as the directory
        for the resulting AutoXecute data.
    :param method: Path to the new Bruker .m directory to be used in the AutoXecute sequence.
    :param method_checkbox: Whether to use user specified Bruker .m directory method file or to use the original
        methods in the new AutoXecute sequence.
    :param exclusion_list: State signal to provide the current exclusion list data.
    :return: Tuple of output signal to determine whether the run_modal modal window is open and output signal to
        determine whether the run_modal_success modal window is open.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'preview_precursor_list_modal_run.n_clicks':
        return not run_is_open, success_is_open
    if changed_id == 'run_button.n_clicks':
        global MS1_AUTOX
        global AUTOX_PATH_DICT
        global INDEXED_DATA
        global BLANK_SPOTS
        global AUTOX_SEQ
        global BLANK_PARAMS_LOG
        global SAMPLE_PARAMS_LOG
        log = 'fleX MS/MS AutoXecute Generator Log\n\n'
        log += f'Output Directory: {outdir}\n\n'
        new_autox = et.Element(MS1_AUTOX.tag, attrib=MS1_AUTOX.attrib)
        new_autox.attrib['directory'] = outdir
        for spot_group in MS1_AUTOX:
            log += f"Spot Group: {spot_group.attrib['sampleName']}\n"
            for cont in spot_group:
                if cont.attrib['Pos_on_Scout'] not in BLANK_SPOTS and \
                        INDEXED_DATA[cont.attrib['Pos_on_Scout']].peak_picked_mz_array is not None and \
                        INDEXED_DATA[cont.attrib['Pos_on_Scout']].peak_picked_intensity_array is not None:
                    new_spot_group = et.SubElement(new_autox, spot_group.tag, attrib=spot_group.attrib)
                    new_spot_group.attrib['sampleName'] = f"{new_spot_group.attrib['sampleName']}_{cont.attrib['Pos_on_Scout']}_MSMS"
                    if method_checkbox and os.path.exists(method):
                        new_spot_group.attrib['acqMethod'] = method
                        log += f"{spot_group.attrib['sampleName']} Method: {method}\n"
                    else:
                        new_spot_group.attrib['acqMethod'] = [value['method_path']
                                                              for key, value in AUTOX_PATH_DICT.items()
                                                              if value['sample_name'] == spot_group.attrib['sampleName']][0]
                        log += (f"{spot_group.attrib['sampleName']} Method: " +
                                [value['method_path']
                                 for key, value in AUTOX_PATH_DICT.items()
                                 if value['sample_name'] == spot_group.attrib['sampleName']][0] + '\n')
                    top_n_peaks = pd.DataFrame({'m/z': INDEXED_DATA[cont.attrib['Pos_on_Scout']].peak_picked_mz_array,
                                                'Intensity': INDEXED_DATA[cont.attrib['Pos_on_Scout']].peak_picked_intensity_array})
                    top_n_peaks = top_n_peaks.sort_values(by='Intensity', ascending=False).round(4)
                    top_n_peaks = top_n_peaks.drop_duplicates(subset='m/z')
                    top_n_peaks = top_n_peaks['m/z'].values.tolist()
                    for peak in top_n_peaks:
                        new_cont = et.SubElement(new_spot_group, cont.tag, attrib=cont.attrib)
                        new_cont.attrib['acqJobMode'] = 'MSMS'
                        new_cont.attrib['precursor_m_z'] = str(peak)
        new_autox_tree = et.ElementTree(new_autox)
        new_autox_tree.write(os.path.join(outdir, os.path.splitext(os.path.split(AUTOX_SEQ)[-1])[0]) + '_MALDI_DDA.run',
                             encoding='utf-8',
                             xml_declaration=True,
                             pretty_print=True)
        log += '\nSample Processing Parameters Used for Precursor Selection\n\n'
        log += toml.dumps(SAMPLE_PARAMS_LOG) + '\n\n'
        if 'PRECURSOR_SELECTION' in SAMPLE_PARAMS_LOG.keys():
            if SAMPLE_PARAMS_LOG['PRECURSOR_SELECTION']['use_exclusion_list']:
                log += 'Blank Processing Parameters Used for Exclusion List Generation\n\n'
                log += toml.dumps(BLANK_PARAMS_LOG) + '\n\n'
                log += 'Exclusion List\n\n'
                log += pd.DataFrame(exclusion_list).to_string(index=False) + '\n'
        with open(os.path.join(outdir,
                               os.path.splitext(os.path.split(AUTOX_SEQ)[-1])[0]) + '_MALDI_DDA.log', 'w') as logfile:
            logfile.write(log)
        return not run_is_open, not success_is_open
    return run_is_open, success_is_open


@app.callback(Output('run_success_modal', 'is_open'),
              Input('run_success_close', 'n_clicks'),
              State('run_success_modal', 'is_open'))
def toggle_run_success_modal(n_clicks, is_open):
    """
    Dash callback to toggle the run success message modal window.

    :param n_clicks: Input signal if the run_success_close button is clicked.
    :param is_open: State signal to determine whether the run_success_modal modal window is open.
    :return: Output signal to determine whether the run_success_modal modal window is open.
    """
    if n_clicks:
        return not is_open
    return is_open


@app.callback(Output('run_method', 'style'),
              [Input('preview_precursor_list_modal_run', 'n_clicks'),
               Input('run_method_checkbox', 'value')])
def toggle_run_new_method_selection_input(n_clicks, value):
    """
    Dash callback to toggle whether the method input group is visible depending on whether using a new method for the
    new AutoXecute sequence is enabled or disabled.

    :param n_clicks: Input signal if the preview_precursor_list_modal_run button is clicked.
    :param value: Whether to use user specified Bruker .m directory method file or to use the original methods in the
        new AutoXecute sequence.
    :return: List of dictionaries containing style template to show or hide parameters.
    """
    if value:
        return copy.deepcopy(SHOWN)
    elif not value:
        return copy.deepcopy(HIDDEN)


@app.callback([Output('run_output_directory_value', 'value'),
               Output('run_output_directory_value', 'valid'),
               Output('run_output_directory_value', 'invalid')],
              Input('run_select_output_directory', 'n_clicks'))
def select_new_output_directory(n_clicks):
    """
    Dash callback to select a new user defined output directory for the new AutoXecute sequence and the resulting data
    acquired using that sequence in timsControl.

    :param n_clicks: Input signal if the run_select_output_directory button is clicked.
    :return: Tuple of the updated output directory path, whether the path is valid, and whether the path is invalid.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'run_select_output_directory.n_clicks':
        dirname = get_path_name()
        if os.path.exists(dirname):
            return dirname, True, False
        else:
            return dirname, False, True


@app.callback([Output('run_method_value', 'value'),
               Output('run_method_value', 'valid'),
               Output('run_method_value', 'invalid')],
              Input('run_select_method', 'n_clicks'))
def select_new_method_(n_clicks):
    """
    Dash callback to select a new user defined Bruker .m method for the new AutoXecute sequence and the resulting data
    acquired using that sequence in timsControl.

    :param n_clicks: Input signal if the run_select_method button is clicked.
    :return: Tuple of the updated Bruker .m directory path, whether the path is valid, and whether the path is invalid.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'run_select_method.n_clicks':
        dirname = get_path_name()
        if dirname.endswith('.m') and os.path.exists(dirname):
            return dirname, True, False
        else:
            return dirname, False, True


@app.callback(Output('preview_figure', 'figure', allow_duplicate=True),
              Input('preview_figure', 'relayoutData'),
              State('store_plot', 'data'),
              prevent_initial_call=True,
              memoize=True)
def resample_spectrum(relayoutdata: dict, fig: FigureResampler):
    """
    Dash callback used for spectrum resampling to improve plotly figure performance.

    :param relayoutdata: Input signal with dictionary with spectrum_plot relayoutData.
    :param fig: State signal for data store for plotly_resampler.
    :return: Figure object used to update spectrum_plot figure.
    """
    if fig is None:
        return no_update
    return fig.construct_update_data_patch(relayoutdata)


if __name__ == '__main__':
    app.run_server(debug=False)
