# The following code has been modified from pyMALDIproc and pyMALDIviz.
# For more infromation, see: https://github.com/gtluu/pyMALDIproc


import toml
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

# get AutoXecute sequence path
AUTOX_SEQ = get_autox_sequence_filename()

app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform(),
                            ServersideOutputTransform(backends=[FileSystemBackend(cache_dir=FILE_SYSTEM_BACKEND)])],
                external_stylesheets=[dbc.themes.SPACELAB])
app.layout = get_dashboard_layout(get_maldi_dda_preprocessing_params(),
                                  get_geometry_format(et.parse(AUTOX_SEQ).getroot()),
                                  get_autox_path_dict(AUTOX_SEQ),
                                  AUTOX_SEQ)


@app.callback([Output({'type': 'raw_data_path_input', 'index': MATCH}, 'value'),
               Output({'type': 'raw_data_path_input', 'index': MATCH}, 'valid'),
               Output({'type': 'raw_data_path_input', 'index': MATCH}, 'invalid')],
              [Input({'type': 'raw_data_path_button', 'index': MATCH}, 'n_clicks'),
               Input({'type': 'raw_data_path_button', 'index': MATCH}, 'id'),
               Input('store_autox_path_dict', 'data')])
def update_raw_data_path(n_clicks, button_id, autox_path_dict):
    """
    Dash callback to update the raw data path during AutoXecute sequence data path validation.

    :param n_clicks: Input signal when a given raw_data_path_button button is clicked.
    :param button_id: ID of the raw_data_path_button clicked.
    :param autox_path_dict: Input signal containing data from autox_path_dict.
    :return: Tuple of the updated Bruker .d directory path, whether the path is valid, and whether the path is invalid.
    """
    dirname = get_path_name()
    if (dirname.endswith('.d') and
            os.path.exists(dirname) and
            os.path.splitext(os.path.split(dirname)[-1])[0] == autox_path_dict[button_id['index']]['sample_name']):
        autox_path_dict[button_id['index']]['raw_data_path'] = dirname
        return dirname, True, False
    else:
        return dirname, False, True


@app.callback([Output({'type': 'method_path_input', 'index': MATCH}, 'value'),
               Output({'type': 'method_path_input', 'index': MATCH}, 'valid'),
               Output({'type': 'method_path_input', 'index': MATCH}, 'invalid')],
              [Input({'type': 'method_path_button', 'index': MATCH}, 'n_clicks'),
               Input({'type': 'method_path_button', 'index': MATCH}, 'id'),
               Input('store_autox_path_dict', 'data')])
def update_method_path(n_clicks, button_id, autox_path_dict):
    """
    Dash callback to update the method path during AutoXecute sequence method path validation.

    :param n_clicks: Input signal when a given method_path_button button is clicked.
    :param button_id: ID of the method_path_button clicked.
    :param autox_path_dict: Input signal containing data from autox_path_dict.
    :return: Tuple of the updated Bruker .m directory path, whether the path is valid, and whether the path is invalid.
    """
    dirname = get_path_name()
    if dirname.endswith('.m') and os.path.exists(dirname):
        autox_path_dict[button_id['index']]['method_path'] = dirname
        return dirname, True, False
    else:
        return dirname, False, True


@app.callback([Output('autox_validation_modal', 'is_open'),
               Output('store_indexed_data', 'data')],
              [Input('autox_validation_modal_close', 'n_clicks'),
               Input('store_indexed_data', 'data')],
              [State({'type': 'raw_data_path_input', 'index': ALL}, 'value'),
               State({'type': 'raw_data_path_input', 'index': ALL}, 'valid'),
               State({'type': 'method_path_input', 'index': ALL}, 'valid'),
               State('autox_validation_modal', 'is_open')])
def toggle_autox_validation_modal_close(n_clicks, indexed_data, raw_data_path_input, raw_data_path_input_valid,
                                        method_path_input_valid, is_open):
    """
    Dash callback to toggle the AutoXecute sequence data/method validation modal window. Data is imported when all
    data and method paths are valid and the modal window is closed.

    :param n_clicks: Input signal if the autox_validation_modal_close button is clicked.
    :param indexed_data: Input signal containing data from store_indexed_data.
    :param raw_data_path_input: List of paths of all the raw data to be loaded.
    :param raw_data_path_input_valid: List of booleans stating whether the raw data paths are valid or not.
    :param method_path_input_valid: List of booleans stating whether the method paths are valid or not.
    :param is_open: State signal to determine whether the autox_validation_modal modal window is open.
    :return: Output signal to determine whether the autox_validation_modal modal window is open.
    """
    if n_clicks:
        for i, j in zip(raw_data_path_input_valid, method_path_input_valid):
            if not i or not j:
                return is_open
        for path in raw_data_path_input:
            data = import_timstof_raw_data(path, mode='profile')
            for spectrum in data:
                indexed_data[spectrum.coord] = path
        return not is_open, indexed_data
    return is_open, indexed_data


@app.callback([Output('new_group_name_modal', 'is_open'),
               Output('group_spots_error_modal', 'is_open'),
               Output('new_group_name_modal_input_value', 'value')],
              [Input('group_spots', 'n_clicks'),
               Input('store_blank_spots', 'data'),
               Input('store_spot_groups', 'data')],
              [State('plate_map', 'selected_cells'),
               State('plate_map', 'data'),
               State('new_group_name_modal', 'is_open'),
               State('group_spots_error_modal', 'is_open')])
