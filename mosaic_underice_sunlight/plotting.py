"""Functions for plotting"""
import re

import numpy as np

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import pandas as pd

from mosaic_underice_sunlight.mosaic_thickness import transect_distance


def plot_results(df, title=None):

    distance = df.index.values
    flux_absorbed_by_ocean = df.downwelling_radiative_flux_absorbed_by_ocean
    par = df.par_absorbed_by_ocean
    surface_downwelling_radiative_flux = df.surface_downwelling_radiative_flux
    surface_albedo = df.surface_albedo

    t0 = distance[0]
    t1 = distance[-1]

    fig, ax = plt.subplots(5, 1, figsize=(10,7))
    ax[0].set_xlim(t0, t1)
    ax[0].plot(distance, flux_absorbed_by_ocean)
    ax[0].set_ylim(np.array(ax[0].get_ylim()) * np.array([0., 1.1]))
    ax[0].set_ylabel(r"$\mathrm{W\ m^{-2}}$")
    ax[0].text(0.01, 0.89, "Radiative flux absorbed by Ocean", transform=ax[0].transAxes)
    ax[0].set_xticklabels([])

    ax[1].set_xlim(t0, t1)
    ax[1].plot(distance, par)
    ax[1].set_ylabel(r"$\mathrm{\mu E\ m^{-2}}\ s^{-1}$")
    ax[1].text(0.01, 0.89, "PAR absorbed by Ocean", transform=ax[1].transAxes)
    ax[1].set_xticklabels([])
    
    ax[2].set_xlim(t0, t1)
    ax[2].plot(distance, surface_downwelling_radiative_flux)
    ax[2].set_ylim(np.array(ax[2].get_ylim()) * np.array([0., 1.2]))
    ax[2].set_ylabel(r"$\mathrm{W\ m^{-2}}$")
    ax[2].text(0.01, 0.89, "Surface downwelling flux", transform=ax[2].transAxes)
    ax[2].set_xticklabels([])

    ax[3].set_xlim(t0, t1)
    ax[3].set_ylim(0., 1.1)
    ax[3].plot(distance, surface_albedo)
    ax[3].text(0.01, 0.89, "Surface Albedo", transform=ax[3].transAxes)
    ax[3].set_xticklabels([])

    plot_thickness_profile(df, ax=ax[4])
    ax[4].set_xlabel('m')

    if title:
        fig.suptitle(title)
    
    fig.subplots_adjust(hspace=0.1, top=0.95)

    return fig


def plot_thickness_profile(df, ax=None, snow_depth_exaggeration=1, ice_thickness_var="ice_thickness_m"):
    """Plots a thickness profile from GEM-2 and Magnaprobe data"""
    surface = df.apply(freeboard, axis=1, ice_thickness_var=ice_thickness_var)
    snow_ice_interface = surface - (df.snow_depth_m.where(df.snow_depth_m > 0.) * snow_depth_exaggeration)
    ice_ocean_interface = surface - df[["snow_depth_m", "melt_pond_depth_m"]].max(axis=1) - df[ice_thickness_var]
    pond_depth = surface - df.melt_pond_depth_m.where(df.melt_pond_depth_m > 0.)

    if "transect_distance_m" in df:
        distance = df.transect_distance_m.values
    else:
        distance = transect_distance(df.local_x.values, df.local_y.values)

    ice_surface = pd.concat([snow_ice_interface, pond_depth], axis=1).max(axis=1)
    
    ax.set_xlim(distance[0], distance[-1])
    ax.fill_between(distance, surface, snow_ice_interface, color='0.7')
    ax.fill_between(distance, ice_surface, ice_ocean_interface, color='lightblue')
    ax.fill_between(distance, surface, pond_depth, color='blue')

    # Kluge fix for labels
    ymin = np.floor(ice_ocean_interface.min() / 0.5) * 0.5
    ymax = np.ceil(surface.max() / 0.5) * 0.5
    ax.set_ylim(ymin, ymax)

    ax.set_xlabel("Transect distance (m)")
    ax.set_ylabel("Height Above Sea Level (m)")


def freeboard(x, 
              density_snow=320.,
              density_ice=915.,
              density_sea_water=1024.,
              density_pond_water=1000.,
              ice_thickness_var="ice_thickness_m"):
    """Returns the snow or ice freeboard height above local sea level

    Parameters
    ----------
    x : pandas.DataFrame containing
        snow depth in meters
        pond depth in meters
        thickness in meters
    
    density_ice : density pf ice (default 915 kg/m3 from Petty et al )
    density_snow : density of snow (default 300 kg/m3)
    density_water : density of freshwater (1000 kg/m3)

    Returns
    -------
    Pandas Series with surface height (freeboard) above local sea level
    """
    a = (density_sea_water - density_ice) / density_sea_water
    b = (density_sea_water - density_snow) / density_sea_water
    c = (density_sea_water - density_pond_water) / density_sea_water

    snow_depth = x.snow_depth_m
    pond_depth = x.melt_pond_depth_m
    ice_thickness = x[ice_thickness_var]

    if snow_depth > 0.:
        return a * ice_thickness + b * snow_depth
    elif pond_depth > 0.:
        return a * ice_thickness + c * pond_depth
    else:
        return a * ice_thickness


# For plotting transect summaries

def round_down(x, decimals=0):
    factor = 10**decimals
    return np.floor(x / factor) * factor


def round_up(x, decimals=0):
    factor = 10**decimals
    return np.ceil(x / factor) * factor
    

def get_transect_bound(x, decimals=0):
    xmin, xmax = round_down(x.min(), decimals), round_up(x.max(), decimals)
    xmin = min([xmin, -100])
    xmax = max([xmax, 100])
    return xmin, xmax


