from setuptools import setup, find_packages

import nusbot


setup(
    name='nusbot',
    version='.'.join(str(e) for e in nusbot.__version__),
    description='adc bot annoucing changes in filelist of hub\'s users',
    url='https://github.com/kraiz/nusbot',
    license='MIT',
    entry_points = {
        'console_scripts': [
            'nusbot = nusbot.main:main',
        ],
    }
)
