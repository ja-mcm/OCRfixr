#!/usr/bin/env python

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="OCRfixr",
    version="1.4.1",
    author="Jack McMahon",
    author_email="OCRfixr@mcmahon.work",
    description="A contextual spellchecker for OCR output",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    package_dir={'OCRfixr': 'ocrfixr'},
    package_data={'OCRfixr': ['data/*.txt']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6, <3.9',
    install_requires=['transformers', 'symspellpy', 'tensorflow>=2.0', 'importlib_resources', 'metaphone', 'tqdm'],
    license="GNU General Public License v3",
    keywords=['ocrfixr','spellcheck', 'OCR', 'contextual', 'BERT'],
    url='https://github.com/ja-mcm/ocrfixr',
)