"""Test routine for parallel seaicert_mp"""
import pandas as pd

from mosaic_underice_sunlight.rtmodel import seaicert_mp, preprocess

def make_dataframe(n=10):
    index = [pd.to_datetime("2024-06-24 12:00:00")] * n
    df = pd.DataFrame(
        {
            "lat": [85.]*n,
            "snow_depth_m": [.3]*n,
            "melt_pond_depth_m": [0.0]*n,
            "ice_thickness_m": [1.0]*n,
            "surface_temperature_K": [272.0]*n,
            "air_temperature_K": [270.0]*n,
        },
        index = index,
    )
    df.index.name = "date/time"
    return df

    
BIG_DATAFRAME = make_dataframe(360*360)
SMALL_DATAFRAME = make_dataframe(10)


def test_seaicert_mp():
    result = seaicert_mp(SMALL_DATAFRAME, parallel=True)
    print(result)
    print(result.duplicated().all())


def test_preprocess():
    """Tests preprocessing"""
    result = preprocess(SMALL_DATAFRAME.reset_index(names=["time"])) #preprocess(SMALL_DATAFRAME)
    print(result)
    
