'''
Created on 3 de jul de 2023

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
from magnetic_cv.devices import multich
from magnetic_cv.data.hall_calibration import voltage_to_tesla
from magnetic_cv.data import shelve_name

from epics import caget

class MeasurementWidget(_QWidget):
    """Measurement widget class for the Vertical Cryostat characterization
     application."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.cfg = {}
        # self.cfg['read_sensor'] = [True, True, True]

        self.shelve_name = shelve_name

        self.temp_pv_failure = 0
        self.current_pv_failure = 0

        try:
            with _shelve.open(self.shelve_name) as db:
                self.df_measurements = db['df_measurements']
            coil_name = self.df_measurements.iloc[-1]['coil_name']
            coil_name = '-'.join(coil_name.split('-')[2:])
            self.ui.le_coil.setText(coil_name)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.df_measurements = None

        self.timer = _QTimer()

        self.connect_signal_slots()

    def connect_signal_slots(self):
        """Create signal/slot connections."""
        self.ui.pbt_connect.clicked.connect(self.connect_multichannel)
        self.ui.pbt_disconnect.clicked.connect(self.disconnect_multichannel)
        self.ui.pbt_start_measurement.clicked.connect(
            self.start_measurement)
        self.ui.pbt_update.clicked.connect(self.update)
        self.ui.chb_monitor.stateChanged.connect(self.monitor)
        self.timer.timeout.connect(self.update_measurement)

    def enable_buttons(self, connected):
        """Enables/disables buttons"""
        if connected:
            self.ui.pbt_connect.setEnabled(False)
            self.ui.pbt_disconnect.setEnabled(True)
            self.ui.pbt_start_measurement.setEnabled(True)
            # self.ui.pbt_stop_measurement.setEnabled(True)
            self.ui.pbt_update.setEnabled(True)
            self.ui.chb_monitor.setEnabled(True)
            # self.ui.pbt_configure_meas.setEnabled(True)
        else:
            self.ui.pbt_connect.setEnabled(True)
            self.ui.pbt_disconnect.setEnabled(False)
            self.ui.pbt_start_measurement.setEnabled(False)
            # self.ui.pbt_stop_measurement.setEnabled(False)
            self.ui.pbt_update.setEnabled(False)
            self.ui.chb_monitor.setEnabled(False)
            # self.ui.pbt_configure_meas.setEnabled(False)

    def connect_multichannel(self):
        """Connects to multichannel agilent 34970A."""
        try:
            _device_name = self.ui.le_multich_name.text()
            multich.connect(_device_name)
            self.configure_multichannel()
            self.enable_buttons(connected=True)
            _QMessageBox.information(self, 'Information',
                                     'Multichannel connected',
                                     _QMessageBox.Ok)
        except Exception:
            self.enable_buttons(connected=False)
            _QMessageBox.warning(self, 'Warning',
                                     'Error connecting the multichannel.',
                                     _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)

    def disconnect_multichannel(self):
        """Disonnects to multichannel agilent 34970A."""
        try:
            multich.disconnect()
            self.enable_buttons(connected=False)
            _QMessageBox.information(self, 'Information',
                                     'Multichannel disconnected.',
                                     _QMessageBox.Ok)
        except Exception:
            self.enable_buttons(connected=True)
            _QMessageBox.warning(self, 'Warning',
                                     'Error disconnecting the multichannel.',
                                     _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)

    def configure_measurement(self):
        """Configures measurement."""
        try:
            # self.cfg['read_sensor'] = [self.ui.chb_hall1.isChecked(),
            #                           self.ui.chb_hall2.isChecked(),
            #                           self.ui.chb_hall3.isChecked()]
            # self.cfg['temperature'] = self.ui.dsb_temperature.value()
            # self.cfg['current'] = self.ui.dsb_current.value()
            self.cfg['npoints'] = self.ui.spb_npoints.value()
            self.cfg['sensitivity_var'] = self.ui.dsb_sense_var.value()
            self.cfg['temp_correction'] = \
                self.ui.chb_temp_correction.isChecked()
            self.cfg['savefile'] = self.ui.chb_savefile.isChecked()

            _coil_name = self.ui.le_coil.text()
            if _coil_name != '':
                self.cfg['coil_name'] = _coil_name
            else:
                msg = 'Please, name the coil.'
                _QMessageBox.information(self, 'Information',
                                         msg,
                                         _QMessageBox.Ok)
                raise ValueError(msg)

            # _QMessageBox.information(self, 'Information',
            #                          'Measurement configured succesfully.',
            #                          _QMessageBox.Ok)
            return True
        except Exception:
            _QMessageBox.warning(self, 'Warning',
                                     'Error configuring the measurement.',
                                     _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def start_measurement(self):
        """Starts a measurement."""
        try:
            self.configure_measurement()

            meas = []
            for i in range(self.cfg['npoints']):
                meas.append(self.measure_field())
                if meas[-1] is False:
                    meas[-1] = self.measure_field()
                    if meas[-1] is False:
                        raise RuntimeError('Unable to read the multichannel.')
                _QApplication.processEvents()
            meas = _np.array(meas)

            date = meas[:, 0]
            time = meas[:, 1]
            v1 = meas[:, 2].astype(float)
            v2 = meas[:, 3].astype(float)
            v3 = meas[:, 4].astype(float)
            b1 = meas[:, 5].astype(float)
            b2 = meas[:, 6].astype(float)
            b3 = meas[:, 7].astype(float)
            temp = meas[:, 8].astype(float)
            current = meas[:, 9].astype(float)

            df = _pd.DataFrame([self.cfg])
            df['coil_name'] = _time.strftime('%y_%m_%d-%H_%M_%S-') +\
                              df['coil_name']
            # cols = ['date', 'time', 'V1[V]', 'V2[V]', 'V3[V]',
            #         'B1[T]', 'B2[T]', 'B3[T]']
            cols = ['date', 'time',
                        'V1[V]', 'V2[V]', 'V3[V]',
                        'B1[T]', 'B2[T]', 'B3[T]',
                        'T[K]', 'I[A]']
            data = [[date.tolist()], [time.tolist()],
                    [v1.tolist()], [v2.tolist()], [v3.tolist()],
                    [b1.tolist()], [b2.tolist()], [b3.tolist()],
                    [temp.tolist()], [current.tolist()]]

            for i in range(len(cols)):
                df.insert(df.shape[1], cols[i], [data[i]])

            if self.df_measurements is None:
                self.df_measurements = df.copy()
            else:
                self.df_measurements = self.df_measurements.append(df, True)

            # print(self.df_measurements)
            with _shelve.open(self.shelve_name) as db:
                db['df_measurements'] = self.df_measurements

            msg = 'Measurement Results:\n\n'
            msg += f'B1 [T] = {b1.mean():.6f} +/- {b1.std():.6f}\n'
            msg += f'B2 [T] = {b2.mean():.6f} +/- {b2.std():.6f}\n'
            msg += f'B3 [T] = {b3.mean():.6f} +/- {b3.std():.6f}\n'
            msg += f'V1 [V] = {v1.mean():.6f} +/- {v1.std():.6f}\n'
            msg += f'V2 [V] = {v2.mean():.6f} +/- {v2.std():.6f}\n'
            msg += f'V3 [V] = {v3.mean():.6f} +/- {v3.std():.6f}\n'
            self.update_lcd(v1.mean(), v2.mean(), v3.mean(),
                            b1.mean(), b2.mean(), b3.mean())

            if self.cfg['savefile']:
                # self.save_meas_file(meas)
                self.save_meas_file(self.df_measurements.iloc[-1])

            _QMessageBox.information(self, 'Results',
                                     msg,
                                     _QMessageBox.Ok)
        except Exception:
            _QMessageBox.warning(self, 'Warning',
                                 'Error during the measurement.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def configure_multichannel(self):
        """Configures multichannel according to measurements configuration."""
        try:
            if multich.inst is None:
                msg = 'Please, connect the multichannel'
                _QMessageBox.information(self, 'Information',
                                         msg,
                                         _QMessageBox.Ok)
                return False
            # channel_list = []
            # if self.cfg['read_sensor'][0]:
            #     channel_list.append('101')
            # if self.cfg['read_sensor'][1]:
            #     channel_list.append('102')
            # if self.cfg['read_sensor'][2]:
            #     channel_list.append('103')
            channel_list = ['101', '102', '103']

            multich.configure(channel_list)
            return True
        except Exception:
            _QMessageBox.warning(self, 'Warning',
                                 'Error configuring the multichannel.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def measure_field(self):
        """Measures hall sensors.
        Returns:
            list: [date, time, v1, v2, v3, b1, b2, b3, temperature, current]"""
        try:
            if multich.inst is None:
                msg = 'Please, connect the multichannel'
                _QMessageBox.information(self, 'Information',
                                         msg,
                                         _QMessageBox.Ok)
                return False

            date = _time.strftime('%y/%m/%d')
            time = _time.strftime('%H:%M:%S')
            v1, v2, v3 = multich.get_readings()

            # Get PCB temperature
            if self.cfg['temp_correction']:
                temperature = self.ui.dsb_temperature.value()
                if self.chb_temp_frm_pv.isChecked():
                    pv_temp = self.ui.le_pv_temp.text()
                    temp = caget(pv_temp)
                    if temp is not None:
                        self.temp_pv_failure = 0
                        temperature = temp
                    else:
                        self.temp_pv_failure += 1
                        msg = _time.strftime("%y/%m/%d %H:%M:%S - ")
                        msg += "Couldn't read temperature PV, getting "\
                            "temperature from GUI."
                        print(msg)
                        if self.temp_pv_failure > 5:
                            self.chb_temp_frm_pv.setChecked(False)
                            msg = _time.strftime("%y/%m/%d %H:%M:%S - ")
                            msg += "Failed to read temperature PV 5 "\
                                "times in a row, from now on, temperature "\
                                "will be read from GUI."
                            print(msg)
            else:
                temperature = None

            # Get coil current
            current = self.ui.dsb_current.value()
            if self.chb_current_frm_pv.isChecked():
                pv_current = self.ui.le_pv_current.text()
                current_value = caget(pv_current)
                if current_value is not None:
                    self.current_pv_failure = 0
                    current = current_value
                else:
                    self.current_pv_failure += 1
                    msg = _time.strftime("%y/%m/%d %H:%M:%S - ")
                    msg += "Couldn't read current PV, getting "\
                        "current from GUI."
                    print(msg)
                    if self.current_pv_failure > 5:
                        self.chb_current_frm_pv.setChecked(False)
                        msg = _time.strftime("%y/%m/%d %H:%M:%S - ")
                        msg += "Failed to read current PV 5 "\
                            "times in a row, from now on, current "\
                            "will be read from GUI."
                        print(msg)

            b1, b2, b3 = voltage_to_tesla(v1, v2, v3, temperature)

            with open('last_results.txt', 'w') as f:
                header = 'V1[V]\tV2[V]\tV3[V]\tB1[T]\tB2[T]\tB3[T]\t'\
                         'T[K]\tI[A]\tdate\ttime\n'
                f.write(header)
                data = f'{v1}\t{v2}\t{v3}\t{b1}\t{b2}\t{b3}\t'\
                       f'{temperature}\t{current}\t{date}\t{time}'
                f.write(data)

            return date, time, v1, v2, v3, b1, b2, b3, temperature, current
        except KeyError:
            msg = 'Please check if you configured the measurement correctly.'
            _QMessageBox.warning(self, 'Warning',
                                 msg,
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False
        except Exception:
            _QMessageBox.warning(self, 'Warning',
                                 'Error reading the multichannel.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def update_measurement(self):
        """Updates measurement."""
        try:
            date, time, v1, v2, v3, b1, b2, b3, tmp, cur = self.measure_field()
            self.update_lcd(v1, v2, v3, b1, b2, b3)

            if self.ui.chb_log_monitor.isChecked():
                cols = ['date', 'time',
                        'V1[V]', 'V2[V]', 'V3[V]',
                        'B1[T]', 'B2[T]', 'B3[T]',
                        'T[K]', 'I[A]']
                data = [_np.array([date]), _np.array([time]),
                        _np.array([v1]), _np.array([v2]), _np.array([v3]),
                        _np.array([b1]), _np.array([b2]), _np.array([b3]),
                        _np.array([tmp]), _np.array([cur])]
                # icols = ['coil_name', 'current', 'npoints', 'savefile',
                #          'sensitivity_var', 'temp_correction', 'temperature']
                icols = ['coil_name',  'npoints', 'savefile',
                         'sensitivity_var', 'temp_correction']
                df = _pd.DataFrame(self.df_measurements.iloc[-1][icols])

                index = self.df_measurements.shape[0]-1
                for i in range(len(cols)):
                    data[i] = _np.append(
                        self.df_measurements.iloc[-1][cols[i]], data[i])
                    self.df_measurements.loc[index, cols[i]] = [
                        [data[i].tolist()]]

                self.df_measurements.loc[index, 'npoints'] = len(
                    self.df_measurements.iloc[-1][cols[3]][0])

                with _shelve.open(self.shelve_name) as db:
                    db['df_measurements'] = self.df_measurements

        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def update_lcd(self, v1, v2, v3, b1, b2, b3):
        """Update lcds with measurement results."""
        try:
            self.ui.lcd_v1.display(v1*1e3)
            self.ui.lcd_v2.display(v2*1e3)
            self.ui.lcd_v3.display(v3*1e3)
            self.ui.lcd_b1.display(b1)
            self.ui.lcd_b2.display(b2)
            self.ui.lcd_b3.display(b3)
            _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def update(self):
        """Interface for update button."""
        self.configure_measurement()
        self.update_measurement()

    def monitor(self):
        """Monitors field"""
        try:
            if self.ui.chb_monitor.isChecked():
                self.configure_measurement()
                df_monitor = _pd.DataFrame([self.cfg])
                name_prefix = _time.strftime('%y_%m_%d-%H_%M_%S-')
                df_monitor['coil_name'] = name_prefix + df_monitor['coil_name']
                df_monitor['npoints'] = None
                # cols = ['date', 'time', 'V1[V]', 'V2[V]', 'V3[V]',
                #         'B1[T]', 'B2[T]', 'B3[T]']
                cols = ['date', 'time',
                        'V1[V]', 'V2[V]', 'V3[V]',
                        'B1[T]', 'B2[T]', 'B3[T]',
                        'T[K]', 'I[A]']

                meas = self.measure_field()
                if meas is False:
                    meas = self.measure_field()
                    if meas is False:
                        raise RuntimeError('Unable to read the multichannel.')
                date = _np.array([meas[0]])
                time = _np.array([meas[1]])
                v1 = _np.array([meas[2]])
                v2 = _np.array([meas[3]])
                v3 = _np.array([meas[4]])
                b1 = _np.array([meas[5]])
                b2 = _np.array([meas[6]])
                b3 = _np.array([meas[7]])
                temp = _np.array([meas[8]])
                current = _np.array([meas[9]])
                data = [[date], [time], [v1], [v2], [v3], [b1], [b2], [b3],
                        [temp], [current]]
                _QApplication.processEvents()
                for i in range(len(cols)):
                    df_monitor.insert(df_monitor.shape[1], cols[i], data[i])

                if self.df_measurements is None:
                    self.df_measurements = df_monitor.copy()
                else:
                    self.df_measurements = (
                        self.df_measurements.append(df_monitor, True))

                period = self.ui.spb_update_rate.value()*1000
                self.timer.start(period)
                self.ui.spb_update_rate.setEnabled(False)
                # self.ui.pbt_start_measurement.setEnabled(False)
                self.ui.gpb_cfg.setEnabled(False)
            else:
                self.timer.stop()
                if self.ui.chb_log_monitor.isChecked():
                    self.save_meas_file(self.df_measurements.iloc[-1])
                self.ui.spb_update_rate.setEnabled(True)
                # self.ui.pbt_start_measurement.setEnabled(True)
                self.ui.gpb_cfg.setEnabled(True)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.timer.stop()
            self.ui.spb_update_rate.setEnabled(True)

    def save_meas_file(self, df):
        """Saves measurement to file."""

        date = _np.array(df['date'][0])
        time = _np.array(df['time'][0])
        v1 = _np.array(df['V1[V]'][0])
        v2 = _np.array(df['V2[V]'][0])
        v3 = _np.array(df['V3[V]'][0])
        b1 = _np.array(df['B1[T]'][0])
        b2 = _np.array(df['B2[T]'][0])
        b3 = _np.array(df['B3[T]'][0])
        temp = _np.array(df['T[K]'][0])
        current = _np.array(df['I[A]'][0])

        results = 'V1_mean[V]\tV1_std[V]\tV2_mean[V]\tV2_std[V]\t'\
                  'V3_mean[V]\tV3_std[V]\tB1_mean[T]\tB1_std[T]\t'\
                  'B2_mean[T]\tB2_std[T]\tB3_mean[T]\tB3_std[T]\n'\
                  f'{v1.mean():.7f}\t{v1.std():.7f}\t'\
                  f'{v2.mean():.7f}\t{v2.std():.7f}\t'\
                  f'{v3.mean():.7f}\t{v3.std():.7f}\t'\
                  f'{b1.mean():.7f}\t{b1.std():.7f}\t'\
                  f'{b2.mean():.7f}\t{b2.std():.7f}\t'\
                  f'{b3.mean():.7f}\t{b3.std():.7f}\n'

        name_date = _time.strftime('%y/%m/%d')
        name_time = _time.strftime('%H:%M:%S')
        filename = name_date.replace('/', '_') + '-' + name_time.replace(':', '_') + '-'
        filename += self.cfg['coil_name'] + '.csv'

        coil_name = self.cfg['coil_name']
        # temp = self.cfg['temperature']
        # cur = self.cfg['current']
        npoints = df['npoints']
        # sens = self.cfg['sensitivity_var']
        correction = self.cfg['temp_correction']
        # header = f'Coil Name: {coil_name}\nI [A]: {cur:.3f}\n'\
        #          f'Number of points: {npoints}\n'\
        #          f'PCB temperature [k]: {temp:.4f}\n'\
        #          f'Temperature Correction: {correction}\n'\
        #          f'{results}\n'\
        #          'date\ttime\tV1[V]\tV2[V]\tV3[V]\tB1[T]\tB2[T]\tB3[T]\n'
        header = f'Coil Name: {coil_name}\n'\
                 f'Number of points: {npoints}\n'\
                 f'Temperature Correction: {correction}\n'\
                 f'{results}\n'\
                 'date\ttime\tV1[V]\tV2[V]\tV3[V]\tB1[T]\tB2[T]\tB3[T]\t'\
                 'T[K]\tI[A]\n'

        with open(filename, 'w') as f:
            f.write(header)
            for i in range(len(v1)):
                line = f'{date[i]}\t{time[i]}\t{v1[i]}\t'\
                       f'{v2[i]}\t{v3[i]}\t{b1[i]}\t'\
                       f'{b2[i]}\t{b3[i]}\t{temp[i]}\t{current[i]}\n'
                f.write(line)
