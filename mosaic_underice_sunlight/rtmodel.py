"""Contains functions to run seaice_rt model"""
from typing import Union, Tuple, List
import datetime as dt

import pandas as pd
import xarray as xr
import numpy as np

from pqdm.processes import pqdm

from seaicert.ccsm3_sir_de import SeaIceRT

# Conversion factors for SW flux to PAR
underice_flux2par = 3.5   # from Eq 10
openwater_flux2par = 2.3  # from Eq 9 Stroeve et al


def sw2par_underice(irradiance: float) -> float:
    """Returns estimated photosynthetic active 
    radiation portion of SW flux density beneath a sea 
    ice column in W/m^2

    Parameters
    ----------
    irradiance : broadband SW flux density in W/m2

    Returns
    -------
    par in W/m2

    Broadband SW flux density is integral of spectral irradiance
    between 200 nm and 4000 nm.  PAR radiative flux density is
    the integral of spectral irradiance over 400 nm to 700 nm.  
    The bulk conversion factor for underice light is estimated
    from measurements made during the Greenedge campaign.

    F_PAR / F_SW = 0.79 +/- 0.003

    E.g. F_PAR is 79% of broadband SW radiative flux density
    
    See Stroeve, Julienne, Martin Vancoppenolle, Gaelle Veyssiere, 
    Marion Lebrun, Giulia Castellani, Marcel Babin, Michael Karcher, 
    Jack Landy, Glen E. Liston, and Jeremy Wilkinson. 
    “A Multi-Sensor and Modeling Approach for Mapping Light Under 
    Sea Ice During the Ice-Growth Season.” 
    Frontiers in Marine Science 7 (2021). 
    https://doi.org/10.3389/fmars.2020.592337.
    """
    SW2PAR = 0.79
    return irradiance * SW2PAR


def sw2par_openwater(irradiance: float) -> float:
    """Returns the estimated phtosynthetically active portion
    of broadband SW irradiance for open sea water in W/m2

    Parameters
    ----------
    irradiance : broadband SW flux density in W/m2

    Returns
    -------
    par in W/m2

    Broadband SW flux density is integral of spectral irradiance
    between 200 nm and 4000 nm.  PAR radiative flux density is
    the integral of spectral irradiance over 400 nm to 700 nm.  
    The conversion factor is taken from Frouin and Pinker (1995).  
    They give the range of conversion factors as 0.45 to 0.5.

    F_PAR / F_SW = 0.5

    E.g. PAR is 50 % of SW flux.

    Frouin, Robert, and Rachel T. Pinker. “Estimating Photosynthetically 
    Active Radiation (PAR) at the Earth’s Surface from Satellite 
    Observations.” Remote Sensing of Environment, Remote Sensing of 
    Land Surface for Studies of Global Chage, 51, no. 1 
    (January 1, 1995): 98–107. https://doi.org/10.1016/0034-4257(94)00068-X.
    """
    SW2PAR = 0.5
    return irradiance * SW2PAR


def rad2quanta_underice(irradiance: float) -> float:
    """Returns an irradiance in W per m2 as quanta per m2 per s for underice light

    Parameter
    ---------
    irradiance : irradiance in W/m2

    Returns
    -------
    quantum measure of irrandiance as micromoles photons/m2/s

    The quantum measure of radiative flux density for PAR is
    given as:
    
    $$
    Q = \frac{1}{hc}\int_{400 nm}^{700 nm} I(\lambda) \lambda d\lambda
    $$

    where $h$ is the Planck constant and $c$ is the speed of light.

    The conversion factor for broadband SW used here is from the Greenedge campaign

    Q_PAR / F_PAR = 4.44 +/- 0.005 micromoles photons per J
    """
    RAD2QUANTA = 4.44
    return irradiance * RAD2QUANTA


def rad2quanta_openwater(irradiance: float) -> float:
    """Returns an irradiance in W per m2 as quanta per m2 per s for underice light

    Parameter
    ---------
    irradiance : irradiance in W/m2

    Returns
    -------
    quantum measure of irrandiance as micromoles photons/m2/s

    The quantum measure of radiative flux density for PAR is
    given as:
    
    $$
    Q = \frac{1}{N_A hc}\int_{400 nm}^{700 nm} I(\lambda) \lambda d\lambda
    $$

    where $h$ is the Planck constant and $c$ is the speed of light.

    The conversion factor for broadband SW used here is from Morel and Smith

    Q_PAR / F_PAR = 4.44 +/- 0.005 micromoles photons per J

    This comes from the Green water estimate in Table 2 of Morel and Smith (1974),
    which gives the conversion factor in units quanta / J.  Dividing by the 
    Avogadro constant (6.022e23) gives the CF in micromoles per J
    """
    RAD2QUANTA = 4.44
    return irradiance * RAD2QUANTA


def get_qpar_openwater(irradiance: float) -> float:
    """Returns PAR in micromoles per meter squared per second"""
    return rad2quanta_openwater( sw2par_openwater( irradiance) )


def get_qpar_underice(irradiance: float) -> float:
    """Returns PAR in micromoles per meter squared per second"""
    return rad2quanta_underice( sw2par_underice( irradiance) )


def flux_to_par(df):
    """Converts radiative flux to PAR based on whether ice is present or not

    :df: pandas.DataFrame created in seaicert_mp

    :returns: modified dataframe
    """
    # Convert radiative flux to par
    underice_par = get_qpar_underice(df["downwelling_radiative_flux_absorbed_by_ocean"])
    ocean_par = get_qpar_openwater(df["downwelling_radiative_flux_absorbed_by_ocean"])
    df["par_absorbed_by_ocean"] = np.where(
        df["ice_thickness_m"] > 0.,
        underice_par,
        ocean_par
    )
    return


