#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Jack McMahon",
    author_email='OCRfixr@mcmahon.work',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Automate the boring work of manually correcting OCR output from Distributed Proofreaders' book digitization projects.",
    entry_points={
        'console_scripts': [
            'ocrfixr=ocrfixr.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords=['ocrfixr','spellcheck', 'OCR', 'contextual', 'BERT'],
    name='ocrfixr',
    packages=find_packages(include=['ocrfixr', 'ocrfixr.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ja-mcm/ocrfixr',
    version='0.1.0',
    zip_safe=False,
)
