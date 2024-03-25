import os
import configparser
import datetime
import pytz
import tzlocal
import pandas as pd
import lxml.etree as et
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QSizePolicy, QHeaderView, \
    QAbstractItemView, QMessageBox
from ms1_autox_generator_template import Ui_MainWindow


def parse_maldi_plate_map(plate_map_filename):
    """
    Parse MALDI plate maps from *.csv files. Example plate maps for 48, 96, 384, 1536, and 6144 format plates are
    provided.

    :param plate_map_filename: Path to *.csv file containing plate map information.
    :type plate_map_filename: str
    :return: Dictionary containing sample names as keys and a list of MALDI plate coordinates as values.
    :rtype: dict
    """
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


def write_autox_seq(conditions_dict, methods, output_path, geometry_path):
    """
    Generate an AutoXecute sequence (*.run) file.

    :param conditions_dict: Dictionary containing sample names as keys and a list of MALDI plate coordinates as values.
    :type conditions_dict: dict
    :param methods: List of methods (*.m files) to be used in the AutoXecute run. Each method is passed to each
        coordinate to ensure that all each sample is run with each method.
    :type methods: list[str]
    :param output_path: Path to the *.run file that will be output.
    :type output_path: str
    :param geometry_path: Path to the geometry (*.xeo) file that this AutoXecute sequence will use.
    :type geometry_path: str
    :return: String containing any missed coordinates to be written to a log file.
    :rtype: str
    """
    # Stores any error_messages.
    messages = ''
    # Write out log.
    log_info = f'MALDI Plate Map: {output_path}\nMALDI Plate Geometry: {geometry_path}\n\nMethods\n'

    # Get AutoXecute attribute dict.
    autox_attrib = {'AnalysisSpectraType': 'Single_Spectra',
                    'DataStorage': 'Container',
                    'appname': 'timsControl',
                    # Initializes with hardcoded version but checks against currently installed timsControl version if
                    # available.
                    # Defaults to Compass 2024b SR1
                    'appVersion': '5.1.6_67f5008_1',
                    'cleanSourceAfterMeasurement': 'Off',
                    'date': datetime.datetime.now(pytz.timezone(tzlocal.get_localzone_name())).isoformat(),
                    'directory': os.path.split(output_path)[0],
                    'doBaselineSub': 'false',
                    'doSmoothing': 'false',
                    'ejectTargetAfterMeasurement': 'false',
                    'fragmentMass': '0.0',
                    'geometry': geometry_path,
                    'parentMass': '0.0',
                    'stopAfterMsMeasurement': 'false',
                    'targetID': '',
                    'type': 'SpotList',
                    'use1to1Preteaching': 'false',
                    'version': '2.0',
                    'executeExternalCalibration': 'true'}

    # Update timsControl version attribute if installed on the current system.
    if os.path.isfile('C:\\Program Files\\Bruker\\timsControl\\buildver.txt'):
        with open('C:\\Program Files\\Bruker\\timsControl\\buildver.txt', 'r') as timscontrol_build_ver:
            autox_attrib['appVersion'] = timscontrol_build_ver.read().strip()

    # Get spot position names from selected geometry file.
    geometree = et.parse(geometry_path)
    position_names = [element.get('PositionName') for element in geometree.xpath('//PlateSpots//*[@PositionName]')]

    # Write new AutoXecute *.run file.
    # Generate XML tree
    autox = et.Element('table', attrib=autox_attrib)
    for method in methods:
        log_info += method + '\n'
        for condition, list_of_spots in conditions_dict.items():
            spots_exist = [True if spot in position_names else False for spot in list_of_spots]
            if any(spots_exist):
                spot_group = et.SubElement(autox,
                                           'spot_group',
                                           attrib={'sampleName': f'{condition}_{os.path.splitext(os.path.split(method)[-1])[0]}',
                                                   'acqMethod': method})
                for spot in list_of_spots:
                    if spot in position_names:
                        cont = et.SubElement(spot_group,
                                             'cont',
                                             attrib={'Chip_on_Scout': '0',
                                                     'Pos_on_Scout': spot,
                                                     'acqJobMode': 'MS'})
                    else:
                        messages += f'{spot} not found on selected geometry and not added to the AutoXecute Sequence.\n'
            else:
                messages += (f'All spots for {condition} not found on selected geometry and not added to the '
                             f'Autoxecute Sequence.\n')
    # Write to *.run file.
    autox_tree = et.ElementTree(autox)
    autox_tree.write(output_path,
                     encoding='utf-8',
                     xml_declaration=True,
                     pretty_print=True)
    # Write out basic log file.
    with open(os.path.splitext(output_path)[0] + '.log', 'w') as logfile:
        logfile.write(log_info)

    return messages


