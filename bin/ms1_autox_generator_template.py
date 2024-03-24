# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ms1_autox_generator.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTableWidget,
    QTableWidgetItem, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(400, 520)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(400, 520))
        MainWindow.setMaximumSize(QSize(400, 520))
        self.ChangeGeometryFilesDirectory = QAction(MainWindow)
        self.ChangeGeometryFilesDirectory.setObjectName(u"ChangeGeometryFilesDirectory")
        self.CentralWidget = QWidget(MainWindow)
        self.CentralWidget.setObjectName(u"CentralWidget")
        self.MethodsTable = QTableWidget(self.CentralWidget)
        self.MethodsTable.setObjectName(u"MethodsTable")
        self.MethodsTable.setGeometry(QRect(20, 150, 361, 192))
        self.MaldiPlateMapLabel = QLabel(self.CentralWidget)
        self.MaldiPlateMapLabel.setObjectName(u"MaldiPlateMapLabel")
        self.MaldiPlateMapLabel.setGeometry(QRect(20, 10, 361, 16))
        self.MaldiPlateMapLine = QLineEdit(self.CentralWidget)
        self.MaldiPlateMapLine.setObjectName(u"MaldiPlateMapLine")
        self.MaldiPlateMapLine.setGeometry(QRect(20, 40, 281, 22))
        self.MaldiPlateMapLine.setReadOnly(True)
        self.MaldiPlateMapButton = QPushButton(self.CentralWidget)
        self.MaldiPlateMapButton.setObjectName(u"MaldiPlateMapButton")
        self.MaldiPlateMapButton.setGeometry(QRect(310, 40, 71, 24))
        self.MethodsLabel = QLabel(self.CentralWidget)
        self.MethodsLabel.setObjectName(u"MethodsLabel")
        self.MethodsLabel.setGeometry(QRect(20, 80, 361, 16))
        self.MethodsButton = QPushButton(self.CentralWidget)
        self.MethodsButton.setObjectName(u"MethodsButton")
        self.MethodsButton.setGeometry(QRect(20, 110, 361, 24))
        self.MaldiPlateGeometryLabel = QLabel(self.CentralWidget)
        self.MaldiPlateGeometryLabel.setObjectName(u"MaldiPlateGeometryLabel")
        self.MaldiPlateGeometryLabel.setGeometry(QRect(20, 360, 361, 16))
        self.GenerateAutoXecuteButton = QPushButton(self.CentralWidget)
        self.GenerateAutoXecuteButton.setObjectName(u"GenerateAutoXecuteButton")
        self.GenerateAutoXecuteButton.setGeometry(QRect(20, 430, 361, 24))
        self.MaldiPlateGeometryCombo = QComboBox(self.CentralWidget)
        self.MaldiPlateGeometryCombo.setObjectName(u"MaldiPlateGeometryCombo")
        self.MaldiPlateGeometryCombo.setGeometry(QRect(20, 390, 361, 22))
        MainWindow.setCentralWidget(self.CentralWidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.MenuBar = QMenuBar(MainWindow)
        self.MenuBar.setObjectName(u"MenuBar")
        self.MenuBar.setGeometry(QRect(0, 0, 400, 22))
        self.Settings = QMenu(self.MenuBar)
        self.Settings.setObjectName(u"Settings")
        MainWindow.setMenuBar(self.MenuBar)

        self.MenuBar.addAction(self.Settings.menuAction())
        self.Settings.addAction(self.ChangeGeometryFilesDirectory)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"AutoXecute Sequence Generator", None))
        self.ChangeGeometryFilesDirectory.setText(QCoreApplication.translate("MainWindow", u"Edit Path to \"GeometryFiles\" Directory", None))
        self.MaldiPlateMapLabel.setText(QCoreApplication.translate("MainWindow", u"MALDI Plate Map", None))
        self.MaldiPlateMapButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.MethodsLabel.setText(QCoreApplication.translate("MainWindow", u"Methods", None))
        self.MethodsButton.setText(QCoreApplication.translate("MainWindow", u"Load Method(s)", None))
        self.MaldiPlateGeometryLabel.setText(QCoreApplication.translate("MainWindow", u"MALDI Plate Geometry", None))
        self.GenerateAutoXecuteButton.setText(QCoreApplication.translate("MainWindow", u"Generate AutoXecute Sequence", None))
        self.Settings.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
    # retranslateUi