def toggle_group_spots_modal(n_clicks, blank_spots, spot_groups, spots, plate_map_data, new_group_name_modal_is_open,
                             group_spots_error_modal_is_open):
    """
    Dash callback to toggle the modal window for entering a new spot group name.

    :param n_clicks: Input signal if the group_spots button is clicked.
    :param blank_spots: Input signal containing data from store_blank_spots.
    :param spot_groups: Input signal containing data from store_spot_groups.
    :param spots: State signal containing the currently selected cells in the plate map.
    :param plate_map_data: State signal containing plate map data.
    :param new_group_name_modal_is_open: State signal to determine whether the new_group_name_modal modal window is
        open.
    :param group_spots_error_modal_is_open: State signal to determine whether the group_spots_error_modal modal
        window is open.
    :return: Output signal to determine whether the new_group_name_modal and group_spots_error_modal modal windows are
        open and the value of the new spot group name.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'group_spots.n_clicks':
        if spots:
            error = False
            for spot in spots:
                spot = plate_map_data[spot['row']][spot['column_id']]
                if spot in blank_spots['spots'] or spot in [i for value in spot_groups.values() for i in value]:
                    error = True
            if not error:
                return not new_group_name_modal_is_open, group_spots_error_modal_is_open, ''
            elif error:
                return new_group_name_modal_is_open, not group_spots_error_modal_is_open, ''


@app.callback([Output('plate_map', 'style_data_conditional'),
               Output('plate_map_legend', 'style_data_conditional'),
               Output('plate_map_legend', 'data'),
               Output('new_group_name_modal', 'is_open'),
               Output('new_group_name_modal_input_value', 'value'),
               Output('plate_map', 'selected_cells'),
               Output('plate_map', 'active_cell'),
               Output('store_spot_groups', 'data')],
              [Input('new_group_name_modal_save', 'n_clicks'),
               Input('store_spot_groups', 'data')],
              [State('plate_map', 'selected_cells'),
               State('plate_map', 'style_data_conditional'),
               State('plate_map', 'data'),
               State('plate_map_legend', 'style_data_conditional'),
               State('plate_map_legend', 'data'),
               State('new_group_name_modal_input_value', 'value'),
               State('new_group_name_modal_input_value', 'valid'),
               State('new_group_name_modal', 'is_open'),])
def group_spots(n_clicks, spot_groups, spots, plate_map_cell_style, plate_map_data, plate_map_legend_cell_style,
                plate_map_legend_data, new_group_name, new_group_name_valid, new_group_name_modal_is_open):
    """
    Dash callback to mark selected spots in the plate map as a group by changing the cell style and adding the cell IDs
    to the dcc.Store store_blank_spots. A new entry in the plate map legend is added for the new spot group.

    :param n_clicks: Input signal if the new_group_name_modal_save button is clicked.
    :param spot_groups: Input signal containing data from store_spot_groups.
    :param spots: State signal containing the currently selected cells in the plate map.
    :param plate_map_cell_style: State signal containing the current style of the cells in the plate map.
    :param plate_map_data: State signal containing plate map data.
    :param plate_map_legend_cell_style: State signal containing the current style of the cells in the plate map legend.
    :param plate_map_legend_data: State signal containing the plate map legend data.
    :param new_group_name: State signal containing the value of the new group name entered.
    :param new_group_name_valid: State signal to determine whether the currently entered group name is valid.
    :param new_group_name_modal_is_open: State signal to determine whether the new_group_name_modal modal window is
        open.
    :return: Output signal containing updated style data for the plate_map and plate_map_legend, plate_map_legend data,
        determining whether the new_group_name_modal modal window is open, resetting the value of the new group name
        input value, resetting the selected and active cells in the plate_map, and containing the updated spot group
        data.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'new_group_name_modal_save.n_clicks' and new_group_name_valid and \
            new_group_name not in pd.DataFrame(plate_map_legend_data)['Category'].values.tolist():
        gray_indices = [(style_dict['if']['row_index'], style_dict['if']['column_id'])
                        for style_dict in plate_map_cell_style
                        if 'if' in style_dict.keys() and 'backgroundColor' in style_dict.keys()
                        if style_dict['backgroundColor'] == 'gray'
                        if 'row_index' in style_dict['if'].keys() and 'column_id' in style_dict['if'].keys()]
        indices = [(i['row'], i['column_id']) for i in spots]
        indices = [i for i in indices if i not in gray_indices]
        spot_groups[new_group_name] = [plate_map_data[i[0]][i[1]] for i in indices]
        color = get_rgb_color()
        plate_map_cell_style = plate_map_cell_style + [{'if': {'row_index': row, 'column_id': col},
                                                        'backgroundColor': color, 'color': 'white'}
                                                       for row, col in indices]
        plate_map_legend_df = pd.concat([pd.DataFrame(plate_map_legend_data),
                                         pd.DataFrame({'Category': [new_group_name]})], ignore_index=True)
        plate_map_legend_cell_style = plate_map_legend_cell_style + [{'if': {'row_index': plate_map_legend_df.shape[0] - 1},
                                                                      'backgroundColor': color, 'color': 'white'}]
        return (plate_map_cell_style,
                plate_map_legend_cell_style,
                plate_map_legend_df.to_dict('records'),
                not new_group_name_modal_is_open,
                '',
                [],
                None,
                spot_groups)


@app.callback(Output('group_spots_error_modal', 'is_open'),
              Input('group_spots_error_modal_close', 'n_clicks'),
              State('group_spots_error_modal', 'is_open'))
def toggle_group_spots_error_modal(n_clicks, is_open):
    """
    Dash callback to toggle the error message window for invalid spots selected in the plate map for grouping or marking
    as blank.

    :param n_clicks: Input signal if the group_spots_error_modal_close button is clicked.
    :param is_open: State signal to determine whether the group_spots_error_modal modal window is open.
    :return: Output signal to determine whether the group_spots_error_modal modal window is open.
    """
    if n_clicks:
        return not is_open
    return is_open


@app.callback([Output('new_group_name_modal_input_value', 'valid'),
               Output('new_group_name_modal_input_value', 'invalid')],
              Input('new_group_name_modal_input_value', 'value'),
              [State('new_group_name_modal_input_value', 'value'),
               State('plate_map_legend', 'data')])
def check_if_new_group_name_valid(input_value, state_value, plate_map_legend_data):
    """
    Dash callback to determine the validity of the new group name entered.

    :param input_value: Input signal containing the value of the new group name entered.
    :param state_value: State signal containing the value of the new group name entered.
    :param plate_map_legend_data: State signal containing the plate map legend data.
    :return: Output signal to determine whether the new group name entered is valid or not.
    """
    if state_value != '' and state_value not in pd.DataFrame(plate_map_legend_data)['Category'].values.tolist():
        return True, False
    return False, True


@app.callback([Output('plate_map', 'style_data_conditional'),
               Output('plate_map', 'selected_cells'),
               Output('plate_map', 'active_cell'),
               Output('group_spots_error_modal', 'is_open'),
               Output('store_blank_spots', 'data')],
              [Input('mark_spot_as_blank', 'n_clicks'),
               Input('store_blank_spots', 'data'),
               Input('store_spot_groups', 'data')],
              [State('plate_map', 'selected_cells'),
               State('plate_map', 'style_data_conditional'),
               State('plate_map', 'data'),
               State('group_spots_error_modal', 'is_open')])