def get_deci_day_of_year(timestamp: dt.datetime) -> float:
    """Returns decimal day of year"""
    return timestamp.day_of_year + (timestamp.hour + (timestamp.minute + timestamp.second/60.)/60.)/24.


def seaicert_point(
        index: int, 
        timestamp: dt.datetime,
        latitude: float,
        snow_depth: float,
        pond_depth: float,
        ice_thickness: float,
        surface_temperature: float,
        air_temperature: float,
        snow_grain_radius: float=180,
    ):
    """Runs SeaIceRT for a single instance

    Parameters
    ----------
    timestamp : datetime
    latitude : latitude (-90.,90.)
    snow_depth : snow depth in meters 
    pond_depth : pond depth in meters
    ice_thickness : ice thickness in meters
    surface_temperature : surface (skin) temperature in Kelvin
    air_temperature: float : 2m air temperature in Kelvin
    snow_grain_radius : effective snow grain radius in um (default = 180 um)

    Returns
    -------
    TBD
    """

    # For debugging
#    print(f"timestamp: {timestamp}\n"
#          f"latitude: {latitude}\n"
#          f"snow_depth: {snow_depth}\n"
#          f"pond_depth: {pond_depth}\n"
#          f"ice_thickness: {ice_thickness}\n"
#          f"surface_temperature: {surface_temperature}\n"
#          f"air_temperature: {air_temperature}\n"
#          f"snow_grain_radius: {snow_grain_radius}")

    if (snow_depth > 0.) & (pond_depth > 0.):
        raise ValueError(f"Snow depth and pond depth cannot both be "
                         f"greater than zero: {iday_of_year}")
    if (snow_depth < 0.):
        raise ValueError(f"Snow depth must be positive")
    if (pond_depth < 0.):
        raise ValueError(f"Melt pond depth must be positive")
    if (ice_thickness < 0.):
        raise ValueError(f"Ice thickness must be positive")
    
    model = SeaIceRT()

    model.snow_grain_radius = 180.

    model.day_of_year = get_deci_day_of_year(timestamp)
    model.latitude = latitude
    model.snow_depth = snow_depth
    model.pond_depth = pond_depth
    model.sea_ice_thickness = ice_thickness
    
    model.surface_air_temperature = air_temperature
    model.ground_temperature = surface_temperature
        
    model.run()
    output = model.get_results()

    total_flux_absorbed_by_ocean = output["downwelling_shortwave_flux_absorbed_by_ocean"] + \
                                   output["downwelling_longwave_flux_absorbed_by_ocean"]
    
    if ice_thickness > 0.:
        qpar_absorbed_by_ocean = get_qpar_underice(total_flux_absorbed_by_ocean)
    else:
        qpar_absorbed_by_ocean = get_qpar_openwater(total_flux_absorbed_by_ocean)

#    print(f"surface_downwelling_radiative_flux: {output["surface_downwelling_radiative_flux"]}\n")
    
    return (
        index,
        (
            output["downwelling_shortwave_flux_absorbed_by_ocean"],
            output["downwelling_longwave_flux_absorbed_by_ocean"],
            total_flux_absorbed_by_ocean,
            qpar_absorbed_by_ocean,
            output["surface_albedo"],
            output["surface_downwelling_radiative_flux"],
        )
    )


def results_to_dataframe(result):
    """Puts results into pandas dataframe"""
    columns=[
        "sw_absorbed_by_ocean",
        "lw_absorbed_by_ocean",
        "downwelling_radiative_flux_absorbed_by_ocean",
        "qpar_absorbed_by_ocean",
        "surface_albedo",
        "surface_downwelling_radiative_flux"
    ]
    
    index, data = list(zip(*result))
    return pd.DataFrame(data, index=index, columns=columns)


def preprocess(obj: Union[pd.DataFrame, xr.Dataset]) -> List[List]:
    """Returns object as a list of tuples"""

    if isinstance(obj, pd.DataFrame):
        return from_dataframe(obj)
    elif isinstance(obj, xr.Dataset):
        return from_dataset(obj)
    else:
        raise TypeError(f"Unknown object {type(obj)}")


def from_dataframe(obj):
    """Returns list of lists or tuples containing forcing"""
    # Fields in dataframe to use as forcing for seaicert
    fields = [
        "time",
        "lat",
        "snow_depth_m",
        "melt_pond_depth_m",
        "ice_thickness_m",
        "surface_temperature_K",
        "air_temperature_K"
    ]
    for field in fields:
        if field not in obj:
            raise KeyError(f"{field} not found in obj")

    return [[idx, *values] for idx, values in obj[fields].iterrows()]    


def from_dataset(obj):
    """Returns list of lists or tuples"""
    raise NotImplementedError()


def seaicert_mp(df: pd.DataFrame,
                parallel: bool=True) -> pd.DataFrame:
    """Runs the SeaIceRT model for multiple points on a transect.  

    Parameters
    ----------
    df : Dataframe containing day of year, latitude, snow depth in m, pond
               depth in m, ice_thickness in meters.  Optionally skin temperature 
               and 2 m air temperature may be in the DataFrame.  If these are not 
               present, the default values are used (effectively 273.15).

    Returns
    -------
    pandas.DataFrame containing shortwave absorbed flux absorbed by ocean, 
    total radiation absorbed by ocean, albedo and surface shortwave flux
    """

    if parallel:
        result = pqdm(preprocess(df), seaicert_point, n_jobs=5, argument_type="args")
    else:
        result = [seaicert_point(*args) for args in preprocess(df)]

    print(results_to_dataframe(result))
    
    # Parse results into pandas.DataFrame
    rt_df = df.join(results_to_dataframe(result))

    return rt_df
