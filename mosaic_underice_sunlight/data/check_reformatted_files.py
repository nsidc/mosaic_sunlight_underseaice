"""Checks reformatted files"""

from pathlib import Path

from mosaic_underice_sunlight.mosaic_thickness import load_reformatted_combined_data


REFORMAT_PATH = Path('/home/apbarret/Data/Sunlight_under_seaice/MOSAiC_Observations/reformat/MOSAiC_magnaprobe')


data_bounds = {
    'lon': {'min': -180., 'max': 180.},
    'lat': {'min': 60., 'max': 90.},
    'local_x': {'min': -5000, 'max': 5000.},
    'local_y': {'min': -5000, 'max': 5000.},
    'snow_depth_m': {'min': 0., 'max': 2.0},
    'melt_pond_depth_m': {'min': 0., 'max': 2.0},
    'ice_thickness': {'min': 0., 'max': 5.},
    'surface_type': {'min': 0, 'max': 4},
}


def check_one_column_bound(col):
    if 'ice_thickness' in col.name:
        bmin = data_bounds['ice_thickness']['min']
        bmax = data_bounds['ice_thickness']['max']
    else:
        bmin = data_bounds[col.name]['min']
        bmax = data_bounds[col.name]['max']
    return all((col >= bmin) & (col <= bmax))


def check_data_bounds(df):
    pass


def get_filepath():
    return REFORMAT_PATH.glob('*/*.csv')


def check_reformatted_files():

    for fp in get_filepath():
        print(f"Checking: {fp}")
        df = load_reformatted_combined_data(fp)
        print(df.head())
        print(df.describe())
        if input("Continue? Y/N").lower == "y":
            continue


if __name__ == "__main__":
    check_reformatted_files()
