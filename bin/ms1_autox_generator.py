import os
import sys
import winreg
import datetime
import pytz
import tzlocal
import numpy as np
import pandas as pd
import lxml.etree as et
from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader


def parse_maldi_plate_map(plate_map_filename):
    # TODO: add check to make sure the plate map position exists in the selected geometry file
    plate_map = pd.read_csv(plate_map_filename, index_col=0)
    plate_dict = {}
    for index, row in plate_map.iterrows():
        for count, value in enumerate(row, start=1):
            plate_dict[f'{index}{str(count)}'] = value
    conditions = list(dict.fromkeys([str(value) for key, value in plate_dict.items()]))
    conditions_dict = {i: [] for i in conditions}
    for key, value in plate_dict.items():
        try:
            conditions_dict[value].append(key)
        except KeyError:
            pass
    return conditions_dict


def get_geometry_files(geometry_path='D:\\Methods\\GeometryFiles'):
    # TODO: use this function in UI to get list to populate dropdown menu
    # Get list of .xeo geometry files from the GeometryFiles path.
    geometry_files = [os.path.join(dirpath, filename)
                      for dirpath, dirnames, filenames in os.walk(geometry_path)
                      for filename in filenames
                      if os.path.splitext(filename)[1] == '.xeo']
    geometry_files_subset = []
    for geometry in geometry_files:
        with open(geometry, 'r') as geometry_object:
            if 'flexImaging' not in geometry_object.read():
                geometry_files_subset.append(geometry)
    return geometry_files_subset


def write_autox_seq(conditions_dict, methods, output_path):
    # TODO: will need check in ui to make sure method exists
    autox_attrib = {'AnalysisSpectraType': 'Single_Spectra',
                    'DataStorage': 'Container',
                    'appname': 'timsControl',
                    'appVersion': None,  # TODO: figure out how to get installed timsControl version
                    'cleanSourceAfterMeasurement': 'Off',
                    'date': datetime.datetime.now(pytz.timezone(tzlocal.get_localzone_name())).isoformat(),
                    'directory': None,
                    'doBaselineSub': 'false',
                    'doSmoothing': 'false',
                    'ejectTargetAfterMeasurement': 'false',
                    'fragmentMass': '0.0',
                    'geometry': None,  # TODO: parse geometries from geometry directory; have config file to change geometry directory too; or fallback to default geometries
                    'parentMass': '0.0',
                    'stopAfterMsMeasurement': 'false',
                    'targetID': '',
                    'type': 'SpotList',
                    'use1to1Preteaching': 'false',
                    'version': '2.0',
                    'executeExternalCalibration': 'true'}
    autox = et.Element('table', attrib=autox_attrib)
    for method in methods:
        for condition, list_of_spots in conditions_dict:
            spot_group = et.SubElement(autox,
                                       'spot_group',
                                       attrib={'sampleName': f'{condition}_{os.path.splitext(os.path.split(method)[-1])[0]}',
                                               'acqMethod': method})
            for spot in list_of_spots:
                cont = et.SubElement(spot_group,
                                     'cont',
                                     attrib={'Chip_on_Scout': '0',
                                             'Pos_on_Scout': spot,
                                             'acqJobMode': 'MS'})
    autox_tree = et.ElementTree(autox)
    # TODO: gui file dialog will supply file path
    autox_tree.write(output_path,
                     encoding='utf-8',
                     xml_declaration=True,
                     pretty_print=True)


def load_ui():
    loader = QUiLoader()
    app = QtWidgets.QApplication()
    window = loader.load('..\\ms1_autox_generator.ui', None)
    window.MaldiPlateGeometryCombo()
    window.show()
    app.exec()


if __name__ == '__main__':
    #conditions = parse_maldi_plate_map('C:\\Users\\bass\\data\\20240322_autox_windows\\strains_map.csv')
    #method_files = ''
    #autox_tree = et.parse('C:\\Users\\bass\\data\\UCSC_Robbie_MALDI\\UCSC_Robbie_MALDI\\240315\\Bsub_MALDI_DDA_MR1\\Bsub_MALDI_DDA_MR1.run')
    #autox = autox_tree.getroot()
    #for key, value in autox.attrib.items():
    #    print(f'{key}: {value}')
    load_ui()
    #write_autox_seq('', '', 'test.run')