def mark_spots_as_blank(n_clicks, blank_spots, spot_groups, spots, cell_style, data, is_open):
    """
    Dash callback to mark a selected spot in the plate map as a 'blank' spot by changing the cell style and adding the
    cell ID to the dcc.Store store_blank_spots.

    :param n_clicks: Input signal if the mark_spot_as_blank button is clicked.
    :param blank_spots: Input signal containing data from store_blank_spots.
    :param spot_groups: Input signal containing data from store_spot_groups.
    :param spots: State signal containing the currently selected cells in the plate map.
    :param cell_style: State signal containing the current style of the cells in the plate map.
    :param data: State signal containing plate map data.
    :param is_open: State signal to determine whether the group_spots_error_modal window is open.
    :return: Style data with the updated blank spot style for the selected cells appended.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'mark_spot_as_blank.n_clicks':
        error = False
        for spot in spots:
            spot = data[spot['row']][spot['column_id']]
            if spot in blank_spots['spots'] or spot in [i for value in spot_groups.values() for i in value]:
                error = True
        if not error:
            gray_indices = [(style_dict['if']['row_index'], style_dict['if']['column_id'])
                            for style_dict in cell_style
                            if 'if' in style_dict.keys() and 'backgroundColor' in style_dict.keys()
                            if style_dict['backgroundColor'] == 'gray'
                            if 'row_index' in style_dict['if'].keys() and 'column_id' in style_dict['if'].keys()]
            indices = [(i['row'], i['column_id']) for i in spots]
            indices = [i for i in indices if i not in gray_indices]
            blank_spots['spots'] = blank_spots['spots'] + [data[i[0]][i[1]]
                                                           for i in indices
                                                           if data[i[0]][i[1]] not in blank_spots['spots']]
            return cell_style + [{'if': {'row_index': row, 'column_id': col},
                                  'backgroundColor': 'green', 'color': 'white'}
                                 for row, col in indices], [], None, is_open, blank_spots
        elif error:
            return cell_style, [], None, not is_open, blank_spots


@app.callback([Output('plate_map', 'style_data_conditional'),
               Output('plate_map_legend', 'style_data_conditional'),
               Output('plate_map_legend', 'data'),
               Output('store_blank_spots', 'data'),
               Output('store_spot_groups', 'data')],
              [Input('clear_blanks_and_groups', 'n_clicks'),
               Input('store_plate_format', 'data'),
               Input('store_autox_seq', 'data')])
def clear_blanks_and_groups(n_clicks, plate_format, autox_seq):
    """
    Dash callback to remove all blank spot and spot group styling from the plate map, remove all blank spot IDs from
    the dcc.Store store_blank_spots, and remove all spot groups from the dcc.Store store_spot_groups.

    :param n_clicks: Input signal if the clear_blank_spots button is clicked.
    :param plate_format: Input signal containing data from store_plate_format.
    :param autox_seq: Input signal containing data from store_autox_seq.
    :return: Default style data for the plate map.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'clear_blanks_and_groups.n_clicks':
        return (get_plate_map_style(get_plate_map(plate_format), et.parse(autox_seq).getroot()),
                [{'if': {'row_index': 1},
                  'backgroundColor': 'green', 'color': 'white'},
                 {'if': {'row_index': 2},
                  'backgroundColor': 'gray', 'color': 'white'}],
                get_plate_map_legend().to_dict('records'),
                {'spots': []},
                {})


@ app.callback([Output('exclusion_list', 'data'),
                Output('view_exclusion_list_spectra', 'style'),
                Output('store_blank_params_log', 'data')],
               [Input('generate_exclusion_list_from_blank_spots', 'n_clicks'),
                Input('store_preprocessing_params', 'data'),
                Input('store_blank_spots', 'data'),
                Input('store_indexed_data', 'data')])
def generate_exclusion_list_from_blank_spots(n_clicks, preprocessing_params, blank_spots, indexed_data):
    """
    Dash callback to perform preprocessing using parameters defined in the Edit Preprocessing Parameters modal window
    on blank spots marked on the plate map and generate an exclusion list to be displayed in the exclusion list table
    and used during sample precursor selection.

    :param n_clicks: Input signal if the generate_exclusion_list_from_blank_spots button is clicked.
    :param preprocessing_params: Input signal containing data from store_preprocessing_params.
    :param blank_spots: Input signal containing data from store_blank_spots.
    :param indexed_data: Input signal containing data from store_indexed_data.
    :return: Tuple of updated exclusion list data table data, style data to make the view_exclusion_list_spectra button
        visible, and data from blank_params_log.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'generate_exclusion_list_from_blank_spots.n_clicks':
        blank_spectra = []
        for spot in blank_spots['spots']:
            data = import_timstof_raw_data(indexed_data[spot], mode='profile')
            blank_spectra = blank_spectra + [spectrum for spectrum in data if spectrum.coord == spot]
        params = copy.deepcopy(preprocessing_params)
        blank_params_log = copy.deepcopy(preprocessing_params)
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
        # peak picking
        for spectrum in blank_spectra:
            spectrum.peak_picking(**params['PEAK_PICKING'])
        # generate feature matrix
        blank_feature_matrix = get_feature_matrix(blank_spectra, missing_value_imputation=False)
        # get exclusion list and return as df.to_dict('records')
        exclusion_list_df = pd.DataFrame(data={'m/z': np.unique(blank_feature_matrix['mz'].values)})
        return exclusion_list_df.to_dict('records'), {'margin': '20px', 'display': 'flex'}, blank_params_log


@app.callback([Output('exclusion_list_blank_spectra_modal', 'is_open'),
               Output('exclusion_list_blank_spectra_id', 'options'),
               Output('exclusion_list_blank_spectra_id', 'value'),
               Output('exclusion_list_blank_spectra_figure', 'figure')],
              [Input('view_exclusion_list_spectra', 'n_clicks'),
               Input('store_blank_spots', 'data'),
               Input('store_indexed_data', 'data')],
              State('exclusion_list_blank_spectra_modal', 'is_open'))
def view_exclusion_list_spectra(n_clicks, blank_spots, indexed_data, is_open):
    """
    Dash callback to view the preprocessed blank spot spectra that were used to generate the exclusion list.

    :param n_clicks: Input signal if the view_exclusion_list_spectra button is clicked.
    :param blank_spots: Input signal containing data from store_blank_spots.
    :param indexed_data: Input signal containing data from store_indexed_data.
    :param is_open: State signal to determine whether the exclusion_list_blank_spectra_modal modal window is open.
    :return: Tuple of the output signal to determine whether the exclusion_list_blank_spectra_modal modal window is
        open, the list of blank spectra IDs to populate the dropdown menu options, the list of blank spectra IDs to
        populate the dropdown menu values, and a blank figure to serve as a placeholder in the modal window body.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'view_exclusion_list_spectra.n_clicks':
        # populate dropdown menu
        dropdown_options = [{'label': i, 'value': i} for i in indexed_data.keys() if i in blank_spots['spots']]
        dropdown_value = [i for i in indexed_data.keys() if i in blank_spots['spots']]
        return not is_open, dropdown_options, dropdown_value, blank_figure()


