from setuptools import setup, find_packages


setup(
    name='nusbot',
    version='0.1.4',
    description='adc bot annoucing changes in filelist of hub\'s users',
    url='https://github.com/kraiz/nusbot',
    license='MIT',
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'nusbot = nusbot.main:main',
        ],
    }
)
