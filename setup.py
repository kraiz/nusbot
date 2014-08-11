from setuptools import setup, find_packages


setup(
    name='nusbot',
    version='0.1.5',
    description='adc bot annoucing changes in filelist of hub\'s users',
    url='https://github.com/kraiz/nusbot',
    license='MIT',
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'nusbot = nusbot.main:main',
        ],
    },
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
