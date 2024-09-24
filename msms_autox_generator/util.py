# The following code has been modified from pyMALDIproc and pyMALDIviz.
# For more infromation, see: https://github.com/gtluu/pyMALDIproc


import os
import copy
import random
import configparser
import numpy as np
import pandas as pd
from lxml import etree as et
import tkinter
from tkinter.filedialog import askopenfilename, askdirectory
import plotly.express as px
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from msms_autox_generator.tmpdir import FILE_SYSTEM_BACKEND


def get_autox_sequence_filename():
    """
    Create GUI file selection window to allow the user to select the AutoXecute sequence file (*.run file).

    :return: AutoXecute sequence filename.
    :rtype: str
    """
    main_tk_window = tkinter.Tk()
    main_tk_window.attributes('-topmost', True, '-alpha', 0)
    autox_filename = askopenfilename(filetypes=[('AutoXecute Sequence', '*.run')])
    main_tk_window.destroy()
    return autox_filename


def get_path_name():
    """
    Create GUI directory selection window to allow the user to select a directory path.

    :return: Directory path name.
    :rtype: str
    """
    main_tk_window = tkinter.Tk()
    main_tk_window.attributes('-topmost', True, '-alpha', 0)
    dirname = askdirectory(mustexist=True)
    main_tk_window.destroy()
    return dirname


def get_maldi_dda_preprocessing_params():
    """
    Parse preprocessing parameters from the configuration file provided with pyMALDIproc.

    :return: Nest dictionaries containing preprocessing parameters for each preprocessing step.
    :rtype: dict
    """
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'etc', 'preprocessing.cfg'))
    trim_spectrum_params = {'run': False,
                            'lower_mass_range': int(config['trim_spectrum']['lower_mass_range']),
                            'upper_mass_range': int(config['trim_spectrum']['upper_mass_range'])}
    transform_intensity_params = {'run': False,
                                  'method': config['transform_intensity']['method']}
    smooth_baseline_params = {'run': False,
                              'method': config['smooth_baseline']['method'],
                              'window_length': int(config['smooth_baseline']['window_length']),
                              'polyorder': int(config['smooth_baseline']['polyorder']),
                              'delta_mz': float(config['smooth_baseline']['delta_mz']),
                              'diff_thresh': float(config['smooth_baseline']['diff_thresh'])}
    remove_baseline_params = {'run': False,
                              'method': config['remove_baseline']['method'],
                              'min_half_window': int(config['remove_baseline']['min_half_window']),
                              'max_half_window': int(config['remove_baseline']['max_half_window']),
                              'decreasing': config['remove_baseline'].getboolean('decreasing'),
                              'smooth_half_window': None,
                              'filter_order': int(config['remove_baseline']['filter_order']),
                              'sigma': None,
                              'increment': int(config['remove_baseline']['increment']),
                              'max_hits': int(config['remove_baseline']['max_hits']),
                              'window_tol': float(config['remove_baseline']['window_tol']),
                              'lambda_': int(config['remove_baseline']['lambda_']),
                              'porder': int(config['remove_baseline']['porder']),
                              'repetition': None,
                              'degree': int(config['remove_baseline']['degree']),
                              'gradient': float(config['remove_baseline']['gradient'])}
    normalize_intensity_params = {'run': False,
                                  'method': config['normalize_intensity']['method']}
    bin_spectrum_params = {'run': False,
                           'n_bins': int(config['bin_spectrum']['n_bins']),
                           'lower_mass_range': int(config['bin_spectrum']['lower_mass_range']),
                           'upper_mass_range': int(config['bin_spectrum']['upper_mass_range'])}
    peak_picking_params = {'method': config['peak_picking']['method'],
                           'snr': int(config['peak_picking']['snr']),
                           'widths': None,
                           'deisotope': config['peak_picking'].getboolean('deisotope'),
                           'fragment_tolerance': float(config['peak_picking']['fragment_tolerance']),
                           'fragment_unit_ppm': config['peak_picking'].getboolean('fragment_unit_ppm'),
                           'min_charge': int(config['peak_picking']['min_charge']),
                           'max_charge': int(config['peak_picking']['max_charge']),
                           'keep_only_deisotoped': config['peak_picking'].getboolean('keep_only_deisotoped'),
                           'min_isopeaks': int(config['peak_picking']['min_isopeaks']),
                           'max_isopeaks': int(config['peak_picking']['max_isopeaks']),
                           'make_single_charged': config['peak_picking'].getboolean('make_single_charged'),
                           'annotate_charge': config['peak_picking'].getboolean('annotate_charge'),
                           'annotate_iso_peak_count': config['peak_picking'].getboolean('annotate_iso_peak_count'),
                           'use_decreasing_model': config['peak_picking'].getboolean('use_decreasing_model'),
                           'start_intensity_check': int(config['peak_picking']['start_intensity_check']),
                           'add_up_intensity': config['peak_picking'].getboolean('add_up_intensity')}
    precursor_selection_params = {'top_n': 10,
                                  'use_exclusion_list': True,
                                  'exclusion_list_tolerance': 0.05}
    if config['remove_baseline']['smooth_half_window'] != 'None':
        remove_baseline_params['smooth_half_window'] = int(config['remove_baseline']['smooth_half_window'])
    if config['remove_baseline']['sigma'] != 'None':
        remove_baseline_params['sigma'] = float(config['rmeove_baseline']['sigma'])
    if config['remove_baseline']['repetition'] != 'None':
        remove_baseline_params['repetition'] = int(config['remove_baseline']['repetition'])
    if config['peak_picking']['widths'] != 'None':
        peak_picking_params['widths'] = int(config['peak_picking']['widths'])

    return {'TRIM_SPECTRUM': trim_spectrum_params,
            'TRANSFORM_INTENSITY': transform_intensity_params,
            'SMOOTH_BASELINE': smooth_baseline_params,
            'REMOVE_BASELINE': remove_baseline_params,
            'NORMALIZE_INTENSITY': normalize_intensity_params,
            'BIN_SPECTRUM': bin_spectrum_params,
            'PEAK_PICKING': peak_picking_params,
            'PRECURSOR_SELECTION': precursor_selection_params}


