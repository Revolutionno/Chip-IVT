"""Package setup for chip-ivt."""

from setuptools import setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="chip-ivt",
    version="0.1.0",
    description="Service tool for IVT heatpump Rego 1000 controller",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chip",
    license="GPL-3.0",
    py_modules=["chip_ivt"],
    python_requires=">=3.8",
    install_requires=[
        "pyserial>=3.5",
    ],
    entry_points={
        "console_scripts": [
            "chip-ivt=chip_ivt:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
    ],
)
