import numpy as np
import pandas as pd
from functools import reduce
from scipy.signal import savgol_filter, find_peaks, find_peaks_cwt, peak_widths
from pyMSpec.smoothing import sg_smooth, apodization, rebin, fast_change, median
from BaselineRemoval import BaselineRemoval
from pyMSpec.normalisation import tic, rms, mad, sqrt
from icoshift import icoshift


def trim_spectra(list_of_spectra, lower_mass_range, upper_mass_range):
    for spectrum in list_of_spectra:
        spectrum_df = pd.DataFrame(data={'mz': spectrum.get_mz_array(), 'intensity': spectrum.get_intensity_array()})
        spectrum_df = spectrum_df[~(spectrum_df['mz'] <= lower_mass_range) & ~(spectrum_df['mz'] >= upper_mass_range)]
        spectrum.preprocessed_mz_array = spectrum_df['mz'].values
        spectrum.preprocessed_intensity_array = spectrum_df['intensity'].values
        spectrum.data_processing['spectrum trimming'] = {'lower mass range': lower_mass_range,
                                                         'upper mass range': upper_mass_range}
    return list_of_spectra


def transform_intensity(list_of_spectra, method='sqrt'):
    # check method
    if method not in ['sqrt', 'log', 'log2', 'log10']:
        raise Exception('Method must be "sqrt", "log", "log2", or "log10"')

    # transform intensity
    for spectrum in list_of_spectra:
        if method == 'sqrt':
            spectrum.preprocessed_intensity_array = np.sqrt(spectrum.get_intensity_array())
        elif method == 'log':
            spectrum.preprocessed_intensity_array = np.log(spectrum.get_intensity_array())
        elif method == 'log2':
            spectrum.preprocessed_intensity_array = np.log2(spectrum.get_intensity_array())
        elif method == 'log10':
            spectrum.preprocessed_intensity_array = np.log10(spectrum.get_intensity_array())
        spectrum.data_processing['intensity transformation'] = {'method': method}

    return list_of_spectra


def smooth_baseline(list_of_spectra, method='SavitzkyGolay', window_length=20, polyorder=3, delta_mz=0.2,
                    diff_thresh=0.01):
    # check method
    if method not in ['SavitzkyGolay', 'apodization', 'rebin', 'fast_change', 'median']:
        raise Exception('Method must be "SavitzkyGolay", "apodization", "rebin", "fast_change", "median"')

    # smooth baseline
    for spectrum in list_of_spectra:
        spectrum.data_processing['baseline smoothing'] = {'method': method}
        if method == 'SavitzkyGolay':
            spectrum.preprocessed_intensity_array = savgol_filter(spectrum.get_intensity_array(),
                                                                  window_length=window_length,
                                                                  polyorder=polyorder)
            spectrum.data_processing['baseline smoothing']['window length'] = window_length
            spectrum.data_processing['baseline smoothing']['polyorder'] = polyorder
        elif method == 'apodization':
            spectrum.preprocessed_mz_array, spectrum.preprocessed_intensity_array = apodization(spectrum.get_mz_array(),
                                                                                                spectrum.get_intensity_array(),
                                                                                                w_size=window_length)
            spectrum.data_processing['baseline smoothing']['window length'] = window_length
        elif method == 'rebin':
            spectrum.preprocessed_mz_array, spectrum.preprocessed_intensity_array = rebin(spectrum.get_mz_array(),
                                                                                          spectrum.get_intensity_array(),
                                                                                          delta_mz=delta_mz)
            spectrum.data_processing['baseline smoothing']['delta m/z'] = delta_mz
        elif method == 'fast_change':
            spectrum.preprocessed_mz_array, spectrum.preprocessed_intensity_array = fast_change(spectrum.get_mz_array(),
                                                                                                spectrum.get_intensity_array(),
                                                                                                diff_thresh=diff_thresh)
            spectrum.data_processing['baseline smoothing']['difference threshold'] = diff_thresh
        elif method == 'median':
            spectrum.preprocessed_mz_array, spectrum.preprocessed_intensity_array = median(spectrum.get_mz_array(),
                                                                                           spectrum.get_intensity_array(),
                                                                                           w_size=window_length)
            spectrum.data_processing['baseline smoothing']['window length'] = window_length

    return list_of_spectra


