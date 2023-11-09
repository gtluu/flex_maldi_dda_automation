import os
import argparse
import numpy as np
import pandas as pd
import lxml.etree as et
from pyTDFSDK.init_tdf_sdk import init_tdf_sdk_api
from pyTDFSDK.classes import TsfData, TdfData
from pymaldiproc.classes import PMPTsfSpectrum, PMPTdfSpectrum
from pymaldiproc.preprocessing import (trim_spectra, transform_intensity, smooth_baseline, remove_baseline,
                                       normalize_intensity, bin_spectra, align_spectra, peak_picking,
                                       get_feature_matrix)


def arg_descriptions():
    descriptions = {'autox': 'AutoXecute .run XML file from timControl.',
                    'blank': 'Spot Group from AutoXecute sequence to use as blank/control. Requires at least 2 spot '
                             'groups for usage. Default = none',
                    'method': '.m method directory to be used for MS/MS data acquisition. Defaults to method used for '
                              'MS1 acquisition if not specified.',
                    'outdir': 'Path to folder in which to write output files. Default = none',
                    'top_n': 'Top N number of peaks to select from each spot for MS/MS acquisition. Default = 10',
                    'peak_picking_method': 'Method to use for peak picking. Default = cwt',
                    'peak_picking_widths': 'Peak widths values to use during peak picking. Default = None',
                    'peak_picking_snr': 'Signal to noise ratio to use during peak picking. Default = 3',
                    'exclusion_list_snr': 'Signal to noise ratio to use during peak picking. Default = 100',
                    'exclusion_list_tolerance': 'm/z tolerance to use when comparing top N selected peaks to exclusion '
                                                'list. Default = 0.1'}
    return descriptions


def get_args():
    desc = arg_descriptions()

    parser = argparse.ArgumentParser()

    required = parser.add_argument_group('Require Parameters')
    required.add_argument('--autox', help=desc['autox'], required=True, type=str)

    optional = parser.add_argument_group('Optional Parameters')
    optional.add_argument('--blank', help=desc['blank'], default='', type=str)
    optional.add_argument('--method', help=desc['method'], default='', type=str)
    optional.add_argument('--outdir', help=desc['outdir'], default='', type=str)
    optional.add_argument('--top_n', help=desc['top_n'], default=10, type=int)
    optional.add_argument('--peak_picking_method', help=desc['peak_picking_method'], default='cwt', type=str,
                          choices=['cwt', 'locmax'])
    optional.add_argument('--peak_picking_widths', help=desc['peak_picking_widths'], default=None)
    optional.add_argument('--peak_picking_snr', help=desc['peak_picking_snr'], default=3, type=int)
    optional.add_argument('--exclusion_list_snr', help=desc['peak_picking_snr'], default=100, type=int)
    optional.add_argument('--exclusion_list_tolerance', help=desc['exclusion_list_tolerance'], default=0.1, type=float)

    arguments = parser.parse_args()
    return vars(arguments)


def parse_maldi_data(dot_d_path, sdk):
    # detect metadata schema in .d directory
    exts = [os.path.splitext(fname)[1] for dirpath, dirnames, filenames in os.walk(dot_d_path)
            for fname in filenames]
    if '.tdf' in exts and '.tsf' not in exts and '.baf' not in exts:
        schema = 'TDF'
    elif '.tsf' in exts and '.tdf' not in exts and '.baf' not in exts:
        schema = 'TSF'
    else:
        raise Exception('Could not detect raw data schema for .d metadata.')
    # read MALDI data
    if schema == 'TSF':
        data = TsfData(dot_d_path, sdk)
    elif schema == 'TDF':
        data = TdfData(dot_d_path, sdk)
    # parse MALDI data
    list_of_scans = []
    for frame in range(1, data.analysis['Frames'].shape[0] + 1):
        if schema == 'TSF':
            scan = PMPTsfSpectrum(data, frame, 'centroid')
        elif schema == 'TDF':
            scan = PMPTdfSpectrum(data, frame, 'centroid', exclude_mobility=True)
        if scan.mz_array is not None and scan.intensity_array is not None and \
                scan.mz_array.size != 0 and scan.intensity_array.size != 0 and \
                scan.mz_array.size == scan.intensity_array.size:
            list_of_scans.append(scan)
    return list_of_scans


