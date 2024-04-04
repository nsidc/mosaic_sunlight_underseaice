"""Generates a transect summary table from cleaned transect files"""

from pathlib import Path
import re

import pandas as pd

from mosaic_underice_sunlight.filepath import CLEAN_DATAPATH
from mosaic_underice_sunlight.mosaic_thickness import load_cleaned_transect


def cleaned_transects():
    """Returns a list of paths to cleaned transect files"""
    return list((CLEAN_DATAPATH / "MOSAiC_magnaprobe").glob('*/*.csv'))


def activity_id_from_filename(fp):
    """Returns activity ID and location"""
    p = re.compile(r"(\d{8}_PS122-\d+_\d+-\d+)_(.*)\.csv")
    m = p.search(fp.name)
    if m:
        activity, location = m.groups()
    else:
        raise ValueError("No matching pattern found")
    return activity, location

    
def parse_one_file(fp):
    """Returns metadata for one file"""
    activity, location = activity_id_from_filename(fp)
    
    df = load_cleaned_transect(fp)

    result = {
        "activity": activity,
        "location": location,
        "npoints": len(df),
        "start_time": df.index[0],
        "end_time": df.index[-1],
        "start_lat": df.lat.iloc[0],
        "start_lon": df.lon.iloc[0],
        "length": df.transect_distance_m.max(),
        "mean_snow_depth_m": df.snow_depth_m.mean(),
        "mean_ice_thickness_m": df.ice_thickness_m.mean(),
        "mean_pond_depth_m": df.melt_pond_depth_m.mean(),
        }
    
    return result


def make_summary_table():
    """Creates summary table of transects"""

    summary = pd.DataFrame([parse_one_file(fp) for fp in cleaned_transects()])
    summary.to_csv("mosaic_transect_summary.csv")
    

if __name__ == "__main__":
    make_summary_table()
