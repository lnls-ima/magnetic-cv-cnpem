
import os
from setuptools import setup, find_packages


basedir = os.path.dirname(__file__)
with open(os.path.join(basedir, 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()


setup(
    name='magnetic-cv-cnpem',
    version=__version__,
    description="Magnet's group interface for cnpem version of "\
                "vertical cryostat magnetic characterization of SC coils.",
    url='https://github.com/lnls-ima/magnetic-cv-cnpem',
    author='lnls-ima',
    license='GNU License',
    packages=find_packages(),
    install_requires=[
        'qtpy',
    ],
    package_data={'magnetic_cv': ['VERSION']},
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False,
)
