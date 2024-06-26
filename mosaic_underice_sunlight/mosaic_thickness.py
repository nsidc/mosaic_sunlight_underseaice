"""Functions for loading and parsing MOSAiC GEM-2 and Magnaprobe datasets"""

from pathlib import Path
import re
import warnings

import pandas as pd
import numpy as np

DATAPATH = Path.home() / 'Data' / 'Sunlight_under_seaice'
GEM2_PATH = DATAPATH / 'MOSAiC_GEM2_icethickness' / '01-ice-thickness'
MAGNAPROBE_PATH = DATAPATH / 'MOSAiC_Observations' / 'raw' / 'MOSAiC_magnaprobe'

KEEP_THESE_COLUMNS = ['lon', 'lat', 'local_x', 'local_y',
                      'ice_thickness_m', 'snow_depth_m',
                      'melt_pond_depth_m', 'surface_type',
                      'transect_distance_m', 'ice_thickness_flag']


def combined_files():
    """Returns a list of combined snow depth and ice thickness files"""
    return [fp for fp in MAGNAPROBE_PATH.glob("*/magna+gem2-transect*.csv") if re.search(r"\d{8}_PS122-\d_\d*-\d*_", fp.name)]


def icethickness_file(dsid):
    """Returns a file from a MOSAiC dataset id"""
    return next(next(GEM2_PATH.glob("*"+dsid.replace('/','-'))).glob('*channel-thickness.csv'))


def snowdepth_file(dsid):
    """Returns a snow depth file from a MOSAiC dataset id"""
    thispath = MAGNAPROBE_PATH.match("*"+dsid.replace("/","-"))
    if thispath:
        filelist = list(thispath.glob("magna+gem2*.csv"))
        if len(filelist) == 0:
            raise FileNotFoundError(f"No magna+gem2*.csv file in {str(thispath)}")
        elif len(filelist) > 1:
            raise RuntimeError(f"Expected unique match for magna+gem2*.csv found {filelist}")
        else:
            return filelist[0]
    else:
        raise NotADirectoryError(f"No directory found for {dsid}")


def transect_distance(x0, y0):
    """Calculates the distance along a transect
    
    :x0: x in local cordinates
    :y0: y in local coordinates
    """
    x0 = np.array(x0)
    y0 = np.array(y0)
    x1, y1 = np.roll(x0, 1), np.roll(y0, 1)
    x1[0], y1[0] = x1[1], y1[1]
    return np.cumsum(np.sqrt((x1 - x0)**2 + (y1 - y0)**2))


def get_filename(fp, type='combined'):
    filelist = list(fp.glob("magna+gem2*.csv"))
    if len(filelist) == 0:
        raise FileNotFoundError(f"No magna+gem2*.csv file in {str(fp)}")
    elif len(filelist) > 1:
        raise RuntimeError(f"Expected unique match for magna+gem2*.csv found {filelist}")
    else:
        return filelist[0]


def infer_surface_type(df):
    """Infers surface type from snow and pond depths.

    Args:
        df : (pandas.DataFrame) containing snow and pond depths

    returns: pandas.Series containing -1, 1 or 2 meaning pond, snow or bare ice surface
    
    Notes: if pond and snow are both > 0, then np.nan is used.
    """
    conditions = [
        (df.snow_depth_m > 0.) & (df.melt_pond_depth_m <= 0.),
        (df.snow_depth_m <= 0.) & (df.melt_pond_depth_m > 0.),
        (df.snow_depth_m <= 0.) & (df.melt_pond_depth_m <= 0.),
        (df.snow_depth_m > 0.) & (df.melt_pond_depth_m > 0.),
        ]
    choices = [1, -1, 2, np.nan]
    surface_type = np.select(conditions, choices)
    return pd.Series(surface_type, index=df.index)


def load_raw_combined_data(fp):
    """Loads raw files containing combined snow depth and ice 
       thickness transect data.

    Args:
        fp : (str or Path object) filepath to combined file

    Returns: pandas.Dataframe

    Notes:
        1. Some files have trailing ',' in first row, which is interpretted 
           by pandas as an extra column and given "Unnamed: column_number".
           This is identified and removed.
        2. Column names have spaces and units in parentheses and are in 
           title case, e.g "Snow Depth (m)".  columns are made lower case, 
           spaces are replaced with "_" and parentheses removed.
    """
    these_columns = lambda x: "Unnamed" not in x

    df = pd.read_csv(fp, parse_dates=True, index_col=0, usecols=these_columns)
    df.columns = ['_'.join(s.strip().lower().replace('(','').replace(')','').split())
                  for s in df.columns]
    return df


def load_reformatted_combined_data(fp):
    """Loads raw files containing combined snow depth and ice 
       thickness transect data.

    Args:
        fp : (str or Path object) filepath to combined file

    Returns: pandas.Dataframe
    """
    df = pd.read_csv(fp, parse_dates=True, index_col=0)
    return df


