# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


version = "0.1"

install_requires = [
    'setuptools',
    'webob',
    'zope.interface',
    'zope.schema',
    ]

test_requires = [
    'WebTest',
    ]


setup(
    name='dolmen.api_engine',
    version=version,
    author='Souheil CHELFOUH',
    author_email='trollfot@gmail.com',
    url='http://gitweb.dolmen-project.org',
    download_url='http://pypi.python.org/pypi/dolmen.api_engine',
    description='API building utilities for Cromlech',
    long_description=(open("README.txt").read() + "\n" +
                      open(os.path.join("docs", "HISTORY.txt")).read()),
    license='ZPL',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['dolmen'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'test': test_requires,
        },
    )
