"""Functions for plotting"""
import numpy as np
import matplotlib.pyplot as plt

def plot_results(df):

    distance = df.index.values
    sw_absorbed_by_ocean = df.sw_absorbed_by_ocean
    surface_downwelling_radiative_flux = df.surface_downwelling_radiative_flux
    surface_albedo = df.surface_albedo
    
    t0 = distance[0]
    t1 = distance[-1]

    fig, ax = plt.subplots(4, 1, figsize=(10,7))
    ax[0].set_xlim(t0, t1)
    ax[0].plot(distance, sw_absorbed_by_ocean)
    ax[0].set_ylim(np.array(ax[0].get_ylim()) * np.array([0., 1.1]))
    ax[0].set_ylabel("$\mathrm{W\ m^{-2}}$")
    ax[0].text(0.01, 0.89, "SW absorbed by Ocean", transform=ax[0].transAxes)
    ax[0].set_xticklabels([])

    ax[1].set_xlim(t0, t1)
    ax[1].plot(distance, surface_downwelling_radiative_flux)
    ax[1].set_ylim(np.array(ax[1].get_ylim()) * np.array([0., 1.2]))
    ax[1].set_ylabel("$\mathrm{W\ m^{-2}}$")
    ax[1].text(0.01, 0.89, "Surface downwelling flux", transform=ax[1].transAxes)
    ax[1].set_xticklabels([])

    ax[2].set_xlim(t0, t1)
    ax[2].set_ylim(0., 1.1)
    ax[2].plot(distance, surface_albedo)
    ax[2].text(0.01, 0.89, "Surface Albedo", transform=ax[2].transAxes)
    ax[2].set_xticklabels([])

    plot_thickness_profile(df, ax=ax[3])
    ax[3].set_xlabel('m')

    fig.subplots_adjust(hspace=0.1)

#    return fig


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

    ax.set_xlabel("Transect distance (m)")
    ax.set_ylabel("Height (m) [wrt to ice surface]")
    #labels = ax.get_yticklabels()
