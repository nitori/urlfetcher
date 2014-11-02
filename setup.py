#!/usr/bin/env python3

from distutils.core import setup

setup(
    name='urlfetcher',
    version='1.1.',
    description='Fetches Information of a URL and assembles it in one short line',
    author='Nitori Kawashiro',
    author_email='nitori@chireiden.net',
    packages=['urlfetcher', 'urlfetcher.fetchers'],
    scripts=['fetch-url-title'],
    requires=['requests', 'enzyme', 'Pillow', 'beautifulsoup4'],
)
