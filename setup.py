#!/usr/bin/env python3
"""Setup script for Chip's Rego 1000 IVT Heatpump Service Tool."""

from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='chip-ivt',
    version='1.0.0',
    description='Chip\'s Rego 1000 IVT heatpump service tool for monitoring and testing your heatpump',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Chip',
    license='GPL-3.0',
    py_modules=['chip_ivt'],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'chip-ivt=chip_ivt:main',
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: System :: Hardware',
        'Topic :: System :: Monitoring',
    ],
)
