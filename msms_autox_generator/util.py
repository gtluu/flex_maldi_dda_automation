import os
import copy
import configparser
import numpy as np
import pandas as pd
import tkinter
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename
import plotly.express as px
import plotly.graph_objects as go
from plotly_resampler import FigureResampler


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
    config.read(os.path.join(os.path.dirname(__file__), 'etc', 'ms1_autox_generator.cfg'))
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


def get_geometry_format(autox):
    """
    Obtain the generalized MALDI target plate geometry format based on the geometry used in the loaded AutoXecute
    sequence. Either 24 spot, 48 spot, 96 spot, 384 spot, 1536 spot, or 6144 spot plates.

    :param autox: AutoXecute sequence file loaded as an XML tree.
    :return: Generalized MALDI target plate geometry format.
    :rtype: int
    """
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'etc', 'ms1_autox_generator.cfg'))
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


def get_spectrum(spectrum):
    """
    Plot the spectrum to a plotly.express.line plot wrapped by plotly_resampler.FigureResampler.

    :param spectrum: Spectrum object whose data is used to generate the figure.
    :type spectrum: pymaldiproc.classes.OpenMALDISpectrum|pymaldiproc.classes.PMPTsfSpectrum|pymaldiproc.classes.PMPTdfSpectrum
    :return: Plotly figure containing mass spectrum.
    """
    spectrum_df = pd.DataFrame({'m/z': copy.deepcopy(spectrum.preprocessed_mz_array),
                                'Intensity': copy.deepcopy(spectrum.preprocessed_intensity_array)})
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
    fig.update_layout(xaxis_tickformat='d',
                      yaxis_tickformat='~e')
    return fig


def cleanup_file_system_backend():
    """
    Clean up temp files generated by plotly_resampler.
    """
    for filename in os.listdir(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'file_system_backend')):
        os.remove(os.path.join(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'file_system_backend'),
                               filename))
