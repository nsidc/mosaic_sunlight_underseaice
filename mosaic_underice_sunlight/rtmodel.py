"""Contains functions to run seaice_rt model"""
import pandas as pd

from seaicert.ccsm3_sir_de import SeaIceRT


def seaicert_mp(df):
    """Runs the SeaIceRT model for multiple points.  Output is returned as a pandas.DataFrame"""
    
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
    surface_albedo = []
    surface_downwelling_radiative_flux = []
    #for idx, vals in df.iterrows():
    for iday_of_year, ilat, isnow_depth_m, imelt_pond_depth_m, iice_thickness_mean_m in thiszip:
        model.day_of_year = iday_of_year + 0.5  # adjust for longitude?
        model.latitude = ilat
        model.snow_depth = isnow_depth_m
        model.pond_depth = imelt_pond_depth_m
        model.sea_ice_thickness = iice_thickness_mean_m
    
        model.run()
        output = model.get_results()
        #distance.append(vals.transect_distance_m)
        sw_absorbed_by_ocean.append(output["downwelling_shortwave_flux_absorbed_by_ocean"])
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
            'surface_albedo': surface_albedo,
            'surface_downwelling_radiative_flux': surface_downwelling_radiative_flux,
            'transect_distance_m': df.transect_distance_m.values,
        },
        index = df.transect_distance_m,
    )
    return result
