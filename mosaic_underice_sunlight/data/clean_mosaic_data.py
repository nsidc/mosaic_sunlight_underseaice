"""Renames paths files to be consistent, reformats data file

We only use the Level 3 data which combines ice thickness, derived by subtracting 
snow depth from GEM2 total thickness, snow depth and melt pond depth.

During summer the magnaprobe was used to measure melt pond depth and SSL thickness, 
in addition to snow depth.

Only Level 3 files are copied to the processed directory.

Level 3 files have naming convention magna+gem2-transect-YYYYMMDD-ccccc-l_x-z_location.csv

where:

YYYYMMDD is date string
ccccc is campaign id - for MOSAic drift this is PS122
l is leg (1-5)
x is an identifier
z is another identifier
location is a string identifier
"""
import warnings

import re

import numpy as np
import pandas as pd

from mosaic_underice_sunlight.filepath import RAW_DATAPATH, PROCESSED_DATAPATH
from mosaic_underice_sunlight.mosaic_thickness import load_raw_combined_data

RAW_MAGNAPROBE = RAW_DATAPATH / 'MOSAiC_magnaprobe'
PROCESSED_MAGNAPROBE = PROCESSED_DATAPATH / 'MOSAiC_magnaprobe'


# Patterns for activity id and filenames
activity_id_str = r'(\d{8})[-_]*(\w+)[-_]*(\d)[-_]*(\d+)[-_]*(\d+)'
filename_str = r'(magna.gem2)[-_]*(transect)[-_]*'+activity_id_str+r'[-_]*([\w_]*).csv'

# Compile regex for patterns
activity_id_pattern = re.compile(activity_id_str)
filename_pattern = re.compile(filename_str)


def get_raw_magnaprobe_path():
    """Returns only paths to magnaprobe files
    ignores recon
    """
    if not RAW_MAGNAPROBE.exists():
        raise FileNotFoundError(f"Path {RAW_MAGNAPROBE} not found!")
    return [path for path in RAW_MAGNAPROBE.glob('**/magna+gem2-transect*.csv')
            if activity_id_pattern.search(path.name)]


def parse_activity_id(activity_id):
    """Fixes the transect path to ensure consistency"""
    attr_names = ["date", "campaign", "leg",
                  "activity2", "activity3"]
    try:
        attributes = activity_id_pattern.match(activity_id).groups()
    except AttributeError as err:
        print(f"Failed to parse {activity_id}: {err}")
        raise
    return {k: v for k, v in zip(attr_names, attributes)}


def parse_filename(fname):
    """Converts filename to POSIX fully portable format

    allowed char set A-Z a-z 0-9 . _ -
    """
    keys = ["content", "transect", "date", "campaign",
            "leg", "activity2", "activity3", "location"]
    try:
        attributes = filename_pattern.search(fname).groups()
    except AttributeError as err:
        print(f"Failed to parse {fname}: {err}")
        raise
    return {k: v for k, v in zip(keys, attributes)}


def make_activity_dirname(activity_attr):
    """Makes directory path for activity"""
    return "{}-{}-{}_{}-{}".format(activity_attr.values())


def activity_and_file_attrs_match(activity_attr, file_attr):
    """Makes sure date, campaign and activity fields are same"""
    file_activity_attr = {k: file_attr[key] for key in activity_attr.keys()}
    if file_activity_attr != activity_attr:
        False
    return True


def parse_filepath(path):
    """Parses and compares fields in activity directory path and transect filenames

    :path: pathlib.Path object

    :returns: dict containing file attributes
    """
    activity_id, filename = path.parts[-2:]

    try:
        activity_attr = parse_activity_id(activity_id)
    except AttributeError as err:
        raise

    try:
        file_attr = parse_filename(filename)
    except AttributeError as err:
        raise

    if not activity_and_file_attrs_match:
        raise ValueError(f"File and activity attributes do not match for {filename}")
        
    return file_attr


def make_new_filepath(attrs):
    """Returns a new file path"""
    activity_path = (f"{attrs['date']}-{attrs['campaign']}-{attrs['leg']}_"
                     f"{attrs['activity2']}-{attrs['activity3']}")
    filename = (f"{attrs['content'].replace('+','-and-')}_{attrs['transect']}_"
                f"{activity_path}_{attrs['location']}.csv")
    return PROCESSED_MAGNAPROBE / activity_path / filename


def check_data_range(series, min_value, max_value, fix=False, fill_value=np.nan):
    """Checks for out-of-expected range values.  If fix=True, set out of range 
    values to fill_value.

    Args:
        series : (pandas.Series) series of values to check
        min_value : (scalar) minimum acceptable values
        max_value : (scalar) maximum acceptable values
        fix : (bool) if True replace out of range values with fill_value
        fill_value : (scalar) value with which to replace out of range values.
            Default is np.nan.

    Returns: same type as caller.

    Notes: raises UserWarning if out of range values are found
    """
    in_range = series.between(min_value, max_value)

    out_of_range = in_range[series.notna()] == False
    if out_of_range.any():
        warnings.warn(f"Out of range values in {series.name}: {out_of_range.sum()} found",
                     UserWarning)

    if fix:
        return series.where(in_range, other=fill_value)

    return series


def df_minmax(df):
    """Prints min and max of dataFrame for all columns"""
    def count_nan(x):
        return x.isna().sum()
    
    print(df.agg(['min', 'max', 'count', count_nan]).T)


def check_file_structure(path, verbose=False):
    """Checks that file has constent structure and values"""

    if verbose: print(f"Checking {'/'.join(path.parts[-2:])}")

    try:
        df = load_data(path)
    except:
        print(f"Failed to load {path.name}")
        raise

    # Run some checks
    # - within range lat, lon
    # - ice thickness range
    # - ice depth range
    # - melt pond range
    # - consistent surface type
    # - Generate plots

    if not df.index.is_monotonic_increasing:
        warnings.warn(f"Index is not monotonic increasing in {path}", UserWarning)

    # To check within bounds use Series.between(left, right)  Treats NaNs as False
    # Write to path
    df_minmax(df)

    if verbose: print("-------------------------------------------------\n")


def clean_mosaic_data():
    """Renames filepaths and reformats data files"""

    raw_paths = get_raw_magnaprobe_path()

    for path in raw_paths:

        try:
            file_attributes = parse_filepath(path)
        except AttributeError as err:
            print(f"Failed to parse filepath {path}: {err}")
            print("Skipping")
            continue
        except ValueError as err:
            print(f"Failed to parse {path}: {err}")
            print("Skipping")
            continue

        outpath = make_new_filepath(file_attributes)
        print(outpath)

        check_file_structure(path, verbose=True)
        break

    return


if __name__ == "__main__":
    clean_mosaic_data()
