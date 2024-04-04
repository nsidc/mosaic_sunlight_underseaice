"""Calculates mean shortwave flux and air temperature for period of transect
observations
"""

from pathlib import Path
import datetime as dt

import xarray as xr
import pandas as pd

from mosaic_underice_sunlight.filepath import MET_DATAPATHS, FILLED_MET_DATAPATH


def load_transect_summary():
    SUMMARY_PATH = Path("mosaic_transect_summary.csv")
    df = pd.read_csv(SUMMARY_PATH, parse_dates=True,
                     date_format="%Y-%m-%d %H:%M:%S",
                     index_col=0)
    return df.dropna(axis=0)


def load_mosaic_metdata(site: str) -> xr.Dataset:
    """Load data for a given MOSAiC met site

    Parameters
    ----------
    site : name of site.  One of tower, asfs30, asfs40, asfs50

    Returns
    -------
    xarray.Dataset containing metdata
    """
    if site not in MET_DATAPATHS:
        raise KeyError(f"site must be one of {', '.join(MET_DATAPATHS.keys())}")
    met_filepaths = MET_DATAPATHS[site].glob("mosmet*.nc")
    ds = xr.open_mfdataset(met_filepaths)
    return ds


def load_filled_metdata():
    met_filepaths = FILLED_MET_DATAPATH / "MOSAiC_MDF_20191011-20201001.nc"
    ds = xr.open_dataset(met_filepaths)
    return ds


def get_met_data_for_one_transect(metds: xr.Dataset,
                                  index: int,
                                  start_time: dt.datetime,
                                  end_time: dt.datetime,
                                  variables=None) -> tuple:
    """Returns metdata for time period as average

    metds : met dataset
    start_time : start time for transect
    end_time : end time for transect

    Returns
    -------
    list-like containing variables of interest
    """

    variables = ['rsd', 'tas']  # Add skin temperature

    result = metds[variables].sel(time01=slice(start_time, end_time)).mean()
    return (index, result)


def get_met_data_for_transects():

    metds = load_filled_metdata()
    transect = load_transect_summary()

    zipper = zip(transect.index, transect['start_time'], transect['end_time'])
    
    result = [get_met_data_for_one_transect(metds, *row) for row in zipper]

    print(result)


if __name__ == "__main__":
    get_met_data_for_transects()
