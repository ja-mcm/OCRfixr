#!/usr/bin/env python

from distutils.core import setup

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
    install_requires=['nltk','pandas', 'transformers', 'spellchecker'],
    license="GNU General Public License v3",
    include_package_data=True,
    keywords=['ocrfixr','spellcheck', 'OCR', 'contextual', 'BERT'],
    name='ocrfixr',
    test_suite='tests',
    url='https://github.com/ja-mcm/ocrfixr',
    version='0.1.0',
    zip_safe=False,
)
