"""Functions for loading and parsing MOSAiC GEM-2 and Magnaprobe datasets"""

from pathlib import Path
import warnings

import pandas as pd
import numpy as np

DATAPATH = Path.home() / 'Data' / 'Sunlight_under_seaice'
GEM2_PATH = DATAPATH / 'MOSAiC_GEM2_icethickness' / '01-ice-thickness'
MAGNAPROBE_PATH = DATAPATH / 'MOSAiC_magnaprobe'


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


def load_data(fp):
    """Loads a combined snowdepth and ice thickness transect"""
    df = pd.read_csv(fp, parse_dates=True, index_col=0)
    df.columns = ['_'.join(s.strip().lower().replace('(','').replace(')','').split()) for s in df.columns]

    return df

    if 'ice_thickness_18khz_ip_m' in df:
        df['ice_thickness_m'] = df['ice_thickness_18khz_ip_m']
    elif 'ice_thickness_f18325hz_hcp_i_m' in df:
        warnings.warn("Using ice_thickness_f18325hz_hcp_i_m for ice thickness",
                     UserWarning)
        df['ice_thickness_m'] = df['ice_thickness_f18325hz_hcp_i_m']
    else:
        warnings.warn("Expected ice_thickness column not found", UserWarning)
        df['ice_thickness_m'] = np.nan

    # Set pond depth <= 0. to 0.  Add column if it doesn't exists
    if 'melt_pond_depth_m' in df:
        df['melt_pond_depth_m'] = df['melt_pond_depth_m'].where(df['melt_pond_depth_m'] > 0., 0.)
    else:
        warnings.warn("melt_pond_depth_m not found in dataFrame; adding column of zeros",
                     UserWarning)
        df['melt_pond_depth_m'] = 0.

    # Set snow depth <= 0. to zero.  If no snow depth column raise warning and set to NaN
    if 'snow_depth_m' in df:
        df['snow_depth_m'] = df['snow_depth_m'].where(df['snow_depth_m'] > 0., 0.)
    else:
        warnings.warn("snow_depth_m not found in dataFrame;adding column of NaN",
                     UserWarning)
        df['snow_depth_m'] = np.nan

    if 'surface_type' not in df:
        df['surface_type'] = infer_surface_type(df)
        
    df['transect_distance_m'] = transect_distance(df.local_x.values, df.local_y.values)
    
    return df