def assign_ice_thickness(df, quiet=False):
    """Adds ice_thickness_m column following Itkin et al (2023).  A ice_thickness_flag
    column is also added.

    Args:
        df : (pandas.DataFrame) Dataframe containing raw combined data
        quiet : (boolean) silence warnings !!!Not Implemeneted!!!

    if ice_thickness_18khz_ip_m in df:
        ice_thickness_m = df.ice_thickness_18khz_ip_m
        ice_thickness_flag = 1
    elif ice_thickness_f18325hz_hcp_i_m in df:
        ice_thickness_m = df.ice_thickness_f18325hz_hcp_i_m
        ice_thickness_flag = 2
    else:
        ice_thickness_m = np.nan
        ice_thickness_flag = 0

    returns None
    """
    if 'ice_thickness_18khz_ip_m' in df:
        df['ice_thickness_m'] = df['ice_thickness_18khz_ip_m']
        df['ice_thickness_flag'] = 1
    elif 'ice_thickness_f18325hz_hcp_i_m' in df:
        warnings.warn("Using ice_thickness_f18325hz_hcp_i_m for ice thickness",
                     UserWarning)
        df['ice_thickness_m'] = df['ice_thickness_f18325hz_hcp_i_m']
        df['ice_thickness_flag'] = 2
    else:
        warnings.warn("Expected ice_thickness column not found", UserWarning)
        df['ice_thickness_m'] = np.nan
        df['ice_thickness_flag'] = 0
    return None


def assign_melt_pond_depth(df):
    """Sets melt_pond_depth_m to zero if <= 0 or add column if not in raw dataframe

    Args:
        df : (pandas.DataFrame) dataframe containing raw data
    
    Returns: None - assigned inplace
    """
    if 'melt_pond_depth_m' in df:
        df['melt_pond_depth_m'] = df['melt_pond_depth_m'].where(df['melt_pond_depth_m'] > 0., 0.)
    else:
        warnings.warn("melt_pond_depth_m not found in dataFrame; adding column of zeros",
                     UserWarning)
        df['melt_pond_depth_m'] = 0.
    return None


def assign_snow_depth(df):
    """Sets snow depth to 0. if <= 0. or adds column if not in dataframe

    Args:
        df : (pandas.DataFrame) raw combined dataframe

    Returns: None - assigned inplace

    Notes: If snow_depth_m column not present a column is added and assigned np.nan
    """
    if 'snow_depth_m' in df:
        df['snow_depth_m'] = df['snow_depth_m'].where(df['snow_depth_m'] > 0., 0.)
    else:
        warnings.warn("snow_depth_m not found in dataFrame;adding column of NaN",
                     UserWarning)
        df['snow_depth_m'] = np.nan
    return None


def check_columns(df):
    """Returns True if essential columns are in df"""
    THESE_COLUMNS = [
        r'^lon$',
        r'^lat$',
        r'^local_x$',
        r'^local_y$',
        r'^ice_thickness.*$',
        r'^snow_depth_m$',
        r'^melt_pond_depth_m$',
        r'^surface_type$',
        ]
    present = [is_column(target, df) for target in THESE_COLUMNS]
    if not all(present):
        raise KeyError(f"Column names have no match for {[c for c, p in zip(THESE_COLUMNS, present) if not p]}")

    return True


def is_column(target, df):
    """Checks if regex matches dataframe column name"""
    return any([re.search(target, c) for c in df.columns])


def parse_raw_combined_data(fp):
    """Parses raw combined snowdepth and ice thickness transect data files

    Args:
        fp: (str or pathlb.Path object) filepath to combined file
    
    Returns: pandas.DataFrame see Notes for structure

    Notes: 
    Rows are indexed by datetime.

    Columns are: lon, lat, local_x, local_y, ice_thickness_m, ice_thickness_flag,
                 snow_depth_m, melt_pond_depth_m, surface_type, transect_distance_m

    All other columns are dropped.

    Data for ice_thickness_m are selected following Itkin et al (2023).  Data in
    the column ice_thickness_18khz_ip_m if this column exists.  If not, data in
    ice_thickness_f18325hz_hcp_i_m is used.  If neither of these columns is found
    ice_thickness_m is assigned np.nan.

    melt_pond_depth_m is set to zero for pond depths <= 0.


    """

    df = load_reformatted_combined_data(fp)

#    try:
#        check_columns(df)
#    except Exception as err:
#        raise err

    # assign ice_thickness_m
    assign_ice_thickness(df)
    
    # Set pond depth <= 0. to 0.  Add column if it doesn't exists
    assign_melt_pond_depth(df)
    
    # Set snow depth <= 0. to zero.  If no snow depth column raise warning and set to NaN
    assign_snow_depth(df)
    
    if 'surface_type' not in df:
        df['surface_type'] = infer_surface_type(df)
        
    df['transect_distance_m'] = transect_distance(df.local_x.values, df.local_y.values)

    return df[KEEP_THESE_COLUMNS]


def load_cleaned_transect(fp):
    """Loads a single cleaned MOSAiC transect file"""
    return pd.read_csv(fp, index_col=0, parse_dates=True, na_values=[-999.])

def load_transect_metadata(polar_day=True, dropna=True):
    """Loads transect metadata files
    
    Arguments
    ---------
    polar_day : only return transects with incident solar radiation greater than 0.
                (Default: True)
    dropna : if forcing data is not available, drop rows (Default: True)
    
    Returns
    Pandas Dataframe containing transect id and forcing data
    """
    METADATA_FILE = Path("../data/transect_surface_forcing.csv")
    transects = pd.read_csv(METADATA_FILE,
                            index_col=0, parse_dates=True,
                            date_format="%Y-%m-%dT%H:%M:%S")

    if dropna == True:
        transects = transects.dropna(axis=0)
    if polar_day == True:
        transects = transects[transects.rsd > 0.]  # Make sure sun is up

    transects["skin_temp_surface"] = transects["skin_temp_surface"] + 273.15
    transects.set_index("activity", drop=True, inplace=True)
    return transects
