import os
import sys
import copy
import gc
import argparse
from psims.mzml import MzMLWriter
from pyTDFSDK.init_tdf_sdk import *
from pyTDFSDK.classes import *

# Code modified from TIMSCONVERT 1.6.5.

INSTRUMENT_SOURCE_TYPE = {'0': 'unspecified',
                          '1': 'electrospray ionization',
                          '2': 'atmospheric pressure chemical ionization',
                          '3': 'nanoelectrospray',
                          '4': 'nanoelectrospray',
                          '5': 'atmospheric pressure photoionization',
                          '6': 'multimode ionization',
                          '9': 'nanoflow electrospray ionization',
                          '10': 'ionBooster',
                          '11': 'CaptiveSpray',
                          '12': 'GC-APCI',
                          '13': 'VIP-HESI-APCI',
                          '18': 'VIP-HESI'}


def get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('--input',
                        help='One or more MALDI-MS .d directories acquired from the timsTOF fleX in successive '
                             'AutoXecute runs with different, non-overlapping mass range windows.',
                        required=True,
                        type=str,
                        nargs='+')
    parser.add_argument('--output',
                        help='Name of the resulting mzML file.',
                        default='',
                        type=str)
    parser.add_argument('--mode',
                        help='Choose whether export to spectra in raw or centroid formats. Defaults to centroid.',
                        default='centroid',
                        type=str,
                        choices=['raw', 'centroid', 'profile'])
    parser.add_argument('--compression',
                        help='Choose between ZLIB compression (zlib) or no compression (none). Defaults to zlib.',
                        default='zlib',
                        type=str,
                        choices=['zlib', 'none'])
    parser.add_argument('--encoding',
                        help='Choose encoding for binary arrays: 32-bit (32) or 64-bit (64). Defaults to 64-bit.',
                        default=64,
                        type=int,
                        choices=[64, 32])
    parser.add_argument('--barebones_metadata',
                        help='Only use basic mzML metadata. Use if downstream data analysis tools throw errors with '
                             'descriptive CV terms.',
                        action='store_true')

    arguments = parser.parse_args()
    return vars(arguments)


class PartialTsfData(TsfData):
    def __init__(self, bruker_d_folder_name, tdf_sdk, use_recalibrated_state=True):
        super().__init__(bruker_d_folder_name, tdf_sdk, use_recalibrated_state)
        self.MzAcqRangeLower = float(self.analysis['GlobalMetadata']['MzAcqRangeLower'])
        self.MzAcqRangeUpper = float(self.analysis['GlobalMetadata']['MzAcqRangeUpper'])


def trim_spectrum(spectrum, lower_mass_range, upper_mass_range):
    indices = np.where((spectrum.mz_array > lower_mass_range) & (spectrum.mz_array <= upper_mass_range))[0]
    spectrum.mz_array = copy.deepcopy(spectrum.mz_array[indices])
    spectrum.intensity_array = copy.deepcopy(spectrum.intensity_array[indices])
    gc.collect()
    return spectrum


def i_activate_the_magic_card_polymerization(sorted_dlist_lower, frame, mode, encoding):
    spectra = [(TsfSpectrum(data, frame=frame, mode=mode, profile_bins=0, encoding=encoding),
                data)
               for data in sorted_dlist_lower]
    spectra = [(trim_spectrum(spectrum, data.MzAcqRangeLower, data.MzAcqRangeUpper),
                data)
               for spectrum, data in spectra]
    mz_arrays = [copy.deepcopy(spectrum.mz_array) for spectrum, data in spectra]
    intensity_arrays = [copy.deepcopy(spectrum.intensity_array)
                        for spectrum, data in spectra]
    fusion_mz_array = np.concatenate(mz_arrays)
    fusion_intensity_array = np.concatenate(intensity_arrays)
    return fusion_mz_array, fusion_intensity_array


