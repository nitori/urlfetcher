#!/usr/bin/env python3

from setuptools import setup

lic = 'GNU General Public License v3 (GPLv3)'
classifiers = [
    'Programming Language :: Python',
    'Natural Language :: English',
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: ' + lic,
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
]

with open("requirements.in") as f:
    requirements = f.read().split()

setup(
    # Package information
    name='UrlFetcher',
    version='1.2',
    description='Fetches Information of a URL and assembles it in one short line',
    url='',
    license=lic,
    author='Lars Peter Søndergaard',
    author_email='lps@chireiden.net',

    classifiers=classifiers,
    zip_safe=True,

    # Requirements
    setup_requires=['pip'],
    install_requires=requirements,

    # Scripts and execution
    packages=['urlfetcher'],
    entry_points={
        'console_scripts': [
            'fetch-url-title=urlfetcher.main:main'
        ],
    },
)
