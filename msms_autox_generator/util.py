# The following code has been modified from pyMALDIproc and pyMALDIviz.
# For more infromation, see: https://github.com/gtluu/pyMALDIproc


import os
import random
import configparser
import numpy as np
import pandas as pd
from lxml import etree as et
import tkinter
from tkinter.filedialog import askopenfilename, askdirectory
from pymaldiviz.util import get_preprocessing_params


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
    Parse preprocessing parameters from the configuration file provided with pyMALDIviz.

    :return: Nest dictionaries containing preprocessing parameters for each preprocessing step.
    :rtype: dict
    """
    params_dict = get_preprocessing_params()
    params_dict['TRIM_SPECTRUM']['run'] = False
    params_dict['TRANSFORM_INTENSITY']['run'] = False
    params_dict['SMOOTH_BASELINE']['run'] = False
    params_dict['REMOVE_BASELINE']['run'] = False
    params_dict['NORMALIZE_INTENSITY']['run'] = False
    params_dict['BIN_SPECTRUM']['run'] = False
    params_dict['PEAK_PICKING']['run'] = False
    params_dict['PRECURSOR_SELECTION'] = {'top_n': 10,
                                          'use_exclusion_list': True,
                                          'exclusion_list_tolerance': 0.05}
    return params_dict


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
    """
    Get a random RGB color.

    :return: Random RGB color.
    :rtype: str
    """
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
    """
    Obtain the plate map styles to be displayed in a Dash DataTable.

    :param df: DataFrame containing coordinate information.
    :type df: pandas.DataFrame
    :param autox: AutoXecute sequence XML element object.
    :return: List of dictionaries containing style parameters for the plate map.
    :rtype: list[dict]
    """
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
    """
    Obtain a pandas.DataFrame containing the default plate map legend values with categories 'Sample', 'Blank', and
    'Empty'.

    :return: Single column DataFrame containing three default categories.
    :rtype: pandas.DataFrame
    """
    return pd.read_csv(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'etc', 'plate_map_legend.csv'))
