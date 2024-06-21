"""Calculates mean shortwave flux and air temperature for period of transect
observations
"""
from typing import Union

from pathlib import Path
import datetime as dt

import numpy as np

import xarray as xr
import pandas as pd

from mosaic_underice_sunlight.filepath import (MET_DATAPATHS,
                                               FILLED_MET_DATAPATH,
                                               FILLED_TSKIN_DATAPATH,
                                               FORCING_DATAPATH,
                                               cleaned_transects)
from mosaic_underice_sunlight.filepath import VIRTUAL_ZARR_JSONS
from mosaic_underice_sunlight.data.mosaic_met_kerchunker import load_metdata_zarr
from mosaic_underice_sunlight.mosaic_thickness import load_cleaned_transect


new_column_name = {
    "rsd": "measured_irradiance_wm2",
    "tas": "air_temperature_K",
    "tskin": "surface_temperature_K",
    }


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
    return FORCING_DATAPATH / transect_file.relative_to(transect_file.parents[2])


def make_one_forcing_file(transect_file: Union[Path, str],
                          met_dataset: xr.Dataset,
                          verbose: bool=True) -> None:
    """Extracts variables for transect date range and 
    writes forcing file to csv

    Arguments
    ---------
    transect_file : Cleaned MOSAiC transect file
    met_dataset : filled me data
    verbose : print verbose output

    Returns
    -------
    None
    """
    if verbose: print(f"Loading {transect_file.name}")
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

    # If irradiance is zero, skip producing forcing file
    if (met_data['rsd'] <= 0):
        print(f"Measured irradiance is zero for {transect_file.name}; skipping")
        return

    if transect_df.ice_thickness_m.isnull().any():
        print(f"Ice thickness is missing for {transect_file.name}; skipping!")
        return
        
    for variable, value in met_data.items():
        transect_df[new_column_name[variable]] = value

    fp_out = make_forcing_filepath(transect_file)
    fp_out.parent.mkdir(parents=True, exist_ok=True)

    if verbose: print(f"Writing forcing data to {fp_out}")
    transect_df.to_csv(fp_out)
    
    return


def make_transect_forcing_files(verbose=False):

    transect_files = cleaned_transects()
    
    # load metdata
    metds = load_combined_metdata()
    
    for fp in transect_files:
        make_one_forcing_file(fp, metds, verbose=verbose)


if __name__ == "__main__":
    verbose=True
    make_transect_forcing_files(verbose=verbose)
