"""Calculates mean shortwave flux and air temperature for period of transect
observations
"""

from pathlib import Path
import datetime as dt

import xarray as xr
import pandas as pd

from mosaic_underice_sunlight.filepath import MET_DATAPATHS, FILLED_MET_DATAPATH
from mosaic_underice_sunlight.filepath import VIRTUAL_ZARR_JSONS
from mosaic_underice_sunlight.data.mosaic_met_kerchunker import load_metdata_zarr


def load_transect_summary():
    SUMMARY_PATH = Path("/home/apbarret/src/mosaic_sunlight_underseaice/data/mosaic_transect_summary.csv")
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
    ds = ds.rename_dims({"time01": "time"})
    ds = ds.rename_vars({"time01": "time"})
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

    if not variables:
        variables = ['rsd', 'tas']  # Add skin temperature

    result = metds[variables].sel(time=slice(start_time, end_time)).mean()
    return (index, result.to_pandas().to_dict())


def extract_to_dataframe(ds, transect, variables):
    """Extracts variables for transect date range and 
    return as pandas dataframe.
    """
    zipper = transect[['start_time', 'end_time']].iterrows()
    
    result = [
        get_met_data_for_one_transect(
            ds, 
            idx, 
            *dates.array,
            variables=variables
        ) for (idx, dates) in zipper
    ]
    idx, data = list(zip(*result))
    
    return pd.DataFrame(data, index=idx)


def get_met_data_for_transects():

    metds = load_filled_metdata()
    transect = load_transect_summary()
    tower = load_metdata_zarr(VIRTUAL_ZARR_JSONS['tower'])
    #transect = transect.iloc[:4]
    
    ds1 = extract_to_dataframe(metds, transect, variables=["rsd", "tas"])
    ds2 = extract_to_dataframe(tower, transect, variables=["skin_temp_surface"])
    
    df = transect[["activity","start_time","end_time"]].join(ds1.join(ds2))
    df.to_csv("data/transect_surface_forcing.csv", 
              na_rep="NaN",
              date_format="%Y-%m-%dT%H:%M:%S")
    

if __name__ == "__main__":
    get_met_data_for_transects()
