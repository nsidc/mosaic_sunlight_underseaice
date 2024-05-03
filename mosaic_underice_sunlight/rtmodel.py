"""Contains functions to run seaice_rt model"""
from typing import Union
import datetime as dt

import pandas as pd
import numpy as np

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
        
    return (
        timestamp,
        output["downwelling_shortwave_flux_absorbed_by_ocean"],
        output["downwelling_longwave_flux_absorbed_by_ocean"],
        total_flux_absorbed_by_ocean,
        qpar_absorbed_by_ocean,
        output["surface_albedo"],
        output["surface_downwelling_radiative_flux"],
        )


def seaicert_mp(df: pd.DataFrame) -> pd.DataFrame:
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
    
    model = SeaIceRT()

    model.snow_grain_radius = 180.

    day_of_year = df.index.day_of_year
    lat = df.lat.values
    snow_depth_m = df.snow_depth_m.values
    melt_pond_depth_m = df.melt_pond_depth_m.values
    ice_thickness_mean_m = df.ice_thickness_mean_m.values
    
    thiszip = zip(
        day_of_year,
        lat,
        snow_depth_m,
        melt_pond_depth_m,
        ice_thickness_mean_m,
    )
    
    distance = []
    sw_absorbed_by_ocean = []
    lw_absorbed_by_ocean = []
    surface_albedo = []
    surface_downwelling_radiative_flux = []
    #for idx, vals in df.iterrows():
    for iday_of_year, ilat, isnow_depth_m, imelt_pond_depth_m, iice_thickness_mean_m in thiszip:
        if (isnow_depth_m > 0.) & (imelt_pond_depth_m > 0.):
            raise ValueError(f"Snow depth and pond depth cannot both be greater than zero: {iday_of_year}")
        if (isnow_depth_m < 0.):
            raise ValueError(f"Snow depth must be positive")
        if (imelt_pond_depth_m < 0.):
            raise ValueError(f"Melt pond depth must be positive")
        if (iice_thickness_mean_m < 0.):
            raise ValueError(f"Ice thickness must be positive")
        model.day_of_year = iday_of_year + 0.5  # adjust for longitude?
        model.latitude = ilat
        model.snow_depth = isnow_depth_m
        model.pond_depth = imelt_pond_depth_m
        model.sea_ice_thickness = iice_thickness_mean_m
    
        model.run()
        output = model.get_results()
        #distance.append(vals.transect_distance_m)
        sw_absorbed_by_ocean.append(output["downwelling_shortwave_flux_absorbed_by_ocean"])
        lw_absorbed_by_ocean.append(output["downwelling_longwave_flux_absorbed_by_ocean"])
        surface_albedo.append(output["surface_albedo"])
        surface_downwelling_radiative_flux.append(output["surface_downwelling_radiative_flux"])
        
    result = pd.DataFrame(
        {
            'datetime': df.index.values,
            'latitude': df.lat.values,
            'snow_depth_m': df.snow_depth_m.values,
            'melt_pond_depth_m': df.melt_pond_depth_m.values,
            'ice_thickness_mean_m': df.ice_thickness_mean_m.values,
            'sw_absorbed_by_ocean': sw_absorbed_by_ocean,
            'downwelling_radiative_flux_absorbed_by_ocean': np.array(sw_absorbed_by_ocean) + np.array(lw_absorbed_by_ocean),
            'surface_albedo': surface_albedo,
            'surface_downwelling_radiative_flux': surface_downwelling_radiative_flux,
            'transect_distance_m': df.transect_distance_m.values,
        },
        index = df.transect_distance_m,
    )

    # Convert radiative flux to ocean to PAR
    flux_to_par(result)
    
    return result
