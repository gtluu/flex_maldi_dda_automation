import copy
import numpy as np
import pandas as pd
import plotly.express as px
from plotly_resampler import FigureResampler
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from bin.util import *


def get_preprocessing_parameters_layout(param_dict):
    trim_spectrum_parameters = html.Div(
        [
            html.H5('Spectrum Trimming Parameters'),
            dbc.Checkbox(
                id='trim_spectrum_checkbox',
                label='Trim Spectrum',
                value=param_dict['TRIM_SPECTRUM']['run']
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Lower Mass Range'),
                    dbc.Input(id='trim_spectrum_lower_mass_range_value',
                              placeholder=param_dict['TRIM_SPECTRUM']['lower_mass_range'],
                              value=param_dict['TRIM_SPECTRUM']['lower_mass_range'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='trim_spectrum_lower_mass_range',
                style={'margin': '10px'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Upper Mass Range'),
                    dbc.Input(id='trim_spectrum_upper_mass_range_value',
                              placeholder=param_dict['TRIM_SPECTRUM']['upper_mass_range'],
                              value=param_dict['TRIM_SPECTRUM']['upper_mass_range'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='trim_spectrum_upper_mass_range',
                style={'margin': '10px'}
            )
        ],
        id='trim_spectrum_parameters',
        style={'margin': '20px'}
    )

    transform_intensity_parameters = html.Div(
        [
            html.H5('Intensity Transformation Parameters'),
            dbc.Checkbox(
                id='transform_intensity_checkbox',
                label='Transform Intensity',
                value=param_dict['TRANSFORM_INTENSITY']['run']
            ),
            html.P('Method', id='transform_intensity_method_label'),
            dbc.RadioItems(
                id='transform_intensity_method',
                options=[
                    {'label': 'Square Root', 'value': 'sqrt'},
                    {'label': 'Natural Log', 'value': 'log'},
                    {'label': 'Log Base 2', 'value': 'log2'},
                    {'label': 'Log Base 10', 'value': 'log10'}
                ],
                value=param_dict['TRANSFORM_INTENSITY']['method'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            )
        ],
        id='transform_intensity_parameters',
        style={'margin': '20px'}
    )

    smooth_baseline_parameters = html.Div(
        [
            html.H5('Baseline Smoothing Parameters'),
            dbc.Checkbox(
                id='smooth_baseline_checkbox',
                label='Smooth Baseline',
                value=param_dict['SMOOTH_BASELINE']['run']
            ),
            html.P('Method', id='smooth_baseline_method_label'),
            dbc.RadioItems(
                id='smooth_baseline_method',
                options=[
                    {'label': 'Savitzky-Golay', 'value': 'SavitzkyGolay'},
                    {'label': 'Apodization', 'value': 'apodization'},
                    {'label': 'Rebin', 'value': 'rebin'},
                    {'label': 'Fast Change', 'value': 'fast_change'},
                    {'label': 'Median', 'value': 'median'}
                ],
                value=param_dict['SMOOTH_BASELINE']['method'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Window Length'),
                    dbc.Input(id='smooth_baseline_window_length_value',
                              placeholder=param_dict['SMOOTH_BASELINE']['window_length'],
                              value=param_dict['SMOOTH_BASELINE']['window_length'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='smooth_baseline_window_length',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Polyorder'),
                    dbc.Input(id='smooth_baseline_polyorder_value',
                              placeholder=param_dict['SMOOTH_BASELINE']['polyorder'],
                              value=param_dict['SMOOTH_BASELINE']['polyorder'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='smooth_baseline_polyorder',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Delta m/z'),
                    dbc.Input(id='smooth_baseline_delta_mz_value',
                              placeholder=param_dict['SMOOTH_BASELINE']['delta_mz'],
                              value=param_dict['SMOOTH_BASELINE']['delta_mz'],
                              type='number',
                              min=0,
                              step=0.001)
                ],
                id='smooth_baseline_delta_mz',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Difference Threshold'),
                    dbc.Input(id='smooth_baseline_diff_thresh_value',
                              placeholder=param_dict['SMOOTH_BASELINE']['diff_thresh'],
                              value=param_dict['SMOOTH_BASELINE']['diff_thresh'],
                              type='number',
                              min=0,
                              step=0.001)
                ],
                id='smooth_baseline_diff_thresh',
                style={'margin': '10px',
                       'display': 'flex'}
            )
        ],
        id='smooth_baseline_parameters',
        style={'margin': '20px'}
    )

    remove_baseline_parameters = html.Div(
        [
            html.H5('Baseline Removal Parameters'),
            dbc.Checkbox(
                id='remove_baseline_checkbox',
                label='Remove Baseline',
                value=param_dict['REMOVE_BASELINE']['run']
            ),
            html.P('Method', id='remove_baseline_method_label'),
            dbc.RadioItems(
                id='remove_baseline_method',
                options=[
                    {'label': 'SNIP', 'value': 'SNIP'},
                    {'label': 'Top Hat', 'value': 'TopHat'},
                    {'label': 'Median', 'value': 'Median'},
                    {'label': 'Zhang Fit', 'value': 'ZhangFit'},
                    {'label': 'ModPoly', 'value': 'ModPoly'},
                    {'label': 'IModPoly', 'value': 'IModPoly'}
                ],
                value=param_dict['REMOVE_BASELINE']['method'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.RadioItems(
                id='remove_baseline_decreasing',
                options=[
                    {'label': 'Use Decreasing Iterative Window Sizes', 'value': True},
                    {'label': 'Do Not Use Decreasing Iterative Window Sizes', 'value': False}
                ],
                value=param_dict['REMOVE_BASELINE']['decreasing'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Minimum Half Window'),
                    dbc.Input(id='remove_baseline_min_half_window_value',
                              placeholder=param_dict['REMOVE_BASELINE']['max_half_window'],
                              value=param_dict['REMOVE_BASELINE']['max_half_window'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_min_half_window',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Maximum Half Window'),
                    dbc.Input(id='remove_baseline_max_half_window_value',
                              placeholder=param_dict['REMOVE_BASELINE']['max_half_window'],
                              value=param_dict['REMOVE_BASELINE']['max_half_window'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_max_half_window',

                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Smoothing Half Window'),
                    dbc.Input(id='remove_baseline_smooth_half_window_value',
                              placeholder=param_dict['REMOVE_BASELINE']['smooth_half_window'],
                              value=param_dict['REMOVE_BASELINE']['smooth_half_window'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_smooth_half_window',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Filter Order'),
                    dbc.Input(id='remove_baseline_filter_order_value',
                              placeholder=param_dict['REMOVE_BASELINE']['filter_order'],
                              value=param_dict['REMOVE_BASELINE']['filter_order'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_filter_order',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Sigma'),
                    dbc.Input(id='remove_baseline_sigma_value',
                              placeholder=param_dict['REMOVE_BASELINE']['sigma'],
                              value=param_dict['REMOVE_BASELINE']['sigma'],
                              type='number',
                              min=0,
                              step=0.001)
                ],
                id='remove_baseline_sigma',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Increment'),
                    dbc.Input(id='remove_baseline_increment_value',
                              placeholder=param_dict['REMOVE_BASELINE']['increment'],
                              value=param_dict['REMOVE_BASELINE']['increment'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_increment',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Max Hits'),
                    dbc.Input(id='remove_baseline_max_hits_value',
                              placeholder=param_dict['REMOVE_BASELINE']['max_hits'],
                              value=param_dict['REMOVE_BASELINE']['max_hits'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_max_hits',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Window Tolerance'),
                    dbc.Input(id='remove_baseline_window_tol_value',
                              placeholder=param_dict['REMOVE_BASELINE']['window_tol'],
                              value=param_dict['REMOVE_BASELINE']['window_tol'],
                              type='number',
                              min=0,
                              step=0.000001)
                ],
                id='remove_baseline_window_tol',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Lambda'),
                    dbc.Input(id='remove_baseline_lambda__value',
                              placeholder=param_dict['REMOVE_BASELINE']['lambda_'],
                              value=param_dict['REMOVE_BASELINE']['lambda_'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_lambda_',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('p-order'),
                    dbc.Input(id='remove_baseline_porder_value',
                              placeholder=param_dict['REMOVE_BASELINE']['porder'],
                              value=param_dict['REMOVE_BASELINE']['porder'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_porder',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Repetition'),
                    dbc.Input(id='remove_baseline_repetition_value',
                              placeholder=param_dict['REMOVE_BASELINE']['repetition'],
                              value=param_dict['REMOVE_BASELINE']['repetition'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_repetition',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Degree'),
                    dbc.Input(id='remove_baseline_degree_value',
                              placeholder=param_dict['REMOVE_BASELINE']['degree'],
                              value=param_dict['REMOVE_BASELINE']['degree'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='remove_baseline_degree',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Gradient'),
                    dbc.Input(id='remove_baseline_gradient_value',
                              placeholder=param_dict['REMOVE_BASELINE']['gradient'],
                              value=param_dict['REMOVE_BASELINE']['gradient'],
                              type='number',
                              min=0,
                              step=0.001)
                ],
                id='remove_baseline_gradient',
                style={'margin': '10px',
                       'display': 'flex'}
            )
        ],
        id='remove_baseline_parameters',
        style={'margin': '20px'}
    )

    normalize_intensity_parameters = html.Div(
        [
            html.H5('Intensity Normalization Parameters'),
            dbc.Checkbox(
                id='normalize_intensity_checkbox',
                label='Normalize Intensity',
                value=param_dict['NORMALIZE_INTENSITY']['run']
            ),
            html.P('Method', id='normalize_intensity_method_label'),
            dbc.RadioItems(
                id='normalize_intensity_method',
                options=[
                    {'label': 'Total Ion Count', 'value': 'tic'},
                    {'label': 'Root Mean Square', 'value': 'rms'},
                    {'label': 'Mean Absolute Deviation', 'value': 'mad'},
                    {'label': 'Square Root', 'value': 'sqrt'}
                ],
                value=param_dict['NORMALIZE_INTENSITY']['method'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            )
        ],
        id='normalize_intensity_parameters',
        style={'margin': '20px'}
    )

    bin_spectrum_parameters = html.Div(
        [
            html.H5('Spectrum Binning Parameters'),
            dbc.Checkbox(
                id='bin_spectrum_checkbox',
                label='Bin Spectrum',
                value=param_dict['BIN_SPECTRUM']['run']
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Number of Bins'),
                    dbc.Input(id='bin_spectrum_n_bins_value',
                              placeholder=param_dict['BIN_SPECTRUM']['n_bins'],
                              value=param_dict['BIN_SPECTRUM']['n_bins'],
                              type='number',
                              min=0,
                              step=100)
                ],
                id='bin_spectrum_n_bins',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Lower Mass Range'),
                    dbc.Input(id='bin_spectrum_lower_mass_range_value',
                              placeholder=param_dict['BIN_SPECTRUM']['lower_mass_range'],
                              value=param_dict['BIN_SPECTRUM']['lower_mass_range'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='bin_spectrum_lower_mass_range',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Upper Mass Range'),
                    dbc.Input(id='bin_spectrum_upper_mass_range_value',
                              placeholder=param_dict['BIN_SPECTRUM']['upper_mass_range'],
                              value=param_dict['BIN_SPECTRUM']['upper_mass_range'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='bin_spectrum_upper_mass_range',
                style={'margin': '10px',
                       'display': 'flex'}
            )
        ],
        id='bin_spectrum_parameters',
        style={'margin': '20px'}
    )

    """align_spectra_parameters = html.Div(
        [
            html.H5('Spectra Alignment Parameters (Only Used for Exclusion List Generation from Blank Spots)'),
            dbc.Checkbox(
                id='align_spectra_checkbox',
                label='Align Spectra (Only Used for Exclusion List Generation from Blank Spots)',
                value=param_dict['ALIGN_SPECTRA']['run']
            ),
            html.P('Method', id='align_spectra_method_label'),
            dbc.RadioItems(
                id='align_spectra_method',
                options=[
                    {'label': 'Average', 'value': 'average'},
                    {'label': 'Median', 'value': 'median'},
                    {'label': 'Max', 'value': 'max'},
                    {'label': 'Average2', 'value': 'average2'}
                ],
                value=param_dict['ALIGN_SPECTRA']['method'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            html.P('Definition of Alignment Mode', id='align_spectra_inter_label'),
            dbc.RadioItems(
                id='align_spectra_inter',
                options=[
                    {'label': 'Whole', 'value': 'whole'},
                    {'label': 'Number of Many Intervals', 'value': 'nint'},
                    {'label': 'Length of Regular Intervals', 'value': 'ndata'}
                ],
                value=param_dict['ALIGN_SPECTRA']['inter'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Number of Many Intervals'),
                    dbc.Input(id='align_spectra_inter_nint_value',
                              placeholder=100,
                              value=100,
                              type='number',
                              min=1,
                              step=1)
                ],
                id='align_spectra_inter_nint',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            html.P('n for Each Interval', id='align_spectra_n_label'),
            dbc.RadioItems(
                id='align_spectra_n',
                options=[
                    {'label': 'Fast', 'value': 'f'},
                    {'label': 'Best', 'value': 'b'},
                    {'label': 'Integer', 'value': 'integer'}
                ],
                value=param_dict['ALIGN_SPECTRA']['n'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Maximum Shift Correction in Data Points/Scale Units'),
                    dbc.Input(id='align_spectra_n_integer_value',
                              placeholder=1,
                              value=1,
                              type='number',
                              min=1,
                              step=1)
                ],
                id='align_spectra_n_integer',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            # skipping scale parameter
            dbc.RadioItems(
                id='align_spectra_coshift_preprocessing',
                options=[
                    {'label': 'Execute Co-Shift Step Before Alignment', 'value': True},
                    {'label': 'Do Not Perform Co-Shift Step', 'value': False}
                ],
                value=param_dict['ALIGN_SPECTRA']['coshift_preprocessing'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Co-Shift Preprocessing Max Shift'),
                    dbc.Input(id='align_spectra_coshift_preprocessing_max_shift_value',
                              placeholder=param_dict['ALIGN_SPECTRA']['coshift_preprocessing_max_shift'],
                              value=param_dict['ALIGN_SPECTRA']['coshift_preprocessing_max_shift'],
                              type='number',
                              min=1,
                              step=1)
                ],
                id='align_spectra_coshift_preprocessing_max_shift',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='align_spectra_fill_with_previous',
                options=[
                    {'label': 'Fill with Previous Point', 'value': True},
                    {'label': 'Set to NaN', 'value': False}
                ],
                value=param_dict['ALIGN_SPECTRA']['fill_with_previous'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Average2 Multiplier'),
                    dbc.Input(id='align_spectra_average2_multiplier_value',
                              placeholder=param_dict['ALIGN_SPECTRA']['average2_multiplier'],
                              value=param_dict['ALIGN_SPECTRA']['average2_multiplier'],
                              type='number',
                              min=1,
                              step=1)
                ],
                id='align_spectra_average2_multiplier',
                style={'margin': '10px',
                       'display': 'flex'}
            )
        ],
        id='align_spectra_parameters',
        style={'margin': '20px'}
    )"""

    peak_picking_parameters = html.Div(
        [
            html.H5('Peak Picking Parameters'),
            html.P('Method'),
            dbc.RadioItems(
                id='peak_picking_method',
                options=[
                    {'label': 'Local Maxima', 'value': 'locmax'},
                    {'label': 'Continuous Wavelet Transform', 'value': 'cwt'}
                ],
                value=param_dict['PEAK_PICKING']['method'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Signal-to-Noise Ratio'),
                    dbc.Input(id='peak_picking_snr_value',
                              placeholder=param_dict['PEAK_PICKING']['snr'],
                              value=param_dict['PEAK_PICKING']['snr'],
                              type='number',
                              min=0,
                              step=1)
                ],
                id='peak_picking_snr',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Widths (Optional)'),
                    dbc.Input(id='peak_picking_widths_value',
                              placeholder=param_dict['PEAK_PICKING']['widths'],
                              value=param_dict['PEAK_PICKING']['widths'],
                              type='number',
                              min=0,
                              step=0.001)
                ],
                id='peak_picking_widths',
                style={'margin': '10px',
                       'display': 'flex'}
            )
        ],
        id='peak_picking_parameters',
        style={'margin': '20px'}
    )

    return [trim_spectrum_parameters,
            transform_intensity_parameters,
            smooth_baseline_parameters,
            remove_baseline_parameters,
            normalize_intensity_parameters,
            bin_spectrum_parameters,
            #align_spectra_parameters,
            peak_picking_parameters]


def get_autox_validation_modal_layout(autox_path_dict):
    modal_divs = []
    # check if data and methods exist
    for index, path_dict in autox_path_dict.items():
        modal_divs.append(
            html.H5(path_dict['sample_name'])
        )
        if os.path.exists(path_dict['raw_data_path']):
            modal_divs.append(
                dbc.InputGroup(
                    [
                        dbc.InputGroupText('Raw Data Path'),
                        dbc.Input(id={'type': 'raw_data_path_input', 'index': index},
                                  placeholder=path_dict['raw_data_path'],
                                  value=path_dict['raw_data_path'],
                                  readonly=True,
                                  type='text',
                                  valid=True)
                    ],
                    style={'margin': '10px',
                           'display': 'flex'}
                )
            )
        elif not os.path.exists(path_dict['raw_data_path']):
            modal_divs.append(
                dbc.InputGroup(
                    [
                        dbc.InputGroupText('Raw Data Path'),
                        dbc.Input(id={'type': 'raw_data_path_input', 'index': index},
                                  placeholder=path_dict['raw_data_path'],
                                  value=path_dict['raw_data_path'],
                                  readonly=True,
                                  type='text',
                                  invalid=True),
                        dbc.Button('Update Raw Data Path', id={'type': 'raw_data_path_button', 'index': index})
                    ],
                    style={'margin': '10px',
                           'display': 'flex'}
                )
            )
        if os.path.exists(path_dict['method_path']):
            modal_divs.append(
                dbc.InputGroup(
                    [
                        dbc.InputGroupText('Method Path'),
                        dbc.Input(id={'type': 'method_path_input', 'index': index},
                                  placeholder=path_dict['method_path'],
                                  value=path_dict['method_path'],
                                  readonly=True,
                                  type='text',
                                  valid=True)
                    ],
                    style={'margin': '10px',
                           'display': 'flex'}
                )
            )
        elif not os.path.exists(path_dict['method_path']):
            modal_divs.append(
                dbc.InputGroup(
                    [
                        dbc.InputGroupText('Method Path'),
                        dbc.Input(id={'type': 'method_path_input', 'index': index},
                                  placeholder=path_dict['method_path'],
                                  value=path_dict['method_path'],
                                  readonly=True,
                                  type='text',
                                  invalid=True),
                        dbc.Button('Update Method Path', id={'type': 'method_path_button', 'index': index})
                    ],
                    style={'margin': '10px',
                           'display': 'flex'}
                )
            )
    return modal_divs


def get_exclusion_list_layout():
    return [
        dash_table.DataTable(
            data=[],
            columns=[{'name': 'm/z', 'id': 'm/z'}],
            id='exclusion_list',
            style_data_conditional=[],
            page_size=10
        ),
        dbc.Button('Generate Exclusion List from Blank Spots',
                   id='generate_exclusion_list_from_blank_spots'),
        dbc.Button('Upload Exclusion List from CSV', id='upload_exclusion_list_from_csv'),
        dbc.Button('Clear Exclusion List', id='clear_exclusion_list'),
    ]


def get_dashboard_layout(param_dict, plate_format, autox_path_dict):
    df = get_plate_map(plate_format)
    return html.Div(
        [
            html.Div(
                # TODO: add legend for blank
                [
                    # TODO: should have grayed out theme for spots that were not found in the .run file
                    dash_table.DataTable(
                        df.to_dict('records'),
                        columns=[{'name': str(col), 'id': str(col)} for col in df.columns],
                        id='plate_map',
                        style_header={'display': 'none'},
                        style_data_conditional=[]
                    ),
                    dbc.Button(
                        'Mark Spots as Blank',
                        id='mark_spot_as_blank',
                        style={'margin': '20px',
                               'display': 'flex',
                               'justify-content': 'center'}
                    ),
                    dbc.Button(
                        'Clear Blank Spots',
                        id='clear_blank_spots',
                        style={'margin': '20px',
                               'display': 'flex',
                               'justify-content': 'center'}
                    )
                ],
                id='plate_map_div',
                className='one column',
                style={'width': '97%',
                       'margin': '20px'}
            ),
            html.Div(
                get_exclusion_list_layout(),
                id='exclusion_list_div',
                className='one column',
                style={'width': '97%',
                       'margin': '20px'}
            ),
            html.Div(
                [
                    dbc.Button('Edit Preprocessing Parameters', id='edit_preprocessing_parameters'),
                    dbc.Button('Preview Precursor List', id='preview_precursor_list'),
                    dbc.Button('Run', id='run')
                ]
            ),
            html.Div(
                id='spectrum',
                className='one column',
                style={'width': '97%',
                       'margin': '20px'}
            ),
            dcc.Loading(
                dcc.Store(id='store_plot')
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('Loaded AutoXecute Sequence'), close_button=False),
                    dbc.ModalBody(get_autox_validation_modal_layout(autox_path_dict)),
                    dbc.ModalFooter(dbc.Button('Close',
                                               id='autox_validation_modal_close',
                                               className='ms-auto'))
                ],
                id='autox_validation_modal',
                fullscreen=True,
                backdrop='static',
                keyboard=False,
                scrollable=True,
                centered=True,
                is_open=True
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('Preprocessing Parameters')),
                    dbc.ModalBody(get_preprocessing_parameters_layout(param_dict)),
                    dbc.ModalFooter(
                        dbc.ButtonGroup(
                            [
                                dbc.Button('Cancel', id='edit_processing_parameters_cancel', className='ms-auto'),
                                dbc.Button('Save', id='edit_processing_parameters_save', className='ms-auto')
                            ]
                        )
                    )
                ],
                id='edit_processing_parameters_modal',
                fullscreen=True,
                backdrop='static',
                scrollable=True,
                centered=True,
                is_open=False
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('Preprocessing parameters have been saved.')),
                    dbc.ModalFooter(dbc.Button('Close',
                                               id='edit_processing_parameters_modal_saved_close',
                                               className='ms-auto'))
                ],
                id='edit_processing_parameters_modal_saved',
                size='lg',
                centered=True,
                is_open=False
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('Error')),
                    dbc.ModalBody('Selected CSV file is not valid. Ensure only one column named "m/z" is present.'),
                    dbc.ModalFooter(dbc.Button('Close',
                                               id='exclusion_list_csv_error_modal_close',
                                               className='ms-auto'))
                ],
                id='exclusion_list_csv_error_modal',
                size='lg',
                centered=True,
                is_open=False
            )
        ],
        className='row',
        style={'justify-content': 'center',
               'display': 'flex'}
    )
