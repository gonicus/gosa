#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

long_desc = '''
This package contains the cindex Sphinx extension.

Allows declaring cindex specs wherever in the documentation (for instance,
in docstrings of UnitTest.test_* methods) and displaying them as a single
list.
'''

requires = ['Sphinx>=0.6']

setup(
    name='sphinxcontrib-cindex',
    version='0.1',
    license='GPL',
    author='Fabian Hickert',
    author_email='hickert@gonicus.de',
    description='Sphinx "cindex" extension',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['sphinxcontrib'],
    package_data={'sphinxcontrib': ['cindex.css']},
)
