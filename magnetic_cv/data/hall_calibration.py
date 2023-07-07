'''
Hall sensors calibration data. 10th order polynomials are used up to +/- 2.019
T, which is the range for our local calibration and linear approximation is used
above +/- 2 T, which is an extrapolation from our calibration.
'''
import numpy as _np

# Hall sensor 1 calibration polynomials:
pol10_HGT1 = _np.poly1d([1.46883450e+02, -3.56191016e+02, -4.98744055e+01,
                         1.37550068e+02, 5.88276136e+00, -2.74125830e+01,
                         -2.80373132e-01,  4.22275310e+00, 7.44161467e-03,
                         -5.82513042e+00,  3.65729929e-04])
linear_HGT1 = _np.poly1d([-5.59894820e+00, 6.21908373e-04])

# Hall sensor 2 calibration polynomials:
pol10_HGT2 = _np.poly1d([2.23517339e+02, -2.24419834e+02, -7.94370061e+01,
                         9.97709068e+01, 9.70645129e+00, -2.33149119e+01,
                         -4.46049130e-01,  3.98251741e+00, 4.04120700e-03,
                         -5.76195306e+00,  8.09870141e-04])
linear_HGT2 = _np.poly1d([-5.53985044e+00, 8.42594745e-04])

# Hall sensor 3 calibration polynomials:
pol10_HGT3 = _np.poly1d([1.45438440e+02, -3.14966756e+02, -5.19738439e+01,
                         1.22231003e+02, 6.54236944e+00, -2.49287031e+01,
                         -3.52555693e-01,  3.96288138e+00, 1.13897757e-02,
                         -5.77974580e+00, -1.61299679e-03])
linear_HGT3 = _np.poly1d([-5.56333233e+00, -1.32398718e-03])


def voltage_to_tesla(v1=None, v2=None, v3=None, meas_temp=None):
    """Magnetic field calculation from the sensor voltages using sensor
    calibration. Uses 10th order polynomial if -2.019T<=field<=2.019T or linear
    aproximation if the field modulus extrapolates 2 T before temperature
    correction.

    Args:
        v1 (float): Hall sensor 1 voltage;
        v2 (float): Hall sensor 2 voltage;
        v3 (float): Hall sensor 3 voltage;
        meas_temp (float): PCB temperature in [k] during the measurement for
            temperature correction. No correction is applied if value is None.

    Returns:
        b (list): list of the magnetic field values. If any sensor voltage is
            None, the corresponding field will also be None. In the
            form [b1, b2, b3].
        """
    try:
        b = [None, None, None]
        if v1 is not None:
            b[0] = pol10_HGT1(v1)
            if abs(b[0]) > 2.019:
                b[0] = linear_HGT1(v1)
        if v2 is not None:
            b[1] = pol10_HGT2(v2)
            if abs(b[1]) > 2.019:
                b[1] = linear_HGT2(v2)
        if v3 is not None:
            b[2] = pol10_HGT3(v3)
            if abs(b[2]) > 2.019:
                b[2] = linear_HGT3(v3)

        # temperature correction:
        if meas_temp is not None:
            for i in range(len(b)):
                if b[i] is not None:
                    b[i] = temperature_correction(b[i], meas_temp)

        return b

    except Exception:
        raise


def temperature_correction(field, meas_temp, cal_temp=297.15,
                           sensitivity_var=-0.06):
    """Returns field value corrected with the sensor sensitivity variation with
    temperature. This approach is simplified and does not account for offset
    variation.

    Args:
        field (float): magnetic field in [T] calculated with room temperature
                       calibration;
        meas_temp (float): PCB temperature in [K] when the measurement was
                           made;
        cal_temp (float): Temperature during the sensor calibration, fixed
                          value of 297.15 K.
        sensitivity_var (float): sensitivity variation with temperature
                                 coefficient in [%/K] or [%/degC]
    Returns:
        corrected field (float: magnetic field in [T] corrected."""

    try:
        delta_temp = (meas_temp - cal_temp)
        coef = 1 + delta_temp*sensitivity_var/100
        corrected_field = coef*field

        return corrected_field

    except Exception:
        raise