def preprocess(maldi_spectra):
    maldi_spectra = trim_spectra(maldi_spectra, lower_mass_range=100, upper_mass_range=2000)
    maldi_spectra = transform_intensity(maldi_spectra, method='sqrt')
    maldi_spectra = smooth_baseline(maldi_spectra, method='SavitzkyGolay')
    maldi_spectra = remove_baseline(maldi_spectra, method='SNIP')
    maldi_spectra = normalize_intensity(maldi_spectra, method='tic')
    maldi_spectra = bin_spectra(maldi_spectra, n_bins=38000, lower_mass_range=100, upper_mass_range=2000)
    maldi_spectra = align_spectra(maldi_spectra)
    return maldi_spectra


def main():
    args = get_args()

    sdk = init_tdf_sdk_api()

    if args['outdir'] == '':
        outdir = os.path.split(args['autox'])[0]
    else:
        outdir = args['outdir']
    outfile = os.path.splitext(os.path.split(args['autox'])[1])[0]

    autox_tree = et.parse(args['autox'])
    autox = autox_tree.getroot()

    if args['blank'] != '':
        for spot_group in autox:
            if spot_group.attrib['sampleName'] == args['blank']:
                dot_d_path = os.path.join(autox.attrib['directory'], spot_group.attrib['sampleName'] + '.d')
                maldi_spectra = parse_maldi_data(dot_d_path, sdk)
                maldi_spectra = preprocess(maldi_spectra)
                maldi_spectra = peak_picking(maldi_spectra,
                                             method=args['peak_picking_method'],
                                             widths=args['peak_picking_widths'],
                                             snr=args['exclusion_list_snr'])
                feature_matrix = get_feature_matrix(maldi_spectra, missing_value_imputation=False)
                feature_matrix = feature_matrix.round(2)
                exclusion_list_df = pd.DataFrame(data={'mz': np.unique(feature_matrix['mz'].values)})

    new_autox = et.Element(autox.tag, attrib=autox.attrib)
    for spot_group in autox:
        if spot_group.attrib['sampleName'] != args['blank']:
            dot_d_path = os.path.join(autox.attrib['directory'], spot_group.attrib['sampleName'] + '.d')
            maldi_spectra = parse_maldi_data(dot_d_path, sdk)
            maldi_spectra = preprocess(maldi_spectra)
            for cont in spot_group:
                spectrum = [i for i in maldi_spectra if i.spot == cont.attrib['Pos_on_Scout']][0]
                spectrum = peak_picking([spectrum],
                                        method=args['peak_picking_method'],
                                        widths=args['peak_picking_widths'],
                                        snr=args['peak_picking_snr'])[0]
                spectrum_mz_df = pd.DataFrame(data={'mz': spectrum.peak_picked_mz_array,
                                                    'intensity': spectrum.peak_picked_intensity_array})
                if args['blank'] != '':
                    merged_mz_df = pd.merge_asof(spectrum_mz_df,
                                                 exclusion_list_df.rename(columns={'mz': 'exclusion_list'}),
                                                 # on='mz',
                                                 left_on='mz',
                                                 right_on='exclusion_list',
                                                 tolerance=args['exclusion_list_tolerance'],
                                                 direction='nearest')
                    merged_mz_df = merged_mz_df.drop(merged_mz_df.dropna().index)
                    merged_mz_df = merged_mz_df.sort_values(by='intensity', ascending=False).round(4)
                    merged_mz_df = merged_mz_df.drop_duplicates(subset='mz')
                    top_n_peaks = merged_mz_df['mz'].values.tolist()[:args['top_n']]
                else:
                    spectrum_mz_df = spectrum_mz_df.sort_values(by='intensity', ascending=False).round(4)
                    spectrum_mz_df = spectrum_mz_df.drop_duplicates(subset='mz')
                    top_n_peaks = spectrum_mz_df['mz'].values.tolist()[:args['top_n']]

                new_spot_group = et.SubElement(new_autox, spot_group.tag, attrib=spot_group.attrib)
                new_spot_group.attrib['sampleName'] = new_spot_group.attrib['sampleName'] + '_' + \
                                                      cont.attrib['Pos_on_Scout'] + '_MSMS'
                if args['method'] != '':
                    new_spot_group.attrib['acqMethod'] = args['method']
                for peak in top_n_peaks:
                    new_cont = et.SubElement(new_spot_group, cont.tag, attrib=cont.attrib)
                    new_cont.attrib['acqJobMode'] = 'MSMS'
                    new_cont.attrib['precursor_m_z'] = str(peak)

    new_autox_tree = et.ElementTree(new_autox)
    new_autox_tree.write(os.path.join(outdir, outfile + '_MALDI_DDA.run'),
                         encoding='utf-8',
                         xml_declaration=True,
                         pretty_print=True)


if __name__ == '__main__':
    main()
