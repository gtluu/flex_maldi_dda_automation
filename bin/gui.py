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
from dash import State, callback_context, no_update, dash_table, MATCH, ALL
from dash_extensions.enrich import Input, Output, DashProxy, MultiplexerTransform, Serverside, ServersideOutputTransform
import dash_bootstrap_components as dbc

# default processing parameters from config file
PREPROCESSING_PARAMS = get_preprocessing_params()
PREPROCESSING_PARAMS['TRIM_SPECTRUM']['run'] = False
PREPROCESSING_PARAMS['TRANSFORM_INTENSITY']['run'] = False
PREPROCESSING_PARAMS['SMOOTH_BASELINE']['run'] = False
PREPROCESSING_PARAMS['REMOVE_BASELINE']['run'] = False
PREPROCESSING_PARAMS['NORMALIZE_INTENSITY']['run'] = False
PREPROCESSING_PARAMS['BIN_SPECTRUM']['run'] = False
config = configparser.ConfigParser()
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
                                         'average2_multiplier': int(config['align_spectra']['average2_multiplier'])}

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

BLANK_SPOTS = []

app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform(), ServersideOutputTransform()],
                external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = get_dashboard_layout(PREPROCESSING_PARAMS, PLATE_FORMAT, AUTOX_PATH_DICT)


# TODO: add callbacks for exclusion list, preview, run buttons
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
              [State({'type': 'raw_data_path_input', 'index': ALL}, 'valid'),
               State({'type': 'method_path_input', 'index': ALL}, 'valid'),
               State('autox_validation_modal', 'is_open')])
def toggle_autox_validation_modal_close(n_clicks, raw_data_path_input_valid, method_path_input_valid, is_open):
    if n_clicks:
        for i, j in zip(raw_data_path_input_valid, method_path_input_valid):
            if not i or not j:
                return is_open
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


"""@ app.callback()
def generate_exclusion_list_from_blank_spots():
    pass"""


@app.callback(Output('exclusion_list', 'data'),
              Input('upload_exclusion_list_from_csv', 'n_clicks'),
              State('exclusion_list', 'data'))
def upload_exclusion_list_from_csv(n_clicks, exclusion_list):
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'upload_exclusion_list_from_csv.n_clicks':
        main_tk_window = tkinter.Tk()
        main_tk_window.attributes('-topmost', True, '-alpha', 0)
        filename = askopenfilename(filetypes=[('Comma Separated Value', '*.csv')])
        main_tk_window.destroy()
        exclusion_list_df = pd.read_csv(filename)
        if exclusion_list_df.shape[1] == 1 and exclusion_list_df.columns[0] == 'm/z':
            return exclusion_list_df.to_dict('records')
        else:
            # TODO: "csv not valid. ensure only one column named m/z is present"
            pass


@app.callback(Output('exclusion_list', 'data'),
              Input('clear_exclusion_list', 'n_clicks'))
def clear_exclusion_list(n_clicks):
    changed_id = [i['prop_id'] for i in callback_context.triggered][0]
    if changed_id == 'clear_exclusion_list.n_clicks':
        return pd.DataFrame(columns=['m/z']).to_dict('records')


# TODO: add preprocessing buttons for flex_maldi_dda_automation parameters (top n precursors, tolerances, etc)
# TODO: move align spectra and exclusion list processing params to new modal when clicking "Generate Exclusion List"
# TODO: preprocessing params modal pops up when clicking "Preview" or "Run"; remove "Edit Preprocessing parameters"
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
               Input('align_spectra_checkbox', 'value'),
               Input('align_spectra_method', 'value'),
               Input('align_spectra_inter', 'value'),
               Input('align_spectra_inter_nint_value', 'value'),
               Input('align_spectra_n', 'value'),
               Input('align_spectra_n_integer_value', 'value'),
               Input('align_spectra_coshift_preprocessing', 'value'),
               Input('align_spectra_coshift_preprocessing_max_shift_value', 'value'),
               Input('align_spectra_fill_with_previous', 'value'),
               Input('align_spectra_average2_multiplier_value', 'value'),
               Input('peak_picking_method', 'value'),
               Input('peak_picking_snr_value', 'value'),
               Input('peak_picking_widths_value', 'value')],
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
                                               align_spectra_checkbox,
                                               align_spectra_method,
                                               align_spectra_inter,
                                               align_spectra_inter_nint_value,
                                               align_spectra_n,
                                               align_spectra_n_integer_value,
                                               align_spectra_coshift_preprocessing,
                                               align_spectra_coshift_preprocessing_max_shift_value,
                                               align_spectra_fill_with_previous,
                                               align_spectra_average2_multiplier_value,
                                               peak_picking_method,
                                               peak_picking_snr,
                                               peak_picking_widths,
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
            PREPROCESSING_PARAMS['ALIGN_SPECTRA']['run'] = align_spectra_checkbox
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
            PREPROCESSING_PARAMS['ALIGN_SPECTRA']['average2_multiplier'] = align_spectra_average2_multiplier_value
            PREPROCESSING_PARAMS['PEAK_PICKING']['method'] = peak_picking_method
            PREPROCESSING_PARAMS['PEAK_PICKING']['snr'] = peak_picking_snr
            PREPROCESSING_PARAMS['PEAK_PICKING']['widths'] = peak_picking_widths
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


@app.callback([Output('align_spectra_method_label', 'style'),
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
def toggle_align_spectra_parameters(n_clicks, align_spectra_checkbox, align_spectra_method, align_spectra_inter, align_spectra_n):
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
        return default_hidden


@app.callback([Output('peak_picking_snr', 'style'),
               Output('peak_picking_widths', 'Style')],
              [Input('edit_preprocessing_parameters', 'n_clicks'),
               Input('peak_picking_method', 'value')])
def toggle_peak_picking_method_parameters(n_clicks, value):
    if value == 'locmax':
        return toggle_locmax_style()
    elif value == 'cwt':
        return toggle_cwt_style()


if __name__ == '__main__':
    app.run_server(debug=False)
