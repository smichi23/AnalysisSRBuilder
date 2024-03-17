from setuptools import setup, find_packages

setup(
    name="analysis_sr_builder",
    version="0.0.1",
    author="Samuel Ouellet",
    author_email="samuel.ouellet.10@ulaval.ca",
    description="Tool to easily store various analysis quantities into a dicom SR",
    url="https://gitlab.chudequebec.ca/sam23/dicom-sr-builder.git",
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU Affero General Public License v3.0",
        "Operating System :: OS Independent",
    ],
    license_files = ('LICENSE.txt',),
    install_requires=['setuptools',
                      'pydicom',
                      'dicom-sr-builder@git+https://gitlab.chudequebec.ca/sam23/dicom-sr-builder.git@python_3_12_support'],
    packages=find_packages(),
    python_requires=">=3.12",
)