@app.callback([Output('exclusion_list_blank_spectra_modal', 'is_open'),
               Output('exclusion_list_blank_spectra_id', 'options'),
               Output('exclusion_list_blank_spectra_id', 'value'),
               Output('exclusion_list_blank_spectra_figure', 'figure')],
              Input('exclusion_list_blank_spectra_modal_close', 'n_clicks'),
              State('exclusion_list_blank_spectra_modal', 'is_open'))
def close_view_exclusion_list_spectra_modal(n_clicks, is_open):
    """
    Dash callback to view the preprocessed blank spot spectra that were used to generate the exclusion list.

    :param n_clicks: Input signal if the exclusion_list_blank_spectra_modal_close button is clicked.
    :param is_open: State signal to determine whether the exclusion_list_blank_spectra_modal modal window is open.
    :return: Tuple of the output signal to determine whether the exclusion_list_blank_spectra_modal modal window is
        open, the list of blank spectra IDs to populate the dropdown menu options, the list of blank spectra IDs to
        populate the dropdown menu values, and a blank figure to serve as a placeholder in the modal window body.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'exclusion_list_blank_spectra_modal_close.n_clicks':
        return not is_open, [], [], blank_figure()


@app.callback([Output('exclusion_list_blank_spectra_figure', 'figure'),
               Output('store_plot', 'data')],
              [Input('exclusion_list_blank_spectra_id', 'value'),
               Input('store_blank_spots', 'data'),
               Input('store_blank_params_log', 'data'),
               Input('store_indexed_data', 'data'),])
def update_blank_spectrum(value, blank_spots, blank_params_log, indexed_data):
    """
    Dash callback to plot the spectrum selected from the exclusion_list_blank_spectra_id dropdown using plotly.express
    and plotly_resampler.FigureResampler.

    :param value: Input signal exclusion_list_blank_spectra_id used as the key in store_indexed_data.
    :param blank_spots: Input signal containing data from store_blank_spots.
    :param blank_params_log: Input signal containing data from store_blank_params_log.
    :param indexed_data: Input signal containing data from store_indexed_data.
    :return: Tuple of spectrum figure as a plotly.express.line plot and data store for plotly_resampler.
    """
    blank_spectra = []
    for spot in blank_spots['spots']:
        data = import_timstof_raw_data(indexed_data[spot], mode='profile')
        blank_spectra = blank_spectra + [spectrum for spectrum in data if spectrum.coord == spot]
    blank_spectrum = [spectrum for spectrum in blank_spectra if spectrum.coord == value][0]
    # preprocessing
    if blank_params_log['TRIM_SPECTRUM']['run']:
        del blank_params_log['TRIM_SPECTRUM']['run']
        blank_spectrum.trim_spectrum(**blank_params_log['TRIM_SPECTRUM'])
    if blank_params_log['TRANSFORM_INTENSITY']['run']:
        del blank_params_log['TRANSFORM_INTENSITY']['run']
        blank_spectrum.transform_intensity(**blank_params_log['TRANSFORM_INTENSITY'])
    if blank_params_log['SMOOTH_BASELINE']['run']:
        del blank_params_log['SMOOTH_BASELINE']['run']
        blank_spectrum.smooth_baseline(**blank_params_log['SMOOTH_BASELINE'])
    if blank_params_log['REMOVE_BASELINE']['run']:
        del blank_params_log['REMOVE_BASELINE']['run']
        blank_spectrum.remove_baseline(**blank_params_log['REMOVE_BASELINE'])
    if blank_params_log['NORMALIZE_INTENSITY']['run']:
        del blank_params_log['NORMALIZE_INTENSITY']['run']
        blank_spectrum.normalize_intensity(**blank_params_log['NORMALIZE_INTENSITY'])
    if blank_params_log['BIN_SPECTRUM']['run']:
        del blank_params_log['BIN_SPECTRUM']['run']
        blank_spectrum.bin_spectrum(**blank_params_log['BIN_SPECTRUM'])
    # peak picking
    blank_spectrum.peak_picking(**blank_params_log['PEAK_PICKING'])
    fig = get_spectrum(blank_spectrum)
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
        return pd.DataFrame(columns=['m/z']).to_dict('records'), {'margin': '20px', 'display': 'none'}


@app.callback([Output('edit_processing_parameters_modal', 'is_open'),
               Output('store_preprocessing_params', 'data')],
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
               Input('precursor_selection_exclusion_list_tolerance_value', 'value'),
               Input('store_preprocessing_params', 'data')],
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
                                               preprocessing_params,
                                               is_open):
    """
    Dash callback to toggle the preprocessing parameters modal window, populate the current preprocessing parameters
    saved in the dcc.Store store_preprocessing_params, and save any modified preprocessing parameters to
    store_preprocessing_params if the Save button is clicked.

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
    :param preprocessing_params: Input signal containing data from store_preprocessing_params.
    :param is_open: State signal to determine whether the edit_preprocessing_parameters_modal modal window is open.
    :return: Output signal to determine whether the edit_preprocessing_parameters_modal modal window is open and output
        signal containing data from store_preprocessing_params.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if (changed_id == 'edit_preprocessing_parameters.n_clicks' or
            changed_id == 'edit_processing_parameters_save.n_clicks' or
            changed_id == 'edit_processing_parameters_cancel.n_clicks'):
        if changed_id == 'edit_processing_parameters_save.n_clicks':
            preprocessing_params['TRIM_SPECTRUM']['run'] = trim_spectrum_checkbox
            preprocessing_params['TRIM_SPECTRUM']['lower_mass_range'] = trim_spectrum_lower_mass_range
            preprocessing_params['TRIM_SPECTRUM']['upper_mass_range'] = trim_spectrum_upper_mass_range
            preprocessing_params['TRANSFORM_INTENSITY']['run'] = transform_intensity_checkbox
            preprocessing_params['TRANSFORM_INTENSITY']['method'] = transform_intensity_method
            preprocessing_params['SMOOTH_BASELINE']['run'] = smooth_baseline_checkbox
            preprocessing_params['SMOOTH_BASELINE']['method'] = smooth_baseline_method
            preprocessing_params['SMOOTH_BASELINE']['window_length'] = smooth_baseline_window_length
            preprocessing_params['SMOOTH_BASELINE']['polyorder'] = smooth_baseline_polyorder
            preprocessing_params['SMOOTH_BASELINE']['delta_mz'] = smooth_baseline_delta_mz
            preprocessing_params['SMOOTH_BASELINE']['diff_thresh'] = smooth_baseline_diff_thresh
            preprocessing_params['REMOVE_BASELINE']['run'] = remove_baseline_checkbox
            preprocessing_params['REMOVE_BASELINE']['method'] = remove_baseline_method
            preprocessing_params['REMOVE_BASELINE']['min_half_window'] = remove_baseline_min_half_window
            preprocessing_params['REMOVE_BASELINE']['max_half_window'] = remove_baseline_max_half_window
            preprocessing_params['REMOVE_BASELINE']['decreasing'] = remove_baseline_decreasing
            preprocessing_params['REMOVE_BASELINE']['smooth_half_window'] = remove_baseline_smooth_half_window
            preprocessing_params['REMOVE_BASELINE']['filter_order'] = remove_baseline_filter_order
            preprocessing_params['REMOVE_BASELINE']['sigma'] = remove_baseline_sigma
            preprocessing_params['REMOVE_BASELINE']['increment'] = remove_baseline_increment
            preprocessing_params['REMOVE_BASELINE']['max_hits'] = remove_baseline_max_hits
            preprocessing_params['REMOVE_BASELINE']['window_tol'] = remove_baseline_window_tol
            preprocessing_params['REMOVE_BASELINE']['lambda_'] = remove_baseline_lambda_
            preprocessing_params['REMOVE_BASELINE']['porder'] = remove_baseline_porder
            preprocessing_params['REMOVE_BASELINE']['repetition'] = remove_baseline_repetition
            preprocessing_params['REMOVE_BASELINE']['degree'] = remove_baseline_degree
            preprocessing_params['REMOVE_BASELINE']['gradient'] = remove_baseline_gradient
            preprocessing_params['NORMALIZE_INTENSITY']['run'] = normalize_intensity_checkbox
            preprocessing_params['NORMALIZE_INTENSITY']['method'] = normalize_intensity_method
            preprocessing_params['BIN_SPECTRUM']['run'] = bin_spectrum_checkbox
            preprocessing_params['BIN_SPECTRUM']['n_bins'] = bin_spectrum_n_bins
            preprocessing_params['BIN_SPECTRUM']['lower_mass_range'] = bin_spectrum_lower_mass_range
            preprocessing_params['BIN_SPECTRUM']['upper_mass_range'] = bin_spectrum_upper_mass_range
            preprocessing_params['PEAK_PICKING']['method'] = peak_picking_method
            preprocessing_params['PEAK_PICKING']['snr'] = peak_picking_snr
            preprocessing_params['PEAK_PICKING']['widths'] = peak_picking_widths
            preprocessing_params['PEAK_PICKING']['deisotope'] = peak_picking_deisotope
            preprocessing_params['PEAK_PICKING']['fragment_tolerance'] = peak_picking_fragment_tolerance
            preprocessing_params['PEAK_PICKING']['fragment_unit_ppm'] = peak_picking_fragment_unit_ppm
            preprocessing_params['PEAK_PICKING']['min_charge'] = peak_picking_min_charge
            preprocessing_params['PEAK_PICKING']['max_charge'] = peak_picking_max_charge
            preprocessing_params['PEAK_PICKING']['keep_only_deisotoped'] = peak_picking_keep_only_deisotoped
            preprocessing_params['PEAK_PICKING']['min_isopeaks'] = peak_picking_min_isopeaks
            preprocessing_params['PEAK_PICKING']['max_isopeaks'] = peak_picking_max_isopeaks
            preprocessing_params['PEAK_PICKING']['make_single_charged'] = peak_picking_make_single_charged
            preprocessing_params['PEAK_PICKING']['annotate_charge'] = peak_picking_annotate_charge
            preprocessing_params['PEAK_PICKING']['annotate_iso_peak_count'] = peak_picking_annotate_iso_peak_count
            preprocessing_params['PEAK_PICKING']['use_decreasing_model'] = peak_picking_use_decreasing_model
            preprocessing_params['PEAK_PICKING']['start_intensity_check'] = peak_picking_start_intensity_check
            preprocessing_params['PEAK_PICKING']['add_up_intensity'] = peak_picking_add_up_intensity
            preprocessing_params['PRECURSOR_SELECTION']['top_n'] = precursor_selection_top_n_value
            preprocessing_params['PRECURSOR_SELECTION']['use_exclusion_list'] = precursor_selection_use_exclusion_list
            preprocessing_params['PRECURSOR_SELECTION']['exclusion_list_tolerance'] = precursor_selection_exclusion_list_tolerance_value
        return not is_open, preprocessing_params
    return is_open, preprocessing_params


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
               Output('preview_figure', 'figure'),
               Output('store_sample_params_log', 'data'),
               Output('store_precursor_data', 'data')],
              [Input('preview_precursor_list', 'n_clicks'),
               Input('store_preprocessing_params', 'data'),
               Input('store_blank_spots', 'data'),
               Input('store_spot_groups', 'data'),
               Input('store_indexed_data', 'data')],
              [State('preview_precursor_list_modal', 'is_open'),
               State('exclusion_list', 'data')])
