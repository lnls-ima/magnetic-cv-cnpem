import time
import numpy as np
import pyvisa as _visa

from imautils.devices import Agilent34970ALib as _Agilent34970ALib


class Multichannel(_Agilent34970ALib.Agilent34970AGPIB):
    """Multichannel class."""

    def __init__(self, log=False):
        """Initiaze variables and prepare logging.

        Args:
            log (bool): True to use event logging, False otherwise.
        """
        super().__init__(log=log)
        self.voltage_channels = ['101', '102', '103']

    def connect(self, address, timeout=1000):
        "Connection, address=address"
        resource_manager = _visa.ResourceManager()
        #self.inst = resource_manager.open_resource(address)

        try:
            #self.inst = inst
            self.inst = resource_manager.open_resource(address)
            self.inst.timeout = timeout
            return True
        except Exception:
            self.inst.close()
            if self.logger is not None:
                self.logger.error('exception', exc_info=True)
            return False

        except Exception:
            if self.logger is not None:
                self.logger.error('exception', exc_info=True)
            return None

    def read_volt(self, I, B, n_points=100, comments='', log=False):
        header = f'I[A]={I}\nB[T]={B}\nn_points={n_points}\n'\
                 f'Comments: {comments}\n\n'\
        'V1_mean[V]\tV1_std[V]\tV2_mean[V]\tV2_std[V]\tV3_mean[V]\tV3_std[V]'
        name = time.strftime('%y_%m_%d-%Hh%M-') + f'I={I}A_B={B}T.dat'

        voltages = []
        for i in range(100):
            _readdings = multich.get_readings()
            if _readdings == []:
                raise ValueError('Unable to read the multichannel. Try reconnecting.')
            else:
                voltages.append(_readdings)
        voltages = np.array(voltages)
        results = np.array([voltages[:,0].mean(), voltages[:,0].std(),
                            voltages[:,1].mean(), voltages[:,1].std(),
                            voltages[:,2].mean(), voltages[:,2].std()])
        if log:
            np.savetxt(name, results.reshape([1,6]), fmt='%.6E',
                       delimiter='\t', header=header, comments='')

        return results, voltages

multich = Multichannel(log=True)