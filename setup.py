from setuptools import setup

import nusbot


setup(
    name='nusbot',
    version=nusbot.__version__,
    description='adc bot annoucing changes in filelist of hub\'s users',
    url='https://github.com/kraiz/old_nusbot',
    license='MIT',
    packages=['nusbot', 'twisted.plugins'],
    install_requires=['twisted'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Information Technology',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: File Sharing',
    ],
)