def preview_precursor_list(n_clicks,
                           preprocessing_params,
                           blank_spots,
                           spot_groups,
                           indexed_data,
                           is_open,
                           exclusion_list):
    """
    Dash callback to preprocess sample spectra based on current preprocessing parameters and view the spectra in a
    modal window. In the modal window, going Back will reset and undo all preprocessing, while continuing to generate
    the MS/MS AutoXecute sequences closes the preview_precursor_list_modal modal window.

    :param n_clicks: Input signal if the preview_precursor_list button is clicked.
    :param preprocessing_params: Input signal containing data from store_preprocessing_params.
    :param blank_spots: Input signal containing data from store_blank_spots.
    :param spot_groups: Input signal containing data from store_spot_groups.
    :param indexed_data: Input signal containing data from store_indexed_data.
    :param is_open: State signal to determine whether the preview_precursor_list_modal modal window is open.
    :param exclusion_list: State signal to provide the current exclusion list data.
    :return: Tuple of output signal to determine whether the preview_precursor_list_modal modal window is open, the
        list of spectra IDs to populate the dropdown menu options, the list of spectra IDs to populate the dropdown
        menu values, and a blank figure to serve as a placeholder in the modal window body.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'preview_precursor_list.n_clicks':
        spectra = {}
        precursor_data = {}
        for spot in indexed_data.keys():
            if spot not in blank_spots['spots']:
                data = import_timstof_raw_data(indexed_data[spot], mode='profile')
                spectra[spot] = [spectrum for spectrum in data if spectrum.coord == spot][0]
        params = copy.deepcopy(preprocessing_params)
        sample_params_log = copy.deepcopy(params)
        # preprocessing
        if params['TRIM_SPECTRUM']['run']:
            del params['TRIM_SPECTRUM']['run']
            for key, spectrum in spectra.items():
                spectrum.trim_spectrum(**params['TRIM_SPECTRUM'])
        if params['TRANSFORM_INTENSITY']['run']:
            del params['TRANSFORM_INTENSITY']['run']
            for key, spectrum in spectra.items():
                spectrum.transform_intensity(**params['TRANSFORM_INTENSITY'])
        if params['SMOOTH_BASELINE']['run']:
            del params['SMOOTH_BASELINE']['run']
            for key, spectrum in spectra.items():
                spectrum.smooth_baseline(**params['SMOOTH_BASELINE'])
        if params['REMOVE_BASELINE']['run']:
            del params['REMOVE_BASELINE']['run']
            for key, spectrum in spectra.items():
                spectrum.remove_baseline(**params['REMOVE_BASELINE'])
        if params['NORMALIZE_INTENSITY']['run']:
            del params['NORMALIZE_INTENSITY']['run']
            for key, spectrum in spectra.items():
                spectrum.normalize_intensity(**params['NORMALIZE_INTENSITY'])
        if params['BIN_SPECTRUM']['run']:
            del params['BIN_SPECTRUM']['run']
            for key, spectrum in spectra.items():
                spectrum.bin_spectrum(**params['BIN_SPECTRUM'])
        # peak picking
        for key, spectrum in spectra.items():
            spectrum.peak_picking(**params['PEAK_PICKING'])
        # groups have been defined
        if len(spot_groups.keys()) > 0:
            # process groups
            spots_in_group = [i for value in spot_groups.values() for i in value]
            for group, list_of_spots in spot_groups.items():
                group_spectra = [spectra[spot] for spot in list_of_spots]
                group_feature_matrix = get_feature_matrix(group_spectra, missing_value_imputation=False)
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
                    spectra[spot].peak_picked_mz_array = None
                    spectra[spot].peak_picked_intensity_array = None
                    spectra[spot].peak_picking_indices = None
                for spot, values in feature_dict.items():
                    spectra[spot].peak_picked_mz_array = np.array(values['mz'])
                    spectra[spot].peak_picked_intensity_array = np.array(values['intensity'])
                    spectra[spot].peak_picking_indices = np.array(values['index'])
                    if spot not in precursor_data.keys():
                        precursor_data[spot] = {}
                        precursor_data[spot]['peak_picked_mz_array'] = copy.deepcopy(spectra[spot].peak_picked_mz_array)
                        precursor_data[spot]['peak_picked_intensity_array'] = copy.deepcopy(spectra[spot].peak_picked_intensity_array)
                        precursor_data[spot]['peak_picking_indices'] = copy.deepcopy(spectra[spot].peak_picking_indices)
                    elif spot in precursor_data.keys():
                        precursor_data[spot]['peak_picked_mz_array'] = copy.deepcopy(spectra[spot].peak_picked_mz_array)
                        precursor_data[spot]['peak_picked_intensity_array'] = copy.deepcopy(spectra[spot].peak_picked_intensity_array)
                        precursor_data[spot]['peak_picking_indices'] = copy.deepcopy(spectra[spot].peak_picking_indices)
            # process all other spots not found in a group
            # remove peaks found in exclusion list
            if params['PRECURSOR_SELECTION']['use_exclusion_list']:
                exclusion_list = pd.DataFrame(exclusion_list)
                if not exclusion_list.empty:
                    for key, spectrum in spectra.items():
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
            for key, spectrum in spectra.items():
                if key not in spots_in_group:
                    top_n_indices = np.argsort(spectrum.peak_picked_intensity_array)[::-1][:params['PRECURSOR_SELECTION']['top_n']]
                    spectrum.peak_picked_mz_array = spectrum.peak_picked_mz_array[top_n_indices]
                    spectrum.peak_picked_intensity_array = spectrum.peak_picked_intensity_array[top_n_indices]
                    spectrum.peak_picking_indices = spectrum.peak_picking_indices[top_n_indices]
                    if key not in precursor_data.keys():
                        precursor_data[key] = {}
                        precursor_data[key]['peak_picked_mz_array'] = copy.deepcopy(spectra[key].peak_picked_mz_array)
                        precursor_data[key]['peak_picked_intensity_array'] = copy.deepcopy(spectra[key].peak_picked_intensity_array)
                        precursor_data[key]['peak_picking_indices'] = copy.deepcopy(spectra[key].peak_picking_indices)
                    elif key in precursor_data.keys():
                        precursor_data[key]['peak_picked_mz_array'] = copy.deepcopy(spectra[key].peak_picked_mz_array)
                        precursor_data[key]['peak_picked_intensity_array'] = copy.deepcopy(spectra[key].peak_picked_intensity_array)
                        precursor_data[key]['peak_picking_indices'] = copy.deepcopy(spectra[key].peak_picking_indices)
        # no groups defined
        else:
            # remove peaks found in exclusion list
            if params['PRECURSOR_SELECTION']['use_exclusion_list']:
                exclusion_list = pd.DataFrame(exclusion_list)
                if not exclusion_list.empty:
                    for key, spectrum in spectra.items():
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
            for key, spectrum in spectra.items():
                top_n_indices = np.argsort(spectrum.peak_picked_intensity_array)[::-1][:params['PRECURSOR_SELECTION']['top_n']]
                spectrum.peak_picked_mz_array = spectrum.peak_picked_mz_array[top_n_indices]
                spectrum.peak_picked_intensity_array = spectrum.peak_picked_intensity_array[top_n_indices]
                spectrum.peak_picking_indices = spectrum.peak_picking_indices[top_n_indices]
                if key not in precursor_data.keys():
                    precursor_data[key] = {}
                    precursor_data[key]['peak_picked_mz_array'] = copy.deepcopy(spectra[key].peak_picked_mz_array)
                    precursor_data[key]['peak_picked_intensity_array'] = copy.deepcopy(spectra[key].peak_picked_intensity_array)
                    precursor_data[key]['peak_picking_indices'] = copy.deepcopy(spectra[key].peak_picking_indices)
                elif key in precursor_data.keys():
                    precursor_data[key]['peak_picked_mz_array'] = copy.deepcopy(spectra[key].peak_picked_mz_array)
                    precursor_data[key]['peak_picked_intensity_array'] = copy.deepcopy(spectra[key].peak_picked_intensity_array)
                    precursor_data[key]['peak_picking_indices'] = copy.deepcopy(spectra[key].peak_picking_indices)
        # populate dropdown menu
        dropdown_options = [{'label': i, 'value': i} for i in indexed_data.keys() if i not in blank_spots['spots']]
        dropdown_value = [i for i in indexed_data.keys() if i not in blank_spots['spots']]
        return not is_open, dropdown_options, dropdown_value, blank_figure(), sample_params_log, precursor_data


@app.callback([Output('preview_precursor_list_modal', 'is_open'),
               Output('preview_id', 'options'),
               Output('preview_id', 'value'),
               Output('preview_figure', 'figure'),
               Output('store_sample_params_log', 'data'),
               Output('store_precursor_data', 'data')],
              Input('preview_precursor_list_modal_back', 'n_clicks'),
              State('preview_precursor_list_modal', 'is_open'))
def close_preview_precursor_list_modal(n_clicks, is_open):
    """
    Dash callback to preprocess sample spectra based on current preprocessing parameters and view the spectra in a
    modal window. In the modal window, going Back will reset and undo all preprocessing, while continuing to generate
    the MS/MS AutoXecute sequences closes the preview_precursor_list_modal modal window.

    :param n_clicks: Input signal if the preview_precursor_list_modal_back button is clicked.
    :param is_open: State signal to determine whether the preview_precursor_list_modal modal window is open.
    :return: Tuple of output signal to determine whether the preview_precursor_list_modal modal window is open, the
        list of spectra IDs to populate the dropdown menu options, the list of spectra IDs to populate the dropdown
        menu values, and a blank figure to serve as a placeholder in the modal window body.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'preview_precursor_list_modal_back.n_clicks':
        return not is_open, [], [], blank_figure(), {}, {}


