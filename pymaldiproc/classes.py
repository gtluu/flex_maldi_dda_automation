import os
from functools import reduce
import numpy as np
import pandas as pd
from uuid import uuid4
from pyteomics import mzml as pyt
from scipy.signal import savgol_filter, find_peaks, find_peaks_cwt, peak_widths
from BaselineRemoval import BaselineRemoval
from pyMSpec.smoothing import sg_smooth, apodization, rebin, fast_change, median
from pyMSpec.normalisation import tic, rms, mad, sqrt


# Barebones class to hold basic MALDI spectrum data.
class MALDISpectrum(object):
    def __init__(self, pyteomics_dict, filename):
        self.source = filename
        self.name = None
        self.uuid = str(uuid4())
        self.spectrum_id = None
        self.spot = None
        self.ms_level = None
        self.raw_mz_array = None
        self.raw_intensity_array = None
        self.preprocessed_mz_array = None
        self.preprocessed_intensity_array = None
        self.peak_picked_mz_array = None
        self.peak_picked_intensity_array = None
        self.data_processing = {}

        self.parse_pyteomics_dict(pyteomics_dict)

    def parse_pyteomics_dict(self, pyteomics_dict):
        # metadata
        self.name = str(os.path.splitext(os.path.split(self.source)[-1])[0]) + '_' + str(pyteomics_dict['index'])
        try:
            self.spot = pyteomics_dict['maldi spot identifier']
            self.spectrum_id = self.name + '|' + self.spot + '|' + self.uuid
        except KeyError:
            print('MALDI Spot Identifier information not found.')
            self.spectrum_id = self.name + '|' + self.uuid

        # spectra
        self.ms_level = pyteomics_dict['ms level']
        self.raw_mz_array = pyteomics_dict['m/z array']
        self.raw_intensity_array = pyteomics_dict['intensity array']

    # get most up to date mz_array (raw or preprocessed)
    def get_mz_array(self):
        if self.preprocessed_mz_array is None and self.peak_picked_mz_array is None:
            return self.raw_mz_array
        elif self.preprocessed_mz_array is not None and self.peak_picked_mz_array is None:
            return self.preprocessed_mz_array
        elif self.peak_picked_mz_array is not None:
            return self.peak_picked_mz_array

    # get most up to date intensity_array (raw or preprocessed)
    def get_intensity_array(self):
        if self.preprocessed_intensity_array is None and self.peak_picked_intensity_array is None:
            return self.raw_intensity_array
        elif self.preprocessed_intensity_array is not None and self.peak_picked_intensity_array is None:
            return self.preprocessed_intensity_array
        elif self.peak_picked_intensity_array is not None:
            return self.peak_picked_intensity_array

    # get peak picked (centroided) feature list
    def get_peak_list(self):
        if self.peak_picked_mz_array is not None and self.peak_picked_intensity_array is not None:
            return pd.DataFrame(data={'mz': self.peak_picked_mz_array,
                                      'intensity': self.peak_picked_intensity_array})
        else:
            return pd.DataFrame(data={'mz': [0], 'intensity': [0]})
