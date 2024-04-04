import re
import warnings

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from mosaic_underice_sunlight.mosaic_thickness import load_reformatted_combined_data
from mosaic_underice_sunlight.plotting import make_transect_summary_plot
from mosaic_underice_sunlight.filepath import REFORMAT_DATAPATH


def reformatted_files():
    """Returns generator object containing paths to reformatted files"""
    return REFORMAT_DATAPATH.glob("*/*.csv")


def plot_reformatted_transect_data():
    """Generates plots of reformatted transect data"""

    for fp in reformatted_files():
        print(f"Plotting {fp}")
        df = load_reformatted_combined_data(fp)

        # Check shape
        if df.shape[0] == 0:
            warnings.warn(f"No data in {fp}.  Skipping!", RuntimeWarning)
            continue
        
        if not "melt_pond_depth_m" in df:
            df["melt_pond_depth_m"] = 0
        fig = make_transect_summary_plot(df, fp)
        fig.savefig(fp.parent / f"{fp.stem}.png")
        plt.close(fig)
#        break


if __name__ == "__main__":
    plot_reformatted_transect_data()