@app.callback([Output('preview_precursor_list_modal', 'is_open'),
               Output('run_modal', 'is_open'),
               Output('preview_id', 'options'),
               Output('preview_id', 'value'),
               Output('preview_figure', 'figure')],
              Input('preview_precursor_list_modal_run', 'n_clicks'),
              [State('preview_precursor_list_modal', 'is_open'),
               State('run_modal', 'is_open')])
def preview_precursor_list_proceed_with_run(n_clicks, preview_is_open, run_is_open):
    """
    Dash callback to preprocess sample spectra based on current preprocessing parameters and view the spectra in a
    modal window. In the modal window, going Back will reset and undo all preprocessing, while continuing to generate
    the MS/MS AutoXecute sequences closes the preview_precursor_list_modal modal window.

    :param n_clicks: Input signal if the preview_precursor_list_modal_run button is clicked.
    :param preview_is_open: State signal to determine whether the preview_precursor_list_modal modal window is open.
    :param run_is_open: State signal to determine whether the run_modal modal window is open.
    :return: Tuple of output signal to determine whether the preview_precursor_list_modal modal window is open, the
        list of spectra IDs to populate the dropdown menu options, the list of spectra IDs to populate the dropdown
        menu values, and a blank figure to serve as a placeholder in the modal window body.
    """
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'preview_precursor_list_modal_run.n_clicks':
        return not preview_is_open, not run_is_open, [], [], blank_figure()


