"""Run the cnpem vertical cryostat characterization application.

Created on 03 de julho de 2023

@author: VitorPS
"""

from magnetic_cv.gui import magnetic_cvapp

_run_in_thread = False


if _run_in_thread:
    thread = magnetic_cvapp.run_in_thread()
else:
    magnetic_cvapp.run()