def remove_baseline(list_of_spectra, method='ZhangFit', lambda_=100, porder=1, repitition=None, degree=2,
                    gradient=0.001):
    # check method
    if method not in ['ZhangFit', 'ModPoly', 'IModPoly']:
        raise Exception('Method must be "ZhangFit", "ModPoly", or "IModPoly"')

    # remove baseline
    for spectrum in list_of_spectra:
        spectrum.data_processing['baseline removal'] = {'method': method}
        if method == 'ZhangFit':
            if repitition is None:
                repitition = 15
            spectrum.preprocessed_intensity_array = BaselineRemoval(spectrum.get_intensity_array()).ZhangFit(lambda_=lambda_,
                                                                                                             porder=porder,
                                                                                                             itermax=repitition)
            spectrum.data_processing['baseline removal']['lambda'] = lambda_
            spectrum.data_processing['baseline removal']['porder'] = porder
            spectrum.data_processing['baseline removal']['repitition'] = repitition
        elif method == 'ModPoly':
            if repitition is None:
                repitition = 100
            spectrum.preprocessed_intensity_array = BaselineRemoval(spectrum.get_intensity_array()).ModPoly(degree=degree,
                                                                                                            repitition=repitition,
                                                                                                            gradient=gradient)
            spectrum.data_processing['baseline removal']['degree'] = degree
            spectrum.data_processing['baseline removal']['repitition'] = repitition
            spectrum.data_processing['baseline removal']['gradient'] = gradient
        elif method == 'IModPoly':
            if repitition is None:
                repitition = 100
            spectrum.preprocessed_intensity_array = BaselineRemoval(spectrum.get_intensity_array()).IModPoly(degree=degree,
                                                                                                             repitition=repitition,
                                                                                                             gradient=gradient)
            spectrum.data_processing['baseline removal']['degree'] = degree
            spectrum.data_processing['baseline removal']['repitition'] = repitition
            spectrum.data_processing['baseline removal']['gradient'] = gradient

    return list_of_spectra


def normalize_intensity(list_of_spectra, method='tic'):
    # check method
    if method not in ['tic', 'rms', 'mad', 'sqrt']:
        raise Exception('Method must be "tic", "rms", "mad", or "sqrt"')

    # normalize intensity
    for spectrum in list_of_spectra:
        if method == 'tic':
            spectrum.preprocessed_intensity_array = tic(spectrum.get_mz_array(),
                                                        spectrum.get_intensity_array())
        elif method == 'rms':
            spectrum.preprocessed_intensity_array = rms(spectrum.get_mz_array(),
                                                        spectrum.get_intensity_array())
        elif method == 'mad':
            spectrum.preprocessed_intensity_array = mad(spectrum.get_mz_array(),
                                                        spectrum.get_intensity_array())
        elif method == 'sqrt':
            spectrum.preprocessed_intensity_array = sqrt(spectrum.get_mz_array(),
                                                         spectrum.get_intensity_array())
        spectrum.data_processing['intensity normalization'] = {'method': method}

    return list_of_spectra


def bin_spectra(list_of_spectra, n_bins, lower_mass_range, upper_mass_range):
    bins = np.linspace(lower_mass_range, upper_mass_range, n_bins, dtype=np.float64)

    for spectrum in list_of_spectra:
        spectrum.preprocessed_intensity_array, spectrum.preprocessed_mz_array = np.histogram(spectrum.preprocessed_mz_array,
                                                                                             bins=bins,
                                                                                             weights=spectrum.preprocessed_intensity_array)
        spectrum.preprocessed_mz_array = spectrum.preprocessed_mz_array[:-1]
        spectrum.data_processing['spectra binning'] = {'lower mass range': lower_mass_range,
                                                       'upper mass range': upper_mass_range,
                                                       'number of bins': n_bins}

    return list_of_spectra


def align_spectra(list_of_spectra, method='average', inter='whole', n='f', scale=None, coshift_preprocessing=False,
                  coshift_preprocessing_max_shift=None, fill_with_previous=True, average2_multiplier=3):
    # check method
    if method not in ['average', 'median', 'max', 'average2']:
        raise Exception('Method must be "average", "median", "max", or "average2"')

    # intensity arrays must be binned/on same m/z axis prior to alignment
    intensity_arrays = [spectrum.get_intensity_array() for spectrum in list_of_spectra]
    intensity_array_2d = np.stack(intensity_arrays)
    xcs, ints, ind, target = icoshift(method, intensity_array_2d, inter=inter, n=n, scale=scale,
                                      coshift_preprocessing=coshift_preprocessing,
                                      coshift_preprocessing_max_shift=coshift_preprocessing_max_shift,
                                      fill_with_previous=fill_with_previous,
                                      average2_multiplier=average2_multiplier)

    for spectrum, row in zip(list_of_spectra, xcs):
        spectrum.preprocessed_intensity_array = row
        spectrum.data_processing['spectra alignment'] = {'method': method}
        spectrum.data_processing['spectra alignment']['inter'] = inter
        spectrum.data_processing['spectra alignment']['n'] = n
        spectrum.data_processing['spectra alignment']['scale'] = scale
        spectrum.data_processing['spectra alignment']['coshift_preprocessing'] = coshift_preprocessing
        spectrum.data_processing['spectra alignment']['coshift_preprocessing_max_shift'] = coshift_preprocessing_max_shift
        spectrum.data_processing['spectra alignment']['fill_with_previous'] = fill_with_previous
        spectrum.data_processing['spectra alignment']['average2_multiplier'] = average2_multiplier

    return list_of_spectra


def estimate_peak_widths(intensity_array):
    peak_indices, peak_properties = find_peaks(intensity_array)
    widths = peak_widths(intensity_array, peak_indices)
    return widths[0]


def peak_picking(list_of_spectra, method='cwt', widths=None, snr=3):
    # check method
    if method not in ['locmax', 'cwt']:
        raise Exception('Method must be "locmax" or "cwt"')

    # peak picking
    for spectrum in list_of_spectra:
        spectrum.data_processing['peak picking'] = {'method': method}
        if method == 'locmax':
            peak_indices, peak_properties = find_peaks(spectrum.get_intensity_array())
            spectrum.peak_picked_mz_array = spectrum.get_mz_array()[peak_indices]
            spectrum.peak_picked_intensity_array = spectrum.get_intensity_array()[peak_indices]
        elif method == 'cwt':
            # estimate peak widths if necessary
            if widths is None:
                estimated_widths = estimate_peak_widths(spectrum.get_intensity_array())
                widths_start = np.min(estimated_widths)
                widths_stop = 2 * np.mean(estimated_widths)
                widths_step = ((2 * np.mean(estimated_widths)) - np.min(estimated_widths)) / 10
                widths = np.arange(widths_start, widths_stop, widths_step)
            peak_indices = find_peaks_cwt(spectrum.get_intensity_array(), widths, min_snr=snr)
            spectrum.peak_picked_mz_array = spectrum.get_mz_array()[peak_indices]
            spectrum.peak_picked_intensity_array = spectrum.get_intensity_array()[peak_indices]
            spectrum.data_processing['peak picking']['lower peak width'] = np.min(widths)
            spectrum.data_processing['peak picking']['upper peak width'] = np.max(widths)

    return list_of_spectra


def get_feature_matrix(list_of_spectra, missing_value_imputation=True):
    # get a consensus m/z array
    peak_picked_mz_arrays = [spectrum.peak_picked_mz_array for spectrum in list_of_spectra]
    peak_picked_consensus = pd.DataFrame(data={'mz': np.unique(np.concatenate(peak_picked_mz_arrays))}).sort_values(by='mz')
    preprocessed_mz_arrays = [spectrum.get_mz_array() for spectrum in list_of_spectra]
    preprocessed_concensus = pd.DataFrame(data={'mz': np.unique(np.concatenate(preprocessed_mz_arrays))}).sort_values(by='mz')

    spectra_dfs_peak_picked = [peak_picked_consensus]
    spectra_dfs_preprocessed = [preprocessed_concensus]
    for spectrum in list_of_spectra:
        spectra_dfs_peak_picked.append(pd.DataFrame(data={'mz': spectrum.peak_picked_mz_array,
                                                          spectrum.spectrum_id: spectrum.get_intensity_array()}))
        spectra_dfs_preprocessed.append(pd.DataFrame(data={'mz': spectrum.get_mz_array(),
                                                           spectrum.spectrum_id: spectrum.get_intensity_array()}))
    feature_matrix = reduce(lambda x, y: pd.merge_asof(x, y, on='mz', tolerance=0.5, direction='nearest'), spectra_dfs_peak_picked).sort_values(by='mz')
    if missing_value_imputation:
        ref_matrix = reduce(lambda x, y: pd.merge_asof(x, y, on='mz', tolerance=0.5, direction='nearest'), spectra_dfs_preprocessed).sort_values(by='mz')
        for colname in feature_matrix.columns:
            if colname != 'mz':
                tmp_df = pd.merge_asof(feature_matrix[['mz', colname]],
                                       ref_matrix[['mz', colname]],
                                       on='mz',
                                       tolerance=0.5,
                                       direction='nearest')
                feature_matrix[colname] = tmp_df.drop('mz', axis=1).mean(axis=1).values
    feature_matrix = feature_matrix.fillna(0)
    return feature_matrix


def export_feature_list(feature_matrix, output):
    feature_matrix.to_csv(output, index=False)