@app.callback([Output('preview_figure', 'figure'),
               Output('store_plot', 'data')],
              [Input('preview_id', 'value'),
               Input('store_indexed_data', 'data'),
               Input('store_sample_params_log', 'data'),
               Input('store_precursor_data', 'data')])
def update_preview_spectrum(value, indexed_data, sample_params_log, precursor_data):
    """
    Dash callback to plot the spectrum selected from the preview_id dropdown using plotly.express and
    plotly_resampler.FigureResampler.

    :param value: Input signal preview_id used as the key in store_indexed_data.
    :param indexed_data: Input signal containing data from store_indexed_data.
    :param sample_params_log: Input signal containing data from store_sample_params_log.
    :param precursor_data: Input signal containing data from store_precursor_data.
    :return: Tuple of spectrum figure as a plotly.express.line plot and data store for plotly_resampler.
    """
    data = import_timstof_raw_data(indexed_data[value], mode='profile')
    spectrum = [i for i in data if i.coord == value][0]
    # preprocessing
    if sample_params_log['TRIM_SPECTRUM']['run']:
        del sample_params_log['TRIM_SPECTRUM']['run']
        spectrum.trim_spectrum(**sample_params_log['TRIM_SPECTRUM'])
    if sample_params_log['TRANSFORM_INTENSITY']['run']:
        del sample_params_log['TRANSFORM_INTENSITY']['run']
        spectrum.transform_intensity(**sample_params_log['TRANSFORM_INTENSITY'])
    if sample_params_log['SMOOTH_BASELINE']['run']:
        del sample_params_log['SMOOTH_BASELINE']['run']
        spectrum.smooth_baseline(**sample_params_log['SMOOTH_BASELINE'])
    if sample_params_log['REMOVE_BASELINE']['run']:
        del sample_params_log['REMOVE_BASELINE']['run']
        spectrum.remove_baseline(**sample_params_log['REMOVE_BASELINE'])
    if sample_params_log['NORMALIZE_INTENSITY']['run']:
        del sample_params_log['NORMALIZE_INTENSITY']['run']
        spectrum.normalize_intensity(**sample_params_log['NORMALIZE_INTENSITY'])
    if sample_params_log['BIN_SPECTRUM']['run']:
        del sample_params_log['BIN_SPECTRUM']['run']
        spectrum.bin_spectrum(**sample_params_log['BIN_SPECTRUM'])
    if value in precursor_data.keys():
        spectrum.peak_picked_mz_array = copy.deepcopy(precursor_data[value]['peak_picked_mz_array'])
        spectrum.peak_picked_intensity_array = copy.deepcopy(precursor_data[value]['peak_picked_intensity_array'])
        spectrum.peak_picking_indices = copy.deepcopy(precursor_data[value]['peak_picking_indices'])
    if spectrum.peak_picking_indices is None:
        label_peaks = False
    else:
        label_peaks = True
    fig = get_spectrum(spectrum, label_peaks)
    cleanup_file_system_backend()
    return fig, Serverside(fig)


