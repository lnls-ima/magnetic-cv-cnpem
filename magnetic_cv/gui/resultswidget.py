'''
Created on 6 de jul de 2023

@author: VitorPS
'''

import os as _os
import sys as _sys
import numpy as _np
import time as _time
import pandas as _pd
import shelve as _shelve
import traceback as _traceback

from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    QApplication as _QApplication,
    QVBoxLayout as _QVBoxLayout,
    )
from qtpy.QtCore import (
    Qt as _Qt,
    QTimer as _QTimer,
    )
import qtpy.uic as _uic

from magnetic_cv.gui.utils import (
    get_ui_file as _get_ui_file,
    )
from magnetic_cv.data import shelve_name

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as _FigureCanvas)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as _NavigationToolbar)
from matplotlib.figure import Figure


class MplCanvas(_FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = matplotlib.figure.Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class ResultsWidget(_QWidget):
    """Results widget class for the Vertical Cryostat characterization
     application."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.shelve_name = shelve_name

        self.set_pyplot()

        self.connect_signal_slots()

        self.update_meas_list()
        self.plot_measurement()

    def set_pyplot(self):
        """Configures plot widget"""
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        _toolbar = _NavigationToolbar(self.canvas, self)

        _layout = _QVBoxLayout()
        _layout.addWidget(self.canvas)
        _layout.addWidget(_toolbar)

        self.wg_plot.setLayout(_layout)

    def connect_signal_slots(self):
        """Create signal/slot connections."""
        self.ui.pbt_update.clicked.connect(self.update_meas_list)
        self.ui.cmb_meas_name.currentIndexChanged.connect(
            self.plot_measurement)
        self.ui.chb_hall1.stateChanged.connect(self.plot_measurement)
        self.ui.chb_hall2.stateChanged.connect(self.plot_measurement)
        self.ui.chb_hall3.stateChanged.connect(self.plot_measurement)
        self.ui.rdb_field.toggled.connect(self.plot_measurement)

    def update_meas_list(self):
        """Update measurement list in combobox."""
        try:
            self.ui.cmb_meas_name.currentIndexChanged.disconnect()
            with _shelve.open(self.shelve_name) as db:
                self.df_measurements = db['df_measurements']
            names = self.df_measurements['coil_name']
            cmb = self.ui.cmb_meas_name
            current_text = cmb.currentText()
            cmb.clear()
            cmb.addItems([name for name in names])
            if len(current_text) == 0:
                cmb.setCurrentIndex(cmb.count()-1)
            else:
                cmb.setCurrentText(current_text)
            self.ui.cmb_meas_name.currentIndexChanged.connect(
                self.plot_measurement)
        except Exception:
            self.ui.cmb_meas_name.currentIndexChanged.connect(
                self.plot_measurement)
            _traceback.print_exc(file=_sys.stdout)

    def plot_measurement(self):
        try:
            coil_name = self.ui.cmb_meas_name.currentText()
            df = self.df_measurements.loc[
                self.df_measurements['coil_name'] == coil_name]

            v1 = _np.array(df['V1[V]'].values[0][0])
            v2 = _np.array(df['V2[V]'].values[0][0])
            v3 = _np.array(df['V3[V]'].values[0][0])
            b1 = _np.array(df['B1[T]'].values[0][0])
            b2 = _np.array(df['B2[T]'].values[0][0])
            b3 = _np.array(df['B3[T]'].values[0][0])

            if self.ui.rdb_field.isChecked():
                y1_data = b1
                y2_data = b2
                y3_data = b3
                label = 'B'
                y_label = 'Magnetic Field [T]'
            else:
                y1_data = v1
                y2_data = v2
                y3_data = v3
                label = 'V'
                y_label = 'Voltage [V]'

            self.canvas.axes.cla()
            if self.ui.chb_hall1.isChecked():
                self.canvas.axes.plot(y1_data, 'o-', label=label+'1')
            if self.ui.chb_hall2.isChecked():
                self.canvas.axes.plot(y2_data, 'o-', label=label+'2')
            if self.ui.chb_hall3.isChecked():
                self.canvas.axes.plot(y3_data, 'o-', label=label+'3')

            self.canvas.axes.set_ylabel(y_label)
            self.canvas.axes.grid(1)
            self.canvas.axes.legend()
            self.canvas.figure.tight_layout()
            self.canvas.draw()

            self.ui.le_b1_mean.setText(f'{b1.mean():.7f}')
            self.ui.le_b2_mean.setText(f'{b2.mean():.7f}')
            self.ui.le_b3_mean.setText(f'{b3.mean():.7f}')
            self.ui.le_v1_mean.setText(f'{v1.mean():.7f}')
            self.ui.le_v2_mean.setText(f'{v2.mean():.7f}')
            self.ui.le_v3_mean.setText(f'{v3.mean():.7f}')
            self.ui.le_b1_std.setText(f'{b1.std():.7f}')
            self.ui.le_b2_std.setText(f'{b2.std():.7f}')
            self.ui.le_b3_std.setText(f'{b3.std():.7f}')
            self.ui.le_v1_std.setText(f'{v1.std():.7f}')
            self.ui.le_v2_std.setText(f'{v2.std():.7f}')
            self.ui.le_v3_std.setText(f'{v3.std():.7f}')

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