def write_fusion_mzml_metadata(writer, dlist, filenames, mode, barebones_metadata):
    # Write controlled vocabularies
    writer.controlled_vocabularies()
    # Basic file descriptions.
    file_description = ['MS1 spectrum']
    if mode == 'raw' or mode == 'centroid':
        file_description.append('centroid spectrum')
    elif mode == 'profile':
        file_description.append('profile spectrum')
    # Source File
    sf = [writer.SourceFile(os.path.split(i)[0],
                            os.path.split(i)[1],
                            id=str(count))
          for count, i in enumerate(filenames)]
    writer.file_description(file_contents=file_description, source_files=sf)
    # Add list of software.
    if not barebones_metadata:
        acquisition_software = {'id': 'micrOTOFcontrol',
                                'version': dlist[0].analysis['GlobalMetadata']['AcquisitionSoftwareVersion'],
                                'params': ['micrOTOFcontrol', ]}
        tdf_sdk_software = {'id': 'TDF-SDK',
                            'version': '2.21.0.4',
                            'params': ['Bruker software']}
        psims_software = {'id': 'psims-writer',
                          'version': '1.2.7',
                          'params': ['python-psims', ]}
        flex_maldi_dda_automation_software = {'id': 'flex_maldi_dda_automation',
                                              'version': '0.4.0a1',
                                              'params': ['flex_maldi_dda_automation', ]}
        writer.software_list([acquisition_software,
                              tdf_sdk_software,
                              psims_software,
                              flex_maldi_dda_automation_software])
    # Instrument configuration.
    # Instrument source, analyzer, and detector are all hard coded to timsTOF hardware and does not allow for non-stock
    # configurations.
    inst_count = 1
    if dlist[0].analysis['GlobalMetadata']['InstrumentSourceType'] in INSTRUMENT_SOURCE_TYPE.keys() \
            and 'MaldiApplicationType' not in dlist[0].analysis['GlobalMetadata'].keys():
        source = writer.Source(inst_count,
                               [INSTRUMENT_SOURCE_TYPE[dlist[0].analysis['GlobalMetadata']['InstrumentSourceType']]])
    elif 'MaldiApplicationType' in dlist[0].analysis['GlobalMetadata'].keys():
        source = writer.Source(inst_count, ['matrix-assisted laser desorption ionization'])
    # Analyzer and detector hard coded for timsTOF fleX
    inst_count += 1
    analyzer = writer.Analyzer(inst_count, ['quadrupole', 'time-of-flight'])
    inst_count += 1
    detector = writer.Detector(inst_count, ['microchannel plate detector', 'photomultiplier'])
    # Get instrument serial number.
    serial_number = dlist[0].analysis['GlobalMetadata']['InstrumentSerialNumber']
    # Get instrument name based on GlobalMetadata or Properties table.
    if not barebones_metadata:
        instrument_name = dlist[0].analysis['GlobalMetadata']['InstrumentName'].strip().lower()
        if instrument_name == 'timstof':
            instrument_name = 'timsTOF'
        elif instrument_name == 'timstof pro':
            instrument_name = 'timsTOF Pro'
        elif instrument_name == 'timstof pro 2':
            instrument_name = 'timsTOF Pro 2'
        elif instrument_name == 'timstof flex':
            instrument_name = 'timsTOF fleX'
        elif instrument_name == 'timstof scp':
            instrument_name = 'timsTOF SCP'
        elif instrument_name == 'timstof ht':
            instrument_name = 'Bruker Daltonics timsTOF series'  # placeholder since HT doesn't have CV param
        elif instrument_name == 'timstof ultra':
            instrument_name = 'timsTOF Ultra'
        params = [instrument_name, {'instrument serial number': serial_number}]
    else:
        params = [{'instrument serial number': serial_number}]
    # Data processing element.
    if not barebones_metadata:
        proc_methods = [writer.ProcessingMethod(order=1,
                                                software_reference='psims-writer',
                                                params=['Conversion to mzML']),
                        writer.ProcessingMethod(order=2,
                                                software_reference='TDF-SDK',
                                                params=['Conversion to mzML']),
                        writer.ProcessingMethod(order=3,
                                                software_reference='flex_maldi_dda_automation',
                                                params=['Conversion to mzML'])]
        processing = writer.DataProcessing(proc_methods, id='exportation')
        writer.data_processing_list([processing])
    inst_config = writer.InstrumentConfiguration(id='instrument',
                                                 component_list=[source, analyzer, detector],
                                                 params=params)
    writer.instrument_configuration_list([inst_config])


