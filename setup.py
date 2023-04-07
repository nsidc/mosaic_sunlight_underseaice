from setuptools import setup

setup(
    name='mosaic_underice_sunlight',
    version='0.1.0',
    author='Andrew P. Barrett',
    author_email='andrew.barrett@colorado.edu',
    packages=['mosaic_underice_sunlight'],
    install_requires=[
        'pytest',
        ],
    license=open('LICENSE_NASA').read(),
    description='A package to calculate underice light for MOSAiC ice thickness and snow depth transects',
    long_description=open('README.md').read(),
)
