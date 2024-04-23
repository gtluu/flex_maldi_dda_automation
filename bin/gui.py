import os
import gc
import copy
import configparser
import pandas as pd
from lxml import etree as et
from pymaldiproc.data_import import import_mzml, import_timstof_raw_data
from pymaldiproc.preprocessing import align_spectra, get_feature_matrix
from pymaldiviz.util import *
from bin.layout import *
from bin.util import *
from dash import State, callback_context, no_update, dash_table, MATCH, ALL
from dash_extensions.enrich import Input, Output, DashProxy, MultiplexerTransform, Serverside, ServersideOutputTransform
import dash_bootstrap_components as dbc
import plotly.express as px
from plotly_resampler import FigureResampler

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

app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform(), ServersideOutputTransform()],
                external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = get_dashboard_layout(PREPROCESSING_PARAMS, PLATE_FORMAT, AUTOX_PATH_DICT, MS1_AUTOX.attrib['directory'])


@app.callback([Output({'type': 'raw_data_path_input', 'index': MATCH}, 'value'),
               Output({'type': 'raw_data_path_input', 'index': MATCH}, 'valid'),
               Output({'type': 'raw_data_path_input', 'index': MATCH}, 'invalid')],
              [Input({'type': 'raw_data_path_button', 'index': MATCH}, 'n_clicks'),
               Input({'type': 'raw_data_path_button', 'index': MATCH}, 'id')])
def update_raw_data_path(n_clicks, button_id):
    global AUTOX_PATH_DICT
    main_tk_window = tkinter.Tk()
    main_tk_window.attributes('-topmost', True, '-alpha', 0)
    dirname = askdirectory(mustexist=True)
    main_tk_window.destroy()
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
    global AUTOX_PATH_DICT
    main_tk_window = tkinter.Tk()
    main_tk_window.attributes('-topmost', True, '-alpha', 0)
    dirname = askdirectory(mustexist=True)
    main_tk_window.destroy()
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


@app.callback(Output('plate_map', 'style_data_conditional'),
              Input('clear_blank_spots', 'n_clicks'))
def clear_blank_spots(n_clicks):
    global BLANK_SPOTS
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'clear_blank_spots.n_clicks':
        BLANK_SPOTS = []
        return []


# TODO: average unaligned duplicates from replicate blank spots
# TODO: (in pymaldiproc) ion deconvolution in peak picking
# TODO: add a modal window to view blank spot peaks
@ app.callback(Output('exclusion_list', 'data'),
               Input('generate_exclusion_list_from_blank_spots', 'n_clicks'))
def generate_exclusion_list_from_blank_spots(n_clicks):
    global INDEXED_DATA
    global BLANK_SPOTS
    global PREPROCESSING_PARAMS
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'generate_exclusion_list_from_blank_spots.n_clicks':
        blank_spectra = [INDEXED_DATA[spot] for spot in BLANK_SPOTS]
        params = copy.deepcopy(PREPROCESSING_PARAMS)
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
        # undo preprocessing
        for spectrum in blank_spectra:
            spectrum.undo_all_processing()
        return exclusion_list_df.to_dict('records')


@app.callback([Output('exclusion_list', 'data'),
               Output('exclusion_list_csv_error_modal', 'is_open')],
              Input('upload_exclusion_list_from_csv', 'n_clicks'),
              [State('exclusion_list', 'data'),
               State('exclusion_list_csv_error_modal', 'is_open')])
def upload_exclusion_list_from_csv(n_clicks, exclusion_list, exclusion_list_csv_error_modal_is_open):
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
    if n_clicks:
        return not is_open
    return is_open


@app.callback(Output('exclusion_list', 'data'),
              Input('clear_exclusion_list', 'n_clicks'))
def clear_exclusion_list(n_clicks):
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'clear_exclusion_list.n_clicks':
        return pd.DataFrame(columns=['m/z']).to_dict('records')


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
                                               precursor_selection_top_n_value,
                                               precursor_selection_use_exclusion_list,
                                               precursor_selection_exclusion_list_tolerance_value,
                                               is_open):
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
    if n_clicks_save or n_clicks_close:
        return not is_open
    return is_open