def write_fusion_mzml(dlist, sorted_dlist_lower, filenames, output,
                      mode, compression, encoding, barebones_metadata):
    # initialize mzml writer
    writer = MzMLWriter(output, close=True)
    with writer:
        # Write mzML metadata.
        write_fusion_mzml_metadata(writer, dlist, filenames, mode, barebones_metadata)
        # Write spectra list.
        with writer.run(id='run',
                        instrument_configuration='instrument',
                        start_time=dlist[0].analysis['GlobalMetadata']['AcquisitionDateTime']):
            scan_count = 0
            with writer.spectrum_list(count=dlist[0].analysis['Frames'].shape[0]):
                # code to parse datasets into TsfSpectrum and append numpy arrays
                for frame in range(1, dlist[0].analysis['Frames'].shape[0] + 1):
                    # get a maldiframeinfo dict
                    maldiframeinfo_dict = \
                        dlist[0].analysis['MaldiFrameInfo'][dlist[0].analysis['MaldiFrameInfo']['Frame'] ==
                                                            frame].to_dict(orient='records')[0]
                    # get, trim, and stitch spectra
                    fusion_mz_array, fusion_intensity_array = i_activate_the_magic_card_polymerization(
                        sorted_dlist_lower,
                        frame,
                        mode,
                        encoding)
                    # Build params list for spectrum.
                    scan_count += 1
                    base_peak_index = np.where(fusion_intensity_array == np.max(fusion_intensity_array))
                    params = ['MS1 spectrum',
                              {'ms level': 1},
                              {'total ion current': sum(fusion_intensity_array)},
                              {'base peak m/z': fusion_mz_array[base_peak_index][0].astype(float)},
                              ({'name': 'base peak intensity',
                                'unit_name': 'number of detector counts',
                                'value': fusion_intensity_array[base_peak_index][0].astype(float)}),
                              {'highest observed m/z': float(max(fusion_mz_array))},
                              {'lowest observed m/z': float(max(fusion_mz_array))},
                              {'maldi spot identifier': get_maldi_coords(dlist[0],
                                                                         maldiframeinfo_dict)}]
                    encoding_dict = {'m/z array': get_encoding_dtype(encoding),
                                     'intensity array': get_encoding_dtype(encoding)}
                    # Write MS1 spectrum
                    writer.write_spectrum(fusion_mz_array,
                                          fusion_intensity_array,
                                          id='scan=' + str(scan_count),
                                          polarity=list(set(dlist[0].analysis['Frames']['Polarity'].values.tolist()))[
                                              0],
                                          centroided=get_centroid_status(mode)[0],
                                          scan_start_time=0,
                                          # other_arrays=None
                                          params=params,
                                          encoding=encoding_dict,
                                          compression=compression)


def run():
    # get args
    args = get_args()

    # read in datasets
    dll = init_tdf_sdk_api()
    dlist = [PartialTsfData(dfile, dll) for dfile in args['input']]
    # group dataset into a list (random order)
    masses = [x.MzAcqRangeLower for x in dlist] + [x.MzAcqRangeUpper for x in dlist]
    sorted_dlist_lower = sorted(dlist, key=lambda x: x.MzAcqRangeLower)  # sort by low to high lower mass range
    sorted_dlist_upper = sorted(dlist, key=lambda x: x.MzAcqRangeUpper)  # sort by low to high upper mass range

    # logic check to make sure mass ranges don't overlap
    # first check: make sure order of sorted lists are the same
    if sorted_dlist_lower == sorted_dlist_upper:
        # second check: make sure mass ranges don't overlap
        for i in range(0, len(dlist) - 1):
            if (not sorted_dlist_lower[i].MzAcqRangeUpper <= sorted_dlist_lower[i + 1].MzAcqRangeLower or
                    not sorted_dlist_upper[i].MzAcqRangeUpper <= sorted_dlist_upper[i + 1].MzAcqRangeLower):
                print('Overlapping mass range detected. Check input files.')
                sys.exit(1)
            else:
                # third check: make sure the first lower mass range is the lowest value of all and the last upper mass
                # range is the largest
                if (not sorted_dlist_lower[0].MzAcqRangeLower == min(masses) or
                        not sorted_dlist_upper[0].MzAcqRangeLower == min(masses) or
                        not sorted_dlist_lower[-1].MzAcqRangeUpper == max(masses) or
                        not sorted_dlist_upper[-1].MzAcqRangeUpper == max(masses)):
                    print('Overlapping mass range detected. Check input files.')
                    sys.exit(1)
                else:
                    # run the workflow
                    write_fusion_mzml(dlist,
                                      sorted_dlist_lower,
                                      args['input'],
                                      args['output'],
                                      args['mode'],
                                      args['compression'],
                                      args['encoding'],
                                      args['barebones_metadata'])

    else:
        print('Overlapping mass range detected. Check input files.')
        sys.exit(1)


if __name__ == '__main__':
    run()