def get_autox_path_dict(autox_seq):
    return {str(index): {'sample_name': spot_group.attrib['sampleName'],
                         'raw_data_path': f"{os.path.join(et.parse(autox_seq).getroot().attrib['directory'], spot_group.attrib['sampleName'])}.d",
                         'method_path': spot_group.attrib['acqMethod']}
            for index, spot_group in enumerate(et.parse(autox_seq).getroot())}


def get_geometry_files(geometry_path):
    """
    Obtain the list of MALDI plate geometries to be selected from.

    :param geometry_path: Path to the directory containing MALDI plate geometry (*.xeo) files.
    :type geometry_path: str
    :return: Dictionary containing the geometry name as keys and the path to the corresponding geometry files as values.
    :rtype: dict
    """
    # Parse config file for inclusion list of acceptable geometries.
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'etc', 'ms1_autox_generator.cfg'))
    defaults = config['GeometryFiles']['defaults'].split(',')

    # Get list of .xeo geometry files from the GeometryFiles path.
    geometry_files = [os.path.join(dirpath, filename).replace('/', '\\')
                      for dirpath, dirnames, filenames in os.walk(geometry_path)
                      for filename in filenames
                      if os.path.splitext(filename)[1] == '.xeo']

    # Only keep geometry files that are not imaging geometries from flexImaging.
    # Discard geometry files not found in inclusion list.
    geometry_files_subset = []
    for geometry in geometry_files:
        if os.path.splitext(os.path.split(geometry)[-1])[0] in defaults:
            with open(geometry, 'r') as geometry_object:
                if 'flexImaging' not in geometry_object.read():
                    geometry_files_subset.append(geometry)
    geometry_files_subset = {os.path.splitext(os.path.split(i)[-1])[0]: i for i in geometry_files_subset}

    return geometry_files_subset


def get_geometry_format(autox):
    """
    Obtain the generalized MALDI target plate geometry format based on the geometry used in the loaded AutoXecute
    sequence. Either 24 spot, 48 spot, 96 spot, 384 spot, 1536 spot, or 6144 spot plates.

    :param autox: AutoXecute sequence file loaded as an XML tree.
    :return: Generalized MALDI target plate geometry format.
    :rtype: int
    """
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'etc', 'ms1_autox_generator.cfg'))
    if autox.attrib['geometry'] in config['GeometryFiles']['24spot_geometries'].split(','):
        return 24
    elif autox.attrib['geometry'] in config['GeometryFiles']['48spot_geometries'].split(','):
        return 48
    elif autox.attrib['geometry'] in config['GeometryFiles']['96spot_geometries'].split(','):
        return 96
    elif autox.attrib['geometry'] in config['GeometryFiles']['384spot_geometries'].split(','):
        return 384
    elif autox.attrib['geometry'] in config['GeometryFiles']['1536spot_geometries'].split(','):
        return 1536
    elif autox.attrib['geometry'] in config['GeometryFiles']['6144spot_geometries'].split(','):
        return 6144