@app.callback([Output('trim_spectrum_lower_mass_range', 'style'),
               Output('trim_spectrum_upper_mass_range', 'style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('trim_spectrum_checkbox', 'value')])
def toggle_trim_spectrum_parameters(n_clicks, value):
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
               Output('peak_picking_widths', 'Style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('peak_picking_method', 'value')])
def toggle_peak_picking_method_parameters(n_clicks, value):
    if value == 'locmax':
        return toggle_locmax_style()
    elif value == 'cwt':
        return toggle_cwt_style()


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
    global INDEXED_DATA
    global PREPROCESSING_PARAMS
    global BLANK_SPOTS
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'preview_precursor_list.n_clicks':
        params = copy.deepcopy(PREPROCESSING_PARAMS)
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
    global INDEXED_DATA
    fig = get_spectrum(INDEXED_DATA[value])
    #cleanup_file_system_backend()
    return fig, Serverside(fig)


@app.callback([Output('run_modal', 'is_open'),
               Output('run_success_modal', 'is_open')],
              [Input('preview_precursor_list_modal_run', 'n_clicks'),
               Input('run_button', 'n_clicks')],
              [State('run_modal', 'is_open'),
               State('run_success_modal', 'is_open'),
               State('run_output_directory_value', 'value'),
               State('run_method_value', 'value'),
               State('run_method_checkbox', 'value')])
def toggle_run_modal(preview_run_n_clicks, run_n_clicks, run_is_open, success_is_open, outdir, method, method_checkbox):
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'preview_precursor_list_modal_run.n_clicks':
        return not run_is_open, success_is_open
    if changed_id == 'run_button.n_clicks':
        global MS1_AUTOX
        global AUTOX_PATH_DICT
        global INDEXED_DATA
        global BLANK_SPOTS
        global AUTOX_SEQ
        new_autox = et.Element(MS1_AUTOX.tag, attrib=MS1_AUTOX.attrib)
        new_autox.attrib['directory'] = outdir
        for spot_group in MS1_AUTOX:
            for cont in spot_group:
                if cont.attrib['Pos_on_Scout'] not in BLANK_SPOTS:
                    new_spot_group = et.SubElement(new_autox, spot_group.tag, attrib=spot_group.attrib)
                    new_spot_group.attrib['sampleName'] = f"{new_spot_group.attrib['sampleName']}_{cont.attrib['Pos_on_Scout']}_MSMS"
                    if method_checkbox and os.path.exists(method):
                        new_spot_group.attrib['acqMethod'] = method
                    else:
                        new_spot_group.attrib['acqMethod'] = [value['method_path']
                                                              for key, value in AUTOX_PATH_DICT.items()
                                                              if value['sample_name'] == spot_group.attrib['sampleName']][0]
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
        return not run_is_open, not success_is_open
    return run_is_open, success_is_open


@app.callback(Output('run_success_modal', 'is_open'),
              Input('run_success_close', 'n_clicks'),
              State('run_success_modal', 'is_open'))
def toggle_run_success_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


@app.callback(Output('run_method', 'style'),
              [Input('preview_precursor_list_modal_run', 'n_clicks'),
               Input('run_method_checkbox', 'value')])
def toggle_run_new_method_selection_input(n_clicks, value):
    if value:
        return copy.deepcopy(SHOWN)
    elif not value:
        return copy.deepcopy(HIDDEN)


@app.callback([Output('run_output_directory_value', 'value'),
               Output('run_output_directory_value', 'valid'),
               Output('run_output_directory_value', 'invalid')],
              Input('run_select_output_directory', 'n_clicks'))
def select_new_output_directory(n_clicks):
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'run_select_output_directory.n_clicks':
        main_tk_window = tkinter.Tk()
        main_tk_window.attributes('-topmost', True, '-alpha', 0)
        dirname = askdirectory(mustexist=True)
        main_tk_window.destroy()
        if os.path.exists(dirname):
            return dirname, True, False
        else:
            return dirname, False, True


@app.callback([Output('run_method_value', 'value'),
               Output('run_method_value', 'valid'),
               Output('run_method_value', 'invalid')],
              Input('run_select_method', 'n_clicks'))
def select_new_method_(n_clicks):
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'run_select_method.n_clicks':
        main_tk_window = tkinter.Tk()
        main_tk_window.attributes('-topmost', True, '-alpha', 0)
        dirname = askdirectory(mustexist=True)
        main_tk_window.destroy()
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
    if fig is None:
        return no_update
    return fig.construct_update_data_patch(relayoutdata)


if __name__ == '__main__':
    app.run_server(debug=False)
