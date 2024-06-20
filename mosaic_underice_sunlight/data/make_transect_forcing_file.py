"""Calculates mean shortwave flux and air temperature for period of transect
observations
"""

from pathlib import Path
import datetime as dt

import numpy as np

import xarray as xr
import pandas as pd

from mosaic_underice_sunlight.filepath import (MET_DATAPATHS,
                                               FILLED_MET_DATAPATH,
                                               FILLED_TSKIN_DATAPATH,
                                               cleaned_transects)
from mosaic_underice_sunlight.filepath import VIRTUAL_ZARR_JSONS
from mosaic_underice_sunlight.data.mosaic_met_kerchunker import load_metdata_zarr
from mosaic_underice_sunlight.mosaic_thickness import load_cleaned_transect


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


def load_filled_tskin():
    """Loads filled skin temperature"""
    df = pd.read_csv(FILLED_TSKIN_DATAPATH, parse_dates=True, index_col=0,
                     header=0, names=["time", "tskin"])
    df = df + 273.15
    return df.to_xarray()


def load_filled_metdata():
    met_filepaths = FILLED_MET_DATAPATH / "MOSAiC_MDF_20191011-20201001.nc"
    ds = xr.open_dataset(met_filepaths)
    ds = ds.rename_dims({"time01": "time"})
    ds = ds.rename_vars({"time01": "time"})
    return ds


def load_combined_metdata():
    """Returns a single dataframe of met data"""
    # load metdata
    metds = load_filled_metdata()
    tskin = load_filled_tskin()
    return xr.merge([metds, tskin])


def load_transect_summary():
    """Loads the transect summary file"""
    return pd.read_csv("data/mosaic_transect_summary.csv", index_col=0, parse_dates=True)


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

    if not variables:
        variables = ['rsd', 'tas', 'tskin']

    result = metds[variables].sel(time=slice(start_time, end_time)).mean()
    return result.to_pandas().to_dict()


def make_forcing_filepath(transect_file):
    """Returns path for new forcing file"""
    print(transect_file)


def make_one_forcing_file(transect_file, met_dataset):
    """Extracts variables for transect date range and 
    return as pandas dataframe.
    """
    
    transect_df = load_cleaned_transect(transect_file)
    
    met_data = get_met_data_for_one_transect(
        met_dataset, 
        0, 
        transect_df.index[0],
        transect_df.index[-1],
    )

    if np.isnan([x for x in met_data.values()]).any():
        print(f"NaN found in period for {transect_file.name}")
        return
    
    for variable, value in met_data.items():
        transect_df[variable] = value

    fp_out = make_forcing_filepath(transect_file)
    
    return 


def make_transect_forcing_files():

    transect_files = cleaned_transects()
    print(transect_files)
    
    # load metdata
#    metds = load_combined_metdata()

#    for fp in transect_files[:5]:
#        make_one_forcing_file(fp, metds)
    
    # Write forcing file
    

if __name__ == "__main__":
    make_transect_forcing_files()