def get_rgb_color():
    return f'rgb({str(random.randrange(0, 256))}, {str(random.randrange(0, 256))}, {str(random.randrange(0, 256))})'


def get_plate_map(plate_format):
    """
    Obtain the plate map based on a given generalized MALDI target plate geometry format.

    :param plate_format: Generalized MALDI target plate geometry format.
    :type plate_format: int
    :return: Plate map in the form of a pandas.DataFrame with alpha numeric values.
    :rtype: pandas.DataFrame
    """
    alphabets = [chr(i) for i in range(65, 91)]
    double_alphabets = [i + j for i in alphabets for j in alphabets]
    rows = alphabets + double_alphabets
    if plate_format == 24:
        rows = rows[:4]
        columns = list(range(1, 7))
    elif plate_format == 48:
        rows = rows[:6]
        columns = list(range(1, 9))
    elif plate_format == 96:
        rows = rows[:8]
        columns = list(range(1, 13))
    elif plate_format == 384:
        rows = rows[:16]
        columns = list(range(1, 25))
    elif plate_format == 1536:
        rows = rows[:32]
        columns = list(range(1, 49))
    elif plate_format == 6144:
        rows = rows[:64]
        columns = list(range(1, 97))
    data = [[f"{row}{col}" for col in columns] for row in rows]
    return pd.DataFrame(data, index=rows, columns=columns)


def get_plate_map_style(df, autox):
    # style_dicts = [{'if': {'state': 'selected'},
    #                'backgroundColor': 'inherit !important'}]
    style_dicts = []
    plate_coords = [coord for coords in df.values.tolist() for coord in coords]
    autox_coords = [cont.attrib['Pos_on_Scout'] for spot_group in autox for cont in spot_group]
    for coord in plate_coords:
        if coord not in autox_coords:
            row, col = np.where(df.values == coord)
            row = int(row)
            col = str(int(col) + 1)
            style_dicts.append({'if': {'row_index': row, 'column_id': col},
                                'backgroundColor': 'gray', 'color': 'white'})
    return style_dicts


def get_plate_map_legend():
    return pd.read_csv(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'etc', 'plate_map_legend.csv'))


def blank_figure():
    """
    Obtain a blank figure wrapped by plotly_resampler.FigureResampler to be used as a placeholder.

    :return: Blank figure.
    """
    fig = FigureResampler(go.Figure(go.Scatter(x=[], y=[])))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)
    return fig


def get_spectrum(spectrum, label_peaks=True):
    """
    Plot the spectrum to a plotly.express.line plot wrapped by plotly_resampler.FigureResampler.

    :param spectrum: Spectrum object whose data is used to generate the figure.
    :type spectrum: pymaldiproc.classes.OpenMALDISpectrum|pymaldiproc.classes.PMPTsfSpectrum|pymaldiproc.classes.PMP2DTdfSpectrum
    :param label_peaks: Whether to label the peak based on peak picking that has been performed.
    :type label_peaks: bool
    :return: Plotly figure containing mass spectrum.
    """
    spectrum_df = pd.DataFrame({'m/z': copy.deepcopy(spectrum.preprocessed_mz_array),
                                'Intensity': copy.deepcopy(spectrum.preprocessed_intensity_array)})

    if label_peaks:
        labels = copy.deepcopy(np.round(copy.deepcopy(spectrum.preprocessed_mz_array), decimals=4).astype(str))
        mask = np.ones(labels.size, dtype=bool)
        mask[spectrum.peak_picking_indices] = False
        labels[mask] = ''
        fig = FigureResampler(px.line(data_frame=spectrum_df,
                                      x='m/z',
                                      y='Intensity',
                                      hover_data={'m/z': ':.4f',
                                                  'Intensity': ':.1f'},
                                      text=labels))
        fig.update_traces(textposition='top center')
        fig.update_traces(marker=dict(color='rgba(0,0,0,0)', size=1))
    else:
        fig = FigureResampler(px.line(data_frame=spectrum_df,
                                      x='m/z',
                                      y='Intensity',
                                      hover_data={'m/z': ':.4f',
                                                  'Intensity': ':.1f'}))
    fig.update_layout(xaxis_tickformat='d',
                      yaxis_tickformat='~e')

    return fig


def cleanup_file_system_backend():
    """
    Clean up temp files generated by plotly_resampler.
    """
    for filename in os.listdir(FILE_SYSTEM_BACKEND):
        os.remove(os.path.join(FILE_SYSTEM_BACKEND, filename))
