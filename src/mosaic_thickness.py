"""Functions for loading and parsing MOSAiC GEM-2 and Magnaprobe datasets"""

from pathlib import Path

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
    
    
def load_data(fp):
    """Loads a combined snowdepth and ice thickness transect"""
    usecols = ['Date/Time', ' Lon', ' Lat', ' Local X', ' Local Y', ' Snow Depth (m)',
       ' Melt Pond Depth (m)', ' Surface Type', ' Ice Thickness 18kHz ip (m)',
       ' Ice Thickness 5kHz ip (m)', ' Ice Thickness 93kHz ip (m)']
    df = pd.read_csv(fp, usecols=usecols, parse_dates=True, index_col=0)
    df.columns = ['_'.join(s.strip().lower().replace('(','').replace(')','').split()) for s in df.columns]
    df['ice_thickness_mean_m'] = df[['ice_thickness_18khz_ip_m', 'ice_thickness_5khz_ip_m', 'ice_thickness_93khz_ip_m']].mean(axis=1)
    df['melt_pond_depth_m'] = df['melt_pond_depth_m'].where(df['melt_pond_depth_m'] > 0., 0.)
    df['snow_depth_m'] = df['snow_depth_m'].where(df['snow_depth_m'] > 0., 0.)
    df['transect_distance_m'] = transect_distance(df.local_x.values, df.local_y.values)
    return df


def plot_thickness_profile(df, ax=None, snow_depth_exaggeration=2):
    """Plots a thickness profile from GEM-2 and Magnaprobe data"""
    snow_ice_interface = np.zeros(len(df.snow_depth_m))
    snow_surface = snow_ice_interface + (df.snow_depth_m.where(df.snow_depth_m > 0.) * snow_depth_exaggeration)
    ice_ocean_interface = snow_ice_interface - df.ice_thickness_mean_m
    pond_depth = snow_ice_interface - df.melt_pond_depth_m.where(df.melt_pond_depth_m > 0.)
    distance = df.transect_distance_m.values
    ax.set_xlim(distance[0], distance[-1])
    ax.fill_between(distance, snow_surface, snow_ice_interface, color='0.7')
    ax.fill_between(distance, snow_ice_interface, ice_ocean_interface, color='lightblue')
    ax.fill_between(distance, snow_ice_interface, pond_depth, color='blue')
    
    # Kluge fix for labels
    ymin = np.floor(ice_ocean_interface.min() / 0.5) * 0.5
    ymax = np.ceil(snow_surface.max() / 0.5) * 0.5
    ax.set_ylim(ymin, ymax)
    #labels = ax.get_yticklabels()