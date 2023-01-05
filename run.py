import os
import argparse
import lxml.etree as et
from timsconvert.init_bruker_dll import *
from timsconvert.data_input import *
from timsconvert.classes import *
from timsconvert.parse_maldi import *
from pymaldiproc.classes import *
from pymaldiproc.preprocessing import *


def arg_descriptions():
    descriptions = {'autox': 'AutoXecute .run XML file from timControl.',
                    'blank': 'Spot Group from AutoXecute sequence to use as blank/control. Requires at least 2 spot '
                             'groups for usage. Default = none',
                    'method': '.m method directory to be used for MS/MS data acquisition. Defaults to method used for '
                              'MS1 acquisition if not specified.',
                    'outdir': 'Path to folder in which to write output files. Default = none',
                    'top_n': 'Top N number of peaks to select from each spot for MS/MS acquisition. Default = 10',
                    'trim_spectra': 'Trim MS1 spectra during preprocessing. Default = False',
                    'trim_spectra_lower_mass_range': 'Lower mass range for spectrum trimming. Default = 100',
                    'trim_spectra_upper_mass_range': 'Upper mass range for spectrum trimming. Default = 2000',
                    'transform_intensity': 'Transform MS1 spectra intensity during preprocessing. Default = False',
                    'transform_intensity_method': 'Method to use for intensity transformation. Default = sqrt',
                    'smooth_baseline': 'Smooth MS1 spectra baseline during preprocessing. Default = False',
                    'smooth_baseline_method': 'Method to use for baseline smoothing. Default = SavitzkyGolay',
                    'smooth_baseline_window_length': 'Window length to use for baseline smoothing. Default = 20',
                    'smooth_baseline_polyorder': 'Polyorder value to use for baseline smoothing. Default = 3',
                    'smooth_baseline_delta_mz': 'Delta m/z value to use for baseline smoothing. Default = 0.2',
                    'smooth_baseline_diff_thresh': 'Difference threshold to use for baseline smoothing. Default = 0.01',
                    'remove_baseline': 'Remove MS1 spectra baseline during preprocessing. Default = False',
                    'remove_baseline_method': 'Method to use for baseline removal. Default = ZhangFit',
                    'remove_baseline_lambda': 'Lambda value to use for baseline removal. Default = 100',
                    'remove_baseline_polyorder': 'Polyorder value to use for baseline removal. Default = 1',
                    'remove_baseline_repitition': 'Repitition value to use for baseline removal. Default = None',
                    'remove_baseline_degree': 'Degree value to use for baseline removal. Default = 2',
                    'remove_baseline_gradient': 'Gradient value to use for baseline removal. Default = 0.001',
                    'normalize_intensity': 'Normalize MS1 spectra intensity during preprocessing. Default = False',
                    'normalize_intensity_method': 'Method to use for intensity normalization. Default = tic',
                    'bin_spectra': 'Perform MS1 spectra binning during preprocessing. Default = False',
                    'bin_spectra_n_bins': 'Number of bins to use for spectra binning. Default = 8000',
                    'bin_spectra_lower_mass_range': 'Lower mass range for spectrum binning. Default = 100',
                    'bin_spectra_upper_mass_range': 'Upper mass range for spectrum binning. Default = 2000',
                    'align_spectra': 'Align MS1 spectra during preprocessing. Default = False',
                    'align_spectra_method': 'Method to use for spectra alignment. Default = average',
                    'align_spectra_inter': 'Icoshift inter value to use for spectra alignment. Default = whole',
                    'align_spectra_n': 'Icoshift n value to use for spectra alignment. Default = f',
                    'align_spectra_scale': 'Icoshift scale value to use for spectra alignment. Default = None',
                    'align_spectra_coshift_preprocessing': 'Perform coshift preprocessing during spectra alignment. '
                                                           'Default = False',
                    'align_spectra_coshift_preprocessing_max_shift': 'Max shift for coshift preprocessing during '
                                                                     'spectra alignment. Default = None',
                    'align_spectra_fill_with_previous': 'Fill with previous value during spectra alignment. '
                                                        'Default = True',
                    'align_spectra_average2_multiplier': 'Multiplier value to use with average2 algorithm during '
                                                         'spectra alignment. Defeault = 3',
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

    preprocessing = parser.add_argument_group('Optional Preprocessing Parameters')

    preprocessing.add_argument('--trim_spectra', help=desc['trim_spectra'], action='store_true')
    preprocessing.add_argument('--trim_spectra_lower_mass_range', help=desc['trim_spectra_lower_mass_range'],
                               default=100, type=int)
    preprocessing.add_argument('--trim_spectra_upper_mass_range', help=desc['trim_spectra_upper_mass_range'],
                               default=2000, type=int)

    preprocessing.add_argument('--transform_intensity', help=desc['transform_intensity'], action='store_true')
    preprocessing.add_argument('--transform_intensity_method', help=desc['transform_intensity_method'], default='sqrt',
                               type=str, choices=['sqrt', 'log', 'log2', 'log10'])

    preprocessing.add_argument('--smooth_baseline', help=desc['smooth_baseline'], action='store_true')
    preprocessing.add_argument('--smooth_baseline_method', help=desc['smooth_baseline_method'], default='SavitzkyGolay',
                               type=str, choices=['SavitzkyGolay', 'apodization', 'rebin', 'fast_change', 'median'])
    preprocessing.add_argument('--smooth_baseline_window_length', help=desc['smooth_baseline_window_length'],
                               default=20, type=int)
    preprocessing.add_argument('--smooth_baseline_polyorder', help=desc['smooth_baseline_polyorder'], default=3,
                               type=int)
    preprocessing.add_argument('--smooth_baseline_delta_mz', help=desc['smooth_baseline_delta_mz'], default=0.2,
                               type=float)
    preprocessing.add_argument('--smooth_baseline_diff_thresh', help=desc['smooth_baseline_diff_thresh'], default=0.01,
                               type=float)

    preprocessing.add_argument('--remove_baseline', help=desc['remove_baseline'], action='store_true')
    preprocessing.add_argument('--remove_baseline_method', help=desc['remove_baseline_method'], default='ZhangFit',
                               type=str, choices=['ZhangFit', 'ModPoly', 'IModPoly'])
    preprocessing.add_argument('--remove_baseline_lambda', help=desc['remove_baseline_lambda'], default=100, type=int)
    preprocessing.add_argument('--remove_baseline_polyorder', help=desc['remove_baseline_polyorder'], default=1,
                               type=int)
    preprocessing.add_argument('--remove_baseline_repitition', help=desc['remove_baseline_repitition'], default=None)
    preprocessing.add_argument('--remove_baseline_degree', help=desc['remove_baseline_degree'], default=2, type=int)
    preprocessing.add_argument('--remove_baseline_gradient', help=desc['remove_baseline_gradient'], default=0.001,
                               type=float)

    preprocessing.add_argument('--normalize_intensity', help=desc['normalize_intensity'], action='store_true')
    preprocessing.add_argument('--normalize_intensity_method', help=desc['normalize_intensity_method'], default='tic',
                               type=str, choices=['tic', 'rms', 'mad', 'sqrt'])

    preprocessing.add_argument('--bin_spectra', help=desc['bin_spectra'], action='store_true')
    preprocessing.add_argument('--bin_spectra_n_bins', help=desc['bin_spectra_n_bins'], default=8000, type=int)
    preprocessing.add_argument('--bin_spectra_lower_mass_range', help=desc['bin_spectra_lower_mass_range'],
                               default=100, type=int)
    preprocessing.add_argument('--bin_spectra_upper_mass_range', help=desc['bin_spectra_upper_mass_range'],
                               default=2000, type=int)

    preprocessing.add_argument('--align_spectra', help=desc['align_spectra'], action='store_true')
    preprocessing.add_argument('--align_spectra_method', help=desc['align_spectra_method'], default='average',
                               type=str, choices=['average', 'median', 'max', 'average2'])
    preprocessing.add_argument('--align_spectra_inter', help=desc['align_spectra_inter'], default='whole', type=str)
    preprocessing.add_argument('--align_spectra_n', help=desc['align_spectra_n'], default='f', type=str)
    preprocessing.add_argument('--align_spectra_scale', help=desc['align_spectra_scale'], default=None)
    preprocessing.add_argument('--align_spectra_coshift_preprocessing',
                               help=desc['align_spectra_coshift_preprocessing'], action='store_true')
    preprocessing.add_argument('--align_spectra_coshift_preprocessing_max_shift',
                               help=desc['align_spectra_coshift_preprocessing_max_shift'], default=None)
    preprocessing.add_argument('--align_spectra_fill_with_previous', help=desc['align_spectra_fill_with_previous'],
                               action='store_true')  # maybe switch to store_false?
    preprocessing.add_argument('--align_spectra_average2_multiplier', help=desc['align_spectra_average2_multiplier'],
                               default=3, type=int)

    arguments = parser.parse_args()
    return vars(arguments)


def main(args):
    sdk = init_tdf_sdk_dll()

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
                if schema_detection(dot_d_path) == 'TSF':
                    blank = tsf_data(dot_d_path, sdk)
                    num_frames = blank.frames.shape[0] + 1
                    scan_dicts = parse_maldi_tsf(blank, 1, num_frames, 'centroid', False, 0, 64)
                elif schema_detection(dot_d_path) == 'TDF':
                    blank = tdf_data(dot_d_path, sdk)
                    num_frames = blank.frames.shape[0] + 1
                    scan_dicts = parse_maldi_tdf(blank, 1, num_frames, 'centroid', False, True, 0, 64)
                maldi_spectra = []
                for count, scan_dict in enumerate(scan_dicts):
                    scan_dict['index'] = count
                    scan_dict['maldi spot identifier'] = scan_dict['coord']
                    scan_dict['ms level'] = scan_dict['ms_level']
                    scan_dict['m/z array'] = scan_dict['mz_array']
                    scan_dict['intensity array'] = scan_dict['intensity_array']
                    maldi_spectra.append(MALDISpectrum(scan_dict, dot_d_path))
                if args['trim_spectra']:
                    maldi_spectra = trim_spectra(maldi_spectra,
                                                 lower_mass_range=args['trim_spectra_lower_mass_range'],
                                                 upper_mass_range=args['trim_spectra_upper_mass_range'])
                if args['transform_intensity']:
                    maldi_spectra = transform_intensity(maldi_spectra, method=args['transform_intensity_method'])
                if args['smooth_baseline']:
                    maldi_spectra = smooth_baseline(maldi_spectra,
                                                    method=args['smooth_baseline_method'],
                                                    window_length=args['smooth_baseline_window_length'],
                                                    polyorder=args['smooth_baseline_polyorder'],
                                                    delta_mz=args['smooth_baseline_delta_mz'],
                                                    diff_thresh=args['smooth_baseline_diff_thresh'])
                if args['remove_baseline']:
                    maldi_spectra = remove_baseline(maldi_spectra,
                                                    method=args['remove_baseline_method'],
                                                    lambda_=args['remove_baseline_lambda'],
                                                    porder=args['remove_baseline_polyorder'],
                                                    repitition=args['remove_baseline_repitition'],
                                                    degree=args['remove_baseline_degree'],
                                                    gradient=args['remove_baseline_gradient'])
                if args['normalize_intensity']:
                    maldi_spectra = normalize_intensity(maldi_spectra, method=args['normalize_intensity_method'])
                if args['bin_spectra']:
                    maldi_spectra = bin_spectra(maldi_spectra,
                                                n_bins=args['bin_spectra_n_bins'],
                                                lower_mass_range=args['bin_spectra_lower_mass_range'],
                                                upper_mass_range=args['bin_spectra_upper_mass_range'])
                if args['align_spectra']:
                    maldi_spectra = align_spectra(maldi_spectra,
                                                  method=args['align_spectra_method'],
                                                  inter=args['align_spectra_inter'],
                                                  n=args['align_spectra_n'],
                                                  scale=args['align_spectra_scale'],
                                                  coshift_preprocessing=args['align_spectra_coshift_preprocessing'],
                                                  coshift_preprocessing_max_shift=args['align_spectra_coshift_preprocessing_max_shift'],
                                                  fill_with_previous=args['align_spectra_fill_with_previous'],
                                                  average2_multiplier=args['align_spectra_average2_multiplier'])
                maldi_spectra = peak_picking(maldi_spectra,
                                             method=args['peak_picking_method'],
                                             widths=args['peak_picking_widths'],
                                             snr=args['exclusion_list_snr'])
                feature_matrix = get_feature_matrix(maldi_spectra, missing_value_imputation=False)
                feature_matrix = feature_matrix.round(2)
                exclusion_list_df = pd.DataFrame(data={'mz': np.unique(feature_matrix['mz'].values)})

    # TODO: initialize new etree here
    new_autox = et.Element(autox.tag, attrib=autox.attrib)
    for spot_group in autox:
        if spot_group.attrib['sampleName'] != args['blank']:
            dot_d_path = os.path.join(autox.attrib['directory'], spot_group.attrib['sampleName'] + '.d')
            if schema_detection(dot_d_path) == 'TSF':
                data = tsf_data(dot_d_path, sdk)
                num_frames = data.frames.shape[0] + 1
                scan_dicts = parse_maldi_tsf(data, 1, num_frames, 'centroid', False, 0, 64)
            elif schema_detection(dot_d_path) == 'TDF':
                data = tdf_data(dot_d_path, sdk)
                num_frames = data.frames.shape[0] + 1
                scan_dicts = parse_maldi_tdf(data, 1, num_frames, 'centroid', False, True, 0, 64)
            maldi_spectra = []
            for count, scan_dict in enumerate(scan_dicts):
                scan_dict['index'] = count
                scan_dict['maldi spot identifier'] = scan_dict['coord']
                scan_dict['ms level'] = scan_dict['ms_level']
                scan_dict['m/z array'] = scan_dict['mz_array']
                scan_dict['intensity array'] = scan_dict['intensity_array']
                maldi_spectra.append(MALDISpectrum(scan_dict, dot_d_path))
            if args['trim_spectra']:
                maldi_spectra = trim_spectra(maldi_spectra,
                                             lower_mass_range=args['trim_spectra_lower_mass_range'],
                                             upper_mass_range=args['trim_spectra_upper_mass_range'])
            if args['transform_intensity']:
                maldi_spectra = transform_intensity(maldi_spectra, method=args['transform_intensity_method'])
            if args['smooth_baseline']:
                maldi_spectra = smooth_baseline(maldi_spectra,
                                                method=args['smooth_baseline_method'],
                                                window_length=args['smooth_baseline_window_length'],
                                                polyorder=args['smooth_baseline_polyorder'],
                                                delta_mz=args['smooth_baseline_delta_mz'],
                                                diff_thresh=args['smooth_baseline_diff_thresh'])
            if args['remove_baseline']:
                maldi_spectra = remove_baseline(maldi_spectra,
                                                method=args['remove_baseline_method'],
                                                lambda_=args['remove_baseline_lambda'],
                                                porder=args['remove_baseline_polyorder'],
                                                repitition=args['remove_baseline_repitition'],
                                                degree=args['remove_baseline_degree'],
                                                gradient=args['remove_baseline_gradient'])
            if args['normalize_intensity']:
                maldi_spectra = normalize_intensity(maldi_spectra, method=args['normalize_intensity_method'])
            if args['bin_spectra']:
                maldi_spectra = bin_spectra(maldi_spectra,
                                            n_bins=args['bin_spectra_n_bins'],
                                            lower_mass_range=args['bin_spectra_lower_mass_range'],
                                            upper_mass_range=args['bin_spectra_upper_mass_range'])
            if args['align_spectra']:
                maldi_spectra = align_spectra(maldi_spectra,
                                              method=args['align_spectra_method'],
                                              inter=args['align_spectra_inter'],
                                              n=args['align_spectra_n'],
                                              scale=args['align_spectra_scale'],
                                              coshift_preprocessing=args['align_spectra_coshift_preprocessing'],
                                              coshift_preprocessing_max_shift=args[
                                                  'align_spectra_coshift_preprocessing_max_shift'],
                                              fill_with_previous=args['align_spectra_fill_with_previous'],
                                              average2_multiplier=args['align_spectra_average2_multiplier'])
            for cont in spot_group:
                spectrum = [i for i in maldi_spectra if i.spot == cont.attrib['Pos_on_Scout']][0]
                # TODO: make pd df and get top n intensity features
                spectrum = peak_picking([spectrum],
                                        method=args['peak_picking_method'],
                                        widths=args['peak_picking_widths'],
                                        snr=args['peak_picking_snr'])[0]
                spectrum_mz_df = pd.DataFrame(data={'mz': spectrum.peak_picked_mz_array,
                                                    'intensity': spectrum.peak_picked_intensity_array})
                if args['blank'] != '':
                    merged_mz_df = pd.merge_asof(spectrum_mz_df,
                                                 exclusion_list_df.rename(columns={'mz': 'exclusion_list'}),
                                                 #on='mz',
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
    args = get_args()
    main(args)