class Gui(QMainWindow, Ui_MainWindow):
    """
    Class for the AutoXecute Sequence Generator GUI developed in PySide6. Inherits formatting from Qt Designer.
    """
    def __init__(self):
        super(Gui, self).__init__()

        self.setupUi(self)

        # Update QTableWidget settings
        self.MethodsTable.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.MethodsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.MethodsTable.verticalHeader().setVisible(False)
        self.MethodsTable.horizontalHeader().setVisible(False)
        self.MethodsTable.setColumnCount(1)
        self.MethodsTable.setHorizontalHeaderLabels(['Methods'])
        self.MethodsTable.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.MethodsTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.MethodsTable.setRowCount(0)

        # Initialize attributes.
        self.maldi_plate_map_path = ''
        self.methods = {}
        self.selected_row_from_table = ''

        # Populate dropdown with plate geometries.
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'etc', 'ms1_autox_generator.cfg'))
        self.geometry_paths = get_geometry_files(geometry_path=config['GeometryFiles']['path'].replace('/', '\\'))
        for key, value in self.geometry_paths.items():
            self.MaldiPlateGeometryCombo.addItem(key)

        # Connect buttons to methods.
        self.MaldiPlateMapButton.clicked.connect(self.select_maldi_plate_map)
        self.MethodsButton.clicked.connect(self.browse_methods)
        self.MethodsTable.selectionModel().selectionChanged.connect(self.select_from_methods_table)
        self.RemoveMethodsButton.clicked.connect(self.remove_methods)
        self.GenerateAutoXecuteButton.clicked.connect(self.run)
        self.ChangeGeometryFilesDirectory.triggered.connect(self.change_geometry_files_directory)

    def select_maldi_plate_map(self):
        """
        Open a file selection dialog to select the MALDI plate map.
        """
        self.maldi_plate_map_path = QFileDialog().getOpenFileName(self,
                                                                  'Select MALDI Plate Map...',
                                                                  '',
                                                                  filter='Comma Separated Values (*.csv)')
        self.maldi_plate_map_path = self.maldi_plate_map_path[0].replace('/', '\\')
        self.MaldiPlateMapLine.setText(self.maldi_plate_map_path)

    def browse_methods(self):
        """
        Open a file selection dialog to select a timsControl method (*.m file) or a folder containing multiple methods.
        """
        methods_path = QFileDialog().getExistingDirectory(self,
                                                          'Select Directory...',
                                                          '')
        if os.path.isdir(methods_path):
            if not methods_path.endswith('.m'):
                methods = [os.path.join(dirpath, directory)
                           for dirpath, dirnames, filenames in os.walk(methods_path)
                           for directory in dirnames
                           if directory.endswith('.m')]
            elif methods_path.endswith('.m'):
                methods = [methods_path]
            methods = [i.replace('/', '\\') for i in methods]
            old_row_count = self.MethodsTable.rowCount()
            self.MethodsTable.setRowCount(self.MethodsTable.rowCount() + len(methods))
            for row, i in enumerate(methods, start=old_row_count):
                new_key = os.path.split(i)[-1]
                if new_key in self.methods.keys():
                    copy_count = len([i for i in self.methods.keys() if i.startswith(new_key)])
                    new_key += f'({str(copy_count)})'
                self.methods[new_key] = i
                text_item = QTableWidgetItem(new_key)
                self.MethodsTable.setItem(row, 0, text_item)

    def select_from_methods_table(self):
        """
        Select a row from the Methods table.
        """
        self.selected_row_from_table = self.MethodsTable.selectionModel().selectedIndexes()

    def remove_methods(self):
        """
        Remove any selected methods from the Methods table.
        """
        for row in sorted([i.row() for i in self.selected_row_from_table], reverse=True):
            del self.methods[self.MethodsTable.item(row, 0).text()]
            self.MethodsTable.removeRow(row)

    def change_geometry_files_directory(self):
        """
        Edit the directory to load MALDI plate geometry (*.xeo) files from and save the new directory to the config
        file.
        """
        geometry_files_directory = QFileDialog().getExistingDirectory(self,
                                                                      'Select GeometryFiles Path...',
                                                                      '').replace('/', '\\')
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'etc', 'ms1_autox_generator.cfg'))
        config['GeometryFiles']['path'] = geometry_files_directory
        with open(os.path.join(os.path.dirname(__file__),
                               'etc',
                               'ms1_autox_generator.cfg'),
                  'w') as config_file:
            config.write(config_file)
        self.geometry_paths = get_geometry_files(geometry_path=geometry_files_directory)
        for key, value in self.geometry_paths.items():
            self.MaldiPlateGeometryCombo.addItem(key)

    def run(self):
        """
        Generate the AutoXecute sequence.
        """
        # Store error messages.
        err_msg = ''
        if self.maldi_plate_map_path == '':
            err_msg += '- MALDI plate map not selected. Select a plate map (*.csv) to continue.\n'
        if not self.methods:
            err_msg += '- No methods selected. Select at least one method to continue.\n'
        if err_msg != '':
            error_msg_box = QMessageBox(self)
            error_msg_box.setWindowTitle('Error')
            error_msg_box.setText(err_msg)
            error_msg_box.exec()

        # Process when all user input satisfied.
        if not self.maldi_plate_map_path == '' and self.methods:
            outfile = QFileDialog().getSaveFileName(self,
                                                    'Save AutoXecute Sequence...',
                                                    '',
                                                    filter='AutoXecute Sequence (*.run)')[0]
            messages = write_autox_seq(parse_maldi_plate_map(self.maldi_plate_map_path),
                                       self.methods,
                                       outfile,
                                       self.geometry_paths[str(self.MaldiPlateGeometryCombo.currentText())])

            # Completion dialog box and any errors.
            finished = QMessageBox(self)
            finished.setWindowTitle('AutoXecute Sequence Generator')
            finished.setText(f'The following AutoXecute Sequence has been created:\n{outfile}')
            finished.exec()
            if messages != '':
                messages_outfile = os.path.splitext(outfile)[0] + '.error'
                with open(messages_outfile, 'w') as logfile:
                    logfile.write(messages)
                error_msg_box = QMessageBox(self)
                error_msg_box.setWindowTitle('Error')
                error_msg_box.setText(f'Unable to write some samples from the provided plate map whose plate '
                                      f'coordinates were not found in the selected MALDI plate geometry. See '
                                      f'{messages_outfile} for more details')
                error_msg_box.exec()


def load_ui():
    """
    Load the GUI.
    """
    app = QApplication([])
    window = Gui()
    window.show()
    app.exec()


if __name__ == '__main__':
    load_ui()
