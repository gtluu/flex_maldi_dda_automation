# The following code has been modified from pyMALDIproc and pyMALDIviz.
# For more infromation, see: https://github.com/gtluu/pyMALDIproc


import os
from lxml import etree as et
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from pymaldiviz.util import blank_figure
from msms_autox_generator.util import (get_plate_map, get_plate_map_legend, get_plate_map_style,
                                       get_maldi_dda_preprocessing_params, get_geometry_format, get_autox_path_dict)


def get_preprocessing_parameters_layout(param_dict):
    """
    Obtain the layout for the preprocessing parameters modal window body.

    :param param_dict: Dictionary of parameters used to populate default values.
    :return: List of divs containing the layout for the preprocessing parameters modal window.
    """
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
            ),
            dbc.RadioItems(
                id='peak_picking_deisotope',
                options=[
                    {'label': 'Deisotope Peak List', 'value': True},
                    {'label': 'Do Not Deisotope', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['deisotope'],
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
                    dbc.InputGroupText('Deisotoping Fragment Tolerance'),
                    dbc.Input(id='peak_picking_deisotope_fragment_tolerance_value',
                              placeholder=param_dict['PEAK_PICKING']['fragment_tolerance'],
                              value=param_dict['PEAK_PICKING']['fragment_tolerance'],
                              type='number',
                              min=0,
                              step=0.0001)
                ],
                id='peak_picking_deisotope_fragment_tolerance',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            html.P('Deisotoping Fragment_Tolerance Unit',
                   id='peak_picking_deisotope_fragment_unit_ppm_label',
                   style={'margin': '10px',
                          'display': 'flex'}),
            dbc.RadioItems(
                id='peak_picking_deisotope_fragment_unit_ppm',
                options=[
                    {'label': 'PPM', 'value': True},
                    {'label': 'Da', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['fragment_unit_ppm'],
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
                    dbc.InputGroupText('Deisotoping Minimum Charge'),
                    dbc.Input(id='peak_picking_deisotope_min_charge_value',
                              placeholder=param_dict['PEAK_PICKING']['min_charge'],
                              value=param_dict['PEAK_PICKING']['min_charge'],
                              type='number',
                              min=1,
                              step=1)
                ],
                id='peak_picking_deisotope_min_charge',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Deisotoping Maximum Charge'),
                    dbc.Input(id='peak_picking_deisotope_max_charge_value',
                              placeholder=param_dict['PEAK_PICKING']['max_charge'],
                              value=param_dict['PEAK_PICKING']['max_charge'],
                              type='number',
                              min=1,
                              step=1)
                ],
                id='peak_picking_deisotope_max_charge',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='peak_picking_deisotope_keep_only_deisotoped',
                options=[
                    {'label': 'Retain Only Deisotoped Peaks', 'value': True},
                    {'label': 'Retain Monoisotopic and All Other Peaks', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['keep_only_deisotoped'],
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
                    dbc.InputGroupText('Deisotoping Minimum Number of Isotopic Peaks'),
                    dbc.Input(id='peak_picking_deisotope_min_isopeaks_value',
                              placeholder=param_dict['PEAK_PICKING']['min_isopeaks'],
                              value=param_dict['PEAK_PICKING']['min_isopeaks'],
                              type='number',
                              min=2,
                              step=1)
                ],
                id='peak_picking_deisotope_min_isopeaks',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Deisotoping Maximum Number of Isotopic Peaks'),
                    dbc.Input(id='peak_picking_deisotope_max_isopeaks_value',
                              placeholder=param_dict['PEAK_PICKING']['max_isopeaks'],
                              value=param_dict['PEAK_PICKING']['max_isopeaks'],
                              type='number',
                              min=2,
                              step=1)
                ],
                id='peak_picking_deisotope_max_isopeaks',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='peak_picking_deisotope_make_single_charged',
                options=[
                    {'label': 'Convert Deisotoped Monoisotopic Peak to Single Charge', 'value': True},
                    {'label': 'Retain Original Charge', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['make_single_charged'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='peak_picking_deisotope_annotate_charge',
                options=[
                    {'label': 'Annotate Charge', 'value': True},
                    {'label': 'Do Not Annotate Charge', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['annotate_charge'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='peak_picking_deisotope_annotate_iso_peak_count',
                options=[
                    {'label': 'Annotate Number of Isotopic Peaks', 'value': True},
                    {'label': 'Do Not Annotate Number of Isotopic Peaks', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['annotate_iso_peak_count'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='peak_picking_deisotope_use_decreasing_model',
                options=[
                    {'label': 'Use Decreasing/Averagine Model', 'value': True},
                    {'label': 'Do Not Perform Peak Intensity Check', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['use_decreasing_model'],
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
                    dbc.InputGroupText('Deisotoping Intensity Check Starting Peak'),
                    dbc.Input(id='peak_picking_deisotope_start_intensity_check_value',
                              placeholder=param_dict['PEAK_PICKING']['start_intensity_check'],
                              value=param_dict['PEAK_PICKING']['start_intensity_check'],
                              type='number',
                              min=1,
                              step=1)
                ],
                id='peak_picking_deisotope_start_intensity_check',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='peak_picking_deisotope_add_up_intensity',
                options=[
                    {'label': 'Sum Isotopic Pattern Intensities Into Monoisotopic Peak', 'value': True},
                    {'label': 'Do Not Sum Intensities', 'value': False}
                ],
                value=param_dict['PEAK_PICKING']['add_up_intensity'],
                labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
                style={'margin': '10px',
                       'display': 'flex'}
            )
        ],
        id='peak_picking_parameters',
        style={'margin': '20px'}
    )

    precursor_selection_parameters = html.Div(
        [
            html.H5('Precursor Selection Parameters'),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Number of Precursors per Spot'),
                    dbc.Input(id='precursor_selection_top_n_value',
                              placeholder=param_dict['PRECURSOR_SELECTION']['top_n'],
                              value=param_dict['PRECURSOR_SELECTION']['top_n'],
                              type='number',
                              min=1,
                              step=1)
                ],
                id='precursor_selection_top_n',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.RadioItems(
                id='precursor_selection_use_exclusion_list',
                options=[
                    {'label': 'Use Exclusion List', 'value': True},
                    {'label': 'Ignore Exclusion List', 'value': False}
                ],
                value=param_dict['PRECURSOR_SELECTION']['use_exclusion_list'],
                labelStyle={'display': 'inline-block', 'marginRgiht': '20px'},
                inputStyle={'margin-right': '10px'},
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary',
                labelCheckedClassName='active',
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Exclusion List Tolerance (Da)'),
                    dbc.Input(id='precursor_selection_exclusion_list_tolerance_value',
                              placeholder=param_dict['PRECURSOR_SELECTION']['exclusion_list_tolerance'],
                              value=param_dict['PRECURSOR_SELECTION']['exclusion_list_tolerance'],
                              type='number',
                              min=0)
                ],
                id='precursor_selection_exclusion_list_tolerance',
                style={'margin': '10px',
                       'display': 'flex'}
            )
        ],
        id='precursor_selection_parameters',
        style={'margin': '20px'}
    )

    return [trim_spectrum_parameters,
            transform_intensity_parameters,
            smooth_baseline_parameters,
            remove_baseline_parameters,
            normalize_intensity_parameters,
            bin_spectrum_parameters,
            peak_picking_parameters,
            precursor_selection_parameters]


def get_autox_validation_modal_layout(autox_path_dict):
    """
    Obtain the layout for the AutoXecute sequence data/method path validation modal window body.

    :param autox_path_dict: Nested dictionary containing spot group sample names, data paths, and method paths from the
        .run file.
    :return: List of divs containing the layout for the validation modal window.
    """
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


def get_run_layout(outdir):
    """
    Obtain the layout for the MS/MS AutoXecute generation parameters modal window body.

    :param outdir: Path to folder in which to write the output AutoXecute sequence. Will also be used as the directory
        for the resulting AutoXecute data.
    :return: List of divs containing the layout for the MS/MS AutoXecute generation parameters modal window.
    """
    if os.path.exists(outdir):
        return [
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Output Directory'),
                    dbc.Input(id='run_output_directory_value',
                              placeholder=outdir,
                              value=outdir,
                              readonly=True,
                              type='text',
                              valid=True),
                    dbc.Button('...', id='run_select_output_directory')
                ],
                id='run_output_directory',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.Checkbox(
                id='run_method_checkbox',
                label='Use a new MS/MS method for the generated AutoXecute sequence',
                value=False,
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('MS/MS Method'),
                    dbc.Input(id='run_method_value',
                              placeholder='',
                              value='',
                              readonly=True,
                              type='text'),
                    dbc.Button('...', id='run_select_method')
                ],
                id='run_method',
                style={'margin': '10px',
                       'display': 'none'}
            )
        ]
    else:
        return [
            dbc.InputGroup(
                [
                    dbc.InputGroupText('Output Directory'),
                    dbc.Input(id='run_output_directory_value',
                              placeholder=outdir,
                              value=outdir,
                              readonly=True,
                              type='text',
                              invalid=True),
                    dbc.Button('...', id='run_select_output_directory')
                ],
                id='run_output_directory',
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.Checkbox(
                id='run_method_checkbox',
                label='Use a new MS/MS method for the generated AutoXecute sequence',
                value=False,
                style={'margin': '10px',
                       'display': 'flex'}
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText('MS/MS Method'),
                    dbc.Input(id='run_method_value',
                              placeholder='',
                              value='',
                              readonly=True,
                              type='text'),
                    dbc.Button('...', id='run_select_method')
                ],
                id='run_method',
                style={'margin': '10px',
                       'display': 'none'}
            )
        ]


def get_exclusion_list_layout():
    """
    Obtain the layout for the exclusion list section of the main dashboard.

    :return: List of divs containing the layout for the exclusion list section of the main dashboard.
    """
    return


def get_exclusion_list_spectra_layout():
    """
    Obtain the layout for the blank spectra viewing modal window body. Blank spectra available are those used to
    generate the exclusion list.

    :return: List of spectraum spot name dropdown and figure elements.
    """
    return [
        dcc.Dropdown(
            id='exclusion_list_blank_spectra_id',
            multi=False,
            options=[],
            value=[],
            style={'width': '97%',
                   'margin': '20px'}
        ),
        dcc.Graph(
            id='exclusion_list_blank_spectra_figure',
            figure=blank_figure(),
            style={'width': '100%',
                   'height': '1000px'}
        )
    ]


def get_preview_layout():
    """
    Obtain the layout for the sample spectra preview modal window body.

    :return: List of spectrum spot name dropdown and figure elements.
    """
    return [
        dcc.Dropdown(
            id='preview_id',
            multi=False,
            options=[],
            value=[],
            style={'width': '97%',
                   'margin': '20px'}
        ),
        dcc.Graph(
            id='preview_figure',
            figure=blank_figure(),
            style={'width': '100%',
                   'height': '1000px'}
        )
    ]


def get_dashboard_layout(param_dict, plate_format, autox_path_dict, autox_seq):
    """
    Obtain the main dashboard layout.

    :param param_dict: Dictionary of parameters used to populate default values.
    :param plate_format: Plate geometry used to generate the plate map table.
    :param autox_path_dict: Nested dictionary containing spot group sample names, data paths, and method paths from the
        .run file.
    :param autox_seq: AutoXecute sequence file path.
    :return: Div containing the main dashboard layout.
    """
    autox = et.parse(autox_seq).getroot()
    outdir = autox.attrib['directory']
    plate_map_df = get_plate_map(plate_format)
    plate_map_legend_df = get_plate_map_legend()
    return html.Div(
        [
            dcc.Loading(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dash_table.DataTable(
                                    plate_map_df.to_dict('records'),
                                    columns=[{'name': str(col), 'id': str(col)} for col in plate_map_df.columns],
                                    id='plate_map',
                                    style_header={'display': 'none',
                                                  'textAlign': 'center'},
                                    style_cell={'textAlign': 'center'},
                                    style_data_conditional=get_plate_map_style(plate_map_df, autox)
                                ),
                                width=9
                            ),
                            dbc.Col(
                                dash_table.DataTable(
                                    plate_map_legend_df.to_dict('records'),
                                    columns=[{'name': str(col), 'id': str(col)} for col in
                                             plate_map_legend_df.columns],
                                    id='plate_map_legend',
                                    style_header={'display': 'none',
                                                  'textAlign': 'center'},
                                    style_cell={'textAlign': 'center'},
                                    style_data_conditional=[{'if': {'row_index': 1},
                                                             'backgroundColor': 'green', 'color': 'white'},
                                                            {'if': {'row_index': 2},
                                                             'backgroundColor': 'gray', 'color': 'white'}]
                                ),
                                width=1
                            ),
                            dbc.Col(
                                dash_table.DataTable(
                                    data=[],
                                    columns=[{'name': 'm/z', 'id': 'm/z'}],
                                    id='exclusion_list',
                                    row_deletable=True,
                                    style_header={'textAlign': 'center'},
                                    style_cell={'textAlign': 'center'},
                                    style_data_conditional=[],
                                    page_size=10
                                ),
                                width=2
                            )
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    'Group Selected Spots',
                                    id='group_spots',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            ),
                            dbc.Col(
                                dbc.Button(
                                    'Mark Selected Spots as Blank',
                                    id='mark_spot_as_blank',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            ),
                            dbc.Col(
                                dbc.Button(
                                    'Clear Selected Groups',
                                    id='clear_selected_groups',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            ),
                            dbc.Col(
                                dbc.Button(
                                    'Clear All Blank Spots and Spot Groups',
                                    id='clear_blanks_and_groups',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            )
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    'Generate Exclusion List from Blank Spots',
                                    id='generate_exclusion_list_from_blank_spots',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            ),
                            dbc.Col(
                                dbc.Button(
                                    'View Blank Spectra Used to Generate Exclusion List',
                                    id='view_exclusion_list_spectra',
                                    style={'margin': '20px',
                                           'display': 'none',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            ),
                            dbc.Col(
                                dbc.Button(
                                    'Upload Exclusion List from CSV',
                                    id='upload_exclusion_list_from_csv',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            ),
                            dbc.Col(
                                dbc.Button(
                                    'Clear Exclusion List',
                                    id='clear_exclusion_list',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            )
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    'Edit Preprocessing Parameters',
                                    id='edit_preprocessing_parameters',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width={'size': 3, 'offset': 3}
                            ),
                            dbc.Col(
                                dbc.Button(
                                    'Preview Precursor List',
                                    id='preview_precursor_list',
                                    style={'margin': '20px',
                                           'display': 'flex',
                                           'justify-content': 'center',
                                           'width': '95%'}
                                ),
                                width=3
                            )
                        ]
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
                                        dbc.Button('Cancel',
                                                   id='edit_processing_parameters_cancel',
                                                   className='ms-auto'),
                                        dbc.Button('Save',
                                                   id='edit_processing_parameters_save',
                                                   className='ms-auto')
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
                            dbc.ModalHeader(dbc.ModalTitle('New Group Name')),
                            dbc.ModalBody(
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText('Name'),
                                        dbc.Input(id='new_group_name_modal_input_value',
                                                  placeholder='',
                                                  value='',
                                                  type='text',
                                                  invalid=True)
                                    ],
                                    id='new_group_name_modal_input',
                                    style={'margin': '10px',
                                           'display': 'flex'}
                                )
                            ),
                            dbc.ModalFooter(dbc.Button('Save',
                                                       id='new_group_name_modal_save',
                                                       className='ms-auto'))
                        ],
                        id='new_group_name_modal',
                        size='lg',
                        centered=True,
                        is_open=False
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle('Error')),
                            dbc.ModalBody(
                                'One or more of the selected spots already belongs to a different group.'),
                            dbc.ModalFooter(
                                dbc.Button('Close',
                                           id='group_spots_error_modal_close',
                                           className='ms-auto')
                            )
                        ],
                        id='group_spots_error_modal',
                        size='lg',
                        centered=True,
                        is_open=False
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle('Blank Spectra Used to Generate Exclusion List')),
                            dbc.ModalBody(get_exclusion_list_spectra_layout()),
                            dbc.ModalFooter(dbc.Button('Close',
                                                       id='exclusion_list_blank_spectra_modal_close'))
                        ],
                        id='exclusion_list_blank_spectra_modal',
                        fullscreen=True,
                        backdrop='static',
                        scrollable=True,
                        centered=True,
                        is_open=False
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle('Error')),
                            dbc.ModalBody(
                                'Selected CSV file is not valid. Ensure only one column named "m/z" is present.'),
                            dbc.ModalFooter(dbc.Button('Close',
                                                       id='exclusion_list_csv_error_modal_close',
                                                       className='ms-auto'))
                        ],
                        id='exclusion_list_csv_error_modal',
                        size='lg',
                        centered=True,
                        is_open=False
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle('Preview Precursor List')),
                            dbc.ModalBody(get_preview_layout()),
                            dbc.ModalFooter(
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button('Go Back',
                                                   id='preview_precursor_list_modal_back',
                                                   className='ms-auto'),
                                        dbc.Button('Generate MS/MS AutoXecute Sequence',
                                                   id='preview_precursor_list_modal_run',
                                                   className='ms-auto')
                                    ]
                                )
                            )
                        ],
                        id='preview_precursor_list_modal',
                        fullscreen=True,
                        backdrop='static',
                        scrollable=True,
                        centered=True,
                        is_open=False
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle('Generate MS/MS AutoXecute Sequence')),
                            dbc.ModalBody(get_run_layout(outdir)),
                            dbc.ModalFooter(
                                dbc.Button('Run',
                                           id='run_button',
                                           className='ms-auto')
                            )
                        ],
                        id='run_modal',
                        fullscreen=True,
                        backdrop='static',
                        scrollable=True,
                        centered=True,
                        is_open=False
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle('Success')),
                            dbc.ModalBody(f'The MS/MS AutoXecute sequence has been created in {outdir}.'),
                            dbc.ModalFooter(
                                dbc.Button('Close',
                                           id='run_success_close',
                                           className='ms-auto')
                            )
                        ],
                        id='run_success_modal',
                        size='lg',
                        centered=True,
                        is_open=False
                    ),
                    dcc.Store(id='store_plot'),
                    dcc.Store(id='store_preprocessing_params',
                              data=get_maldi_dda_preprocessing_params()),
                    dcc.Store(id='store_blank_params_log',
                              data={}),
                    dcc.Store(id='store_sample_params_log',
                              data={}),
                    dcc.Store(id='store_autox_seq',
                              data=autox_seq),
                    dcc.Store(id='store_plate_format',
                              data=get_geometry_format(et.parse(autox_seq).getroot())),
                    dcc.Store(id='store_autox_path_dict',
                              data=get_autox_path_dict(autox_seq)),
                    dcc.Store(id='store_blank_spots',
                              data={'spots': []}),
                    dcc.Store(id='store_spot_groups',
                              data={}),
                    dcc.Store(id='store_indexed_data',
                              data={}),
                    dcc.Store(id='store_precursor_data',
                              data={})
                ]
            )
        ],
        style={'margin': '20px'}
    )
