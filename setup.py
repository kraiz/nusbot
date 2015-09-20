from setuptools import setup

import nusbot


setup(
    name='nusbot',
    version=nusbot.__version__,
    description='adc bot annoucing changes in filelist of hub\'s users',
    url='https://github.com/kraiz/nusbot',
    author='Lars Kreisz',
    author_email='lars.kreisz@gmail.com',
    license='MIT',
    packages=['nusbot', 'twisted.plugins'],
    install_requires=['twisted'],
    long_description=open('README.rst').read() + '\n\n' + open('CHANGES.rst').read(),
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