@app.callback([Output('run_modal', 'is_open'),
               Output('run_success_modal', 'is_open')],
              [Input('run_button', 'n_clicks'),
               Input('store_blank_params_log', 'data'),
               Input('store_sample_params_log', 'data'),
               Input('store_autox_seq', 'data'),
               Input('store_autox_path_dict', 'data'),
               Input('store_blank_spots', 'data'),
               Input('store_precursor_data', 'data')],
              [State('run_modal', 'is_open'),
               State('run_success_modal', 'is_open'),
               State('run_output_directory_value', 'value'),
               State('run_method_value', 'value'),
               State('run_method_checkbox', 'value'),
               State('exclusion_list', 'data')])
def generate_msms_autox_sequence(n_clicks, blank_params_log, sample_params_log, autox_seq, autox_path_dict, blank_spots,
                                 precursor_data, run_is_open, success_is_open, outdir, method, method_checkbox,
                                 exclusion_list):
    """
    Dash callback to toggle the run_modal modal window and create the new MS/MS AutoXecute sequence. A new modal window
    displaying a success message and the output directory of the resulting AutoXecute sequence will be shown upon
    success.

    :param n_clicks: Input signal if the run_button button is clicked.
    :param blank_params_log: Input signal containing data from store_blank_params_log.
    :param sample_params_log: Input signal containing data from store_sample_params_log.
    :param autox_seq: Input signal containing data from store_autox_seq.
    :param autox_path_dict: Input signal containing data from store_autox_path_dict.
    :param blank_spots: Input signal containing data from store_blank_spots.
    :param precursor_data: Input signal containing data from store_precursor_data.
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
    if changed_id == 'run_button.n_clicks':
        log = 'fleX MS/MS AutoXecute Generator Log\n\n'
        log += f'Output Directory: {outdir}\n\n'
        ms1_autox = et.parse(autox_seq).getroot()
        new_autox = et.Element(ms1_autox.tag, attrib=ms1_autox.attrib)
        new_autox.attrib['directory'] = outdir
        for spot_group in ms1_autox:
            log += f"Spot Group: {spot_group.attrib['sampleName']}\n"
            for cont in spot_group:
                if cont.attrib['Pos_on_Scout'] not in blank_spots['spots'] and \
                        cont.attrib['Pos_on_Scout'] in precursor_data.keys() and \
                        precursor_data[cont.attrib['Pos_on_Scout']]['peak_picked_mz_array'] is not None and \
                        precursor_data[cont.attrib['Pos_on_Scout']]['peak_picked_intensity_array'] is not None:
                    new_spot_group = et.SubElement(new_autox, spot_group.tag, attrib=spot_group.attrib)
                    new_spot_group.attrib['sampleName'] = f"{new_spot_group.attrib['sampleName']}_{cont.attrib['Pos_on_Scout']}_MSMS"
                    if method_checkbox and os.path.exists(method):
                        new_spot_group.attrib['acqMethod'] = method
                        log += f"{spot_group.attrib['sampleName']} Method: {method}\n"
                    else:
                        new_spot_group.attrib['acqMethod'] = [value['method_path']
                                                              for key, value in autox_path_dict.items()
                                                              if value['sample_name'] == spot_group.attrib['sampleName']][0]
                        log += (f"{spot_group.attrib['sampleName']} Method: " +
                                [value['method_path']
                                 for key, value in autox_path_dict.items()
                                 if value['sample_name'] == spot_group.attrib['sampleName']][0] + '\n')
                    top_n_peaks = pd.DataFrame({'m/z': precursor_data[cont.attrib['Pos_on_Scout']]['peak_picked_mz_array'],
                                                'Intensity': precursor_data[cont.attrib['Pos_on_Scout']]['peak_picked_intensity_array']})
                    top_n_peaks = top_n_peaks.sort_values(by='Intensity', ascending=True).round(4)
                    top_n_peaks = top_n_peaks.drop_duplicates(subset='m/z')
                    top_n_peaks = top_n_peaks['m/z'].values.tolist()
                    for peak in top_n_peaks:
                        new_cont = et.SubElement(new_spot_group, cont.tag, attrib=cont.attrib)
                        new_cont.attrib['acqJobMode'] = 'MSMS'
                        new_cont.attrib['precursor_m_z'] = str(peak)
        new_autox_tree = et.ElementTree(new_autox)
        new_autox_tree.write(os.path.join(outdir, os.path.splitext(os.path.split(autox_seq)[-1])[0]) + '_MALDI_DDA.run',
                             encoding='utf-8',
                             xml_declaration=True,
                             pretty_print=True)
        log += '\nSample Processing Parameters Used for Precursor Selection\n\n'
        log += toml.dumps(sample_params_log) + '\n\n'
        if 'PRECURSOR_SELECTION' in sample_params_log.keys():
            if sample_params_log['PRECURSOR_SELECTION']['use_exclusion_list']:
                log += 'Blank Processing Parameters Used for Exclusion List Generation\n\n'
                log += toml.dumps(blank_params_log) + '\n\n'
                log += 'Exclusion List\n\n'
                log += pd.DataFrame(exclusion_list).to_string(index=False) + '\n'
        with open(os.path.join(outdir,
                               os.path.splitext(os.path.split(autox_seq)[-1])[0]) + '_MALDI_DDA.log', 'w') as logfile:
            logfile.write(log)
        return not run_is_open, not success_is_open


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