def metadata_from_path(fp):
    filename = fp.name
    m = re.search(r"_(\d{8})_(PS\d+-\d+_\d+-\d+)_(.*)", fp.stem)
    if not m:
        raise ValueError("Unable to find matching elements in path")
    date, id, note = m.groups()
    return filename, date, id, note


def plot_location_map(df, ax=None, projection=None):
    ax.set_extent([-180.,180.,65.,90.], ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND)
    ax.gridlines()
    df.plot(ax=ax, kind="scatter", x='lon', y='lat', transform=ccrs.PlateCarree())

    # Find quadrant of RVPS in Arctic Ocean
    xy = projection.transform_point(df.lon.mean(), df.lat.mean(), ccrs.PlateCarree())
    if xy[0] > 0 and xy[1] > 0:
        bounds = [0.05, 0.05, 0.4, 0.4]
    elif xy[0] < 0 and xy[1] > 0:
        bounds = [0.55, 0.05, 0.4, 0.4]
    elif xy[0] < 0 and xy[1] < 0:
        bounds = [0.55, 0.55, 0.4, 0.4]
    else:
        bounds = [0.05, 0.55, 0.4, 0.4]

    x1, x2 = get_transect_bound(df.local_x, decimals=2)
    y1, y2 = get_transect_bound(df.local_y, decimals=2)
    axins = ax.inset_axes(
        bounds,
        xlim=(x1, x2), ylim=(y1, y2), xticklabels=[], yticklabels=[])
    df.plot(ax=axins, x='local_x', y='local_y', title='Transect Path',
           legend=False)  #, xlim=(-100,1000), ylim=(-500,100))
    axins.axhline(ls='--', color='0.5')
    axins.axvline(ls='--', color='0.5')
    axins.scatter(0.,0.)
    axins.set_xlabel("")
    axins.set_ylabel("")


def plot_snow_depth_hist(df, ax=None):
    vmin = np.min([0.,np.round(df.snow_depth_m.min(),2)])
    vmax = np.ceil(df.snow_depth_m.max())
    snow_bins = np.arange(vmin, vmax, 0.01)

    df.snow_depth_m.plot(kind="hist", ax=ax, title="Snow Depth", xlabel="m", bins=snow_bins)


def plot_ice_thickness_hist(df, ax=None):
    df_it = df.loc[:,df.columns.str.contains('ice_thickness')]

    vmin = np.min([0.,np.round(df_it.min().min(),1)])
    vmax = np.ceil(df_it.max().max())
    ice_bins = np.arange(vmin, vmax, 0.1)

    df_it.plot(kind="hist", alpha=0.5, bins=ice_bins, ax=ax, legend=True,
               title='Ice Thickness', xlabel="m")
    handle, label = ax.get_legend_handles_labels()
    new_label = []
    for l in label:
        m = re.search(r"ice_thickness_(\d+khz)_(\w*)_m", l)
        if m:
            new_label.append(' '.join(m.groups()))
    ax.legend(labels=new_label, fontsize=7)


def plot_pond_depth_hist(df, ax=None):
    max_scale_inc = 0.5
    vmin = 0.
    vmax = np.max([np.ceil(df.melt_pond_depth_m.max() / max_scale_inc) * max_scale_inc, 1])
    pond_bins = np.arange(vmin, vmax, 0.01)
    print(vmin, vmax)
    df.melt_pond_depth_m.plot(kind="hist", alpha=0.5, bins=pond_bins, ax=ax, 
                              legend=False, title='Pond Depth', xlabel="m")


def make_transect_summary_plot(df, fp):

    projection = ccrs.NorthPolarStereo()
    
    fig = plt.figure(constrained_layout=False, figsize=(6,8))
    gs = fig.add_gridspec(4, 3, wspace=0)
    hist_grid = gs[2,:].subgridspec(1, 3, wspace=0.05, hspace=0)

    ax1 = fig.add_subplot(gs[0:2, 0:2], aspect='equal', projection=projection)
    ax2 = fig.add_subplot(hist_grid[0, 0])
    ax3 = fig.add_subplot(hist_grid[0, 1])
    ax4 = fig.add_subplot(hist_grid[0, 2])
    ax5 = fig.add_subplot(gs[3, :])

    plot_location_map(df, ax=ax1, projection=projection)

    plot_snow_depth_hist(df, ax=ax2)
    plot_ice_thickness_hist(df, ax=ax3)
    plot_pond_depth_hist(df, ax=ax4)
    for axis in [ax2,ax3,ax4]:
        axis.get_yaxis().set_visible(False)

    if 'ice_thickness_18khz_ip_m' in df:
        ice_thickness_var = 'ice_thickness_18khz_ip_m'
    elif 'ice_thickness_f18325hz_hcp_i_m' in df:
        ice_thickness_var = 'ice_thickness_f18325hz_hcp_i_m'
    else:
        # Just grab the first ice thickness column
        ice_thickness_var = df.columns[df.columns.str.contains('ice_thickness')][0]
    plot_thickness_profile(df, ax=ax5, snow_depth_exaggeration=1, ice_thickness_var=ice_thickness_var)

    # Add test
    filename, date, id, note = metadata_from_path(fp)
    fig.suptitle(f"File: {filename}", fontsize=10)
    fig.text(0.65, 0.775, f"Date: {date}", fontsize=10)
    fig.text(0.65, 0.75, f"ID: {id}", fontsize=10)
    fig.text(0.65, 0.725, f"Note: {note}", fontsize=10)

    return fig
