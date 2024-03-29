"""Test code for clean data"""
from pathlib import Path
import warnings

import pytest

import pandas as pd
import numpy as np

import mosaic_underice_sunlight.data.clean_mosaic_data as clean_data
import mosaic_underice_sunlight.mosaic_thickness as mosaic_thickness


TESTPATH = Path("tests")


@pytest.mark.parametrize(
    "fix,expected",
    [
        (False, [-1., -0.1, 0., 1, 2., np.nan, 3., 4., np.nan]),
        (True, [np.nan, np.nan, 0., 1., 2., np.nan, 3., np.nan, np.nan]),
    ]
)
def test_check_data_range(fix, expected):
    test_data = [-1., -0.1, 0., 1, 2., np.nan, 3., 4., np.nan]
    min_expected_value = 0.
    max_expected_value = 3.

    time_index = pd.date_range('2023-04-07', periods=len(test_data), freq='T')

    test_series = pd.Series(test_data, index=time_index)
    expected_series = pd.Series(expected, index=time_index)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = clean_data.check_data_range(test_series,
                                             min_expected_value,
                                             max_expected_value,
                                             fix=fix)
        assert len(w) == 1
        assert issubclass(w[-1].category, UserWarning)
        assert "out of range" in str(w[-1].message).lower()

    assert result.equals(expected_series)


def test_infer_surface_type():
    test_df = pd.DataFrame({
        'snow_depth_m': [0.3, 0., 0., .2],
        'melt_pond_depth_m': [0., .5, 0., .3],
        })
    expected = pd.Series([1, -1, 2, np.nan])
    result = mosaic_thickness.infer_surface_type(test_df)
    print(result)
    print(expected)
    assert result.equals(expected)


    """Test to check correct columns returned.
       Test to check logic of alternative columns
       Test to check correct values returned.
       May be idea to move ice_thickness_m, snow_depth_m and melt_pond_depth_m
       to functions.
    """

@pytest.mark.parametrize(
    "test_file,expected_columns",
    [
        (
            "magna+gem2-transect-test_file_00.csv",
            [
                "lon", "lat", "local_x", "local_y", "snow_depth_m",
                "ice_thickness_18khz_ip_m", "ice_thickness_5khz_ip_m",
                "ice_thickness_93khz_ip_m",
            ]
        ),
        (
            "magna+gem2-transect-test_file_01.csv",
            [
                "lon", "lat", "local_x", "local_y", "snow_depth_m",
                "ice_thickness_f1525hz_hcp_i_m", "ice_thickness_f1525hz_hcp_q_m",
                "ice_thickness_f5325hz_hcp_i_m", "ice_thickness_f5325hz_hcp_q_m",
                "ice_thickness_f18325hz_hcp_i_m", "ice_thickness_f18325hz_hcp_q_m",
                "ice_thickness_f63025hz_hcp_i_m", "ice_thickness_f63025hz_hcp_q_m",
                "ice_thickness_f93075hz_hcp_i_m", "ice_thickness_f93075hz_hcp_q_m",
            ]
        ),
        (
            "magna+gem2-transect-test_file_02.csv",
            [
                "lon", "lat", "local_x", "local_y", "snow_depth_m",
                "melt_pond_depth_m", "surface_type",
                "ice_thickness_18khz_ip_m", "ice_thickness_5khz_ip_m",
                "ice_thickness_93khz_ip_m",
            ]
        ),
        (
            "magna+gem2-transect-test_file_03.csv",
            [
                "lon", "lat", "local_x", "local_y", "snow_depth_m",
                "ice_thickness_18khz_ip_m", "ice_thickness_5khz_ip_m",
                "ice_thickness_93khz_ip_m",
            ]
        ),
        (
            "magna+gem2-transect-test_file_04.csv",
            [
                "lon", "lat", "local_x", "local_y", "snow_depth_m",
                "ice_thickness_18khz_ip_m", "ice_thickness_5khz_ip_m",
                "ice_thickness_93khz_ip_m",
            ]
        ),
        (
            "magna+gem2-transect-test_file_05.csv",
            ["lon", "lat", "local_x", "local_y", "snow_depth_m",
             "melt_pond_depth_m", "surface_type",
             "ice_thickness_18khz_q_m", "ice_thickness_63khz_q_m",
             "ice_thickness_93khz_q_m",
            ]
        ),
        (
            "magna+gem2-transect-test_file_06.csv",
            [
                "lon", "lat", "local_x", "local_y", "snow_depth_m",
                "melt_pond_depth_m", "surface_type",
                "ice_thickness_18khz_ip_m", "ice_thickness_5khz_ip_m",
                "ice_thickness_93khz_ip_m",
            ]
        ),
    ]
)
def test_load_raw_data(test_file, expected_columns):
    """Checks that correct column names returned"""
    result = mosaic_thickness.load_raw_combined_data(TESTPATH / test_file)
    assert list(result.columns) == expected_columns

@pytest.mark.parametrize(
    "test_file,expected_thickness,expected_flag",
    [
        (
            "magna+gem2-transect-test_file_00.csv",
            10, 1
        ),
        (
            "magna+gem2-transect-test_file_01.csv",
            13, 2
        ),
        (
            "magna+gem2-transect-test_file_02.csv",
            10, 1
        ),
        (
            "magna+gem2-transect-test_file_03.csv",
            10, 1
        ),
        (
            "magna+gem2-transect-test_file_04.csv",
            10, 1
        ),
        (
            "magna+gem2-transect-test_file_05.csv",
            np.nan, 0
        ),
        (
            "magna+gem2-transect-test_file_06.csv",
            10, 1
        )
    ]
)
def test_assign_ice_thickness(test_file, expected_thickness, expected_flag):
    """Tests that correct thickness column is assigned"""
    df = mosaic_thickness.load_raw_combined_data(TESTPATH / test_file)
    mosaic_thickness.assign_ice_thickness(df)
    df_expected = pd.DataFrame(
        {
            'ice_thickness_m': [expected_thickness]*len(df),
            'ice_thickness_flag': [expected_flag]*len(df),
        },
        index=df.index,
    )
    assert df.ice_thickness_m.equals(df_expected.ice_thickness_m)
    assert df.ice_thickness_flag.equals(df_expected.ice_thickness_flag)


@pytest.mark.parametrize(
    "test_file,expected_snow",
    [
        (
            "magna+gem2-transect-test_file_00.csv",
            [0., 0.3, 0.3, 0., 0.]
        ),
    ]
)
def test_assign_snow_depth(test_file, expected_snow):
    """Test that correct snow depth is assigned"""
    df = mosaic_thickness.load_raw_combined_data(TESTPATH / test_file)
    mosaic_thickness.assign_snow_depth(df)
    df_expected = pd.Series(expected_snow, index=df.index)
    print(df.snow_depth_m)
    print(df_expected)
    assert df.snow_depth_m.equals(df_expected)


@pytest.mark.parametrize(
    "test_file,expected_pond_depth",
    [
        (
            "magna+gem2-transect-test_file_02.csv",
            [0., 0.3, 0., 0.3, 0.]
        ),
        (
            "magna+gem2-transect-test_file_00.csv",
            [0., 0., 0., 0., 0.]
        ),
    ]
)
def test_assign_melt_pond_depth(test_file, expected_pond_depth):
    df = mosaic_thickness.load_raw_combined_data(TESTPATH / test_file)
    mosaic_thickness.assign_melt_pond_depth(df)
    df_expected = pd.Series(expected_pond_depth, index=df.index)
    print(df.melt_pond_depth_m)
    print(df_expected)
    assert df.melt_pond_depth_m.equals(df_expected)


@pytest.mark.parametrize(
    "test_file",
    [
        ("magna+gem2-transect-test_file_00.csv"),
        ("magna+gem2-transect-test_file_01.csv"),
        ("magna+gem2-transect-test_file_02.csv"),
        ("magna+gem2-transect-test_file_03.csv"),
        ("magna+gem2-transect-test_file_04.csv"),
        ("magna+gem2-transect-test_file_05.csv"),
        ("magna+gem2-transect-test_file_06.csv"),
    ]
)
def test_parse_data_columns(test_file):
    expected_columns = ['lon', 'lat', 'local_x', 'local_y',
                        'ice_thickness_m', 'snow_depth_m',
                        'melt_pond_depth_m', 'surface_type',
                        'transect_distance_m', 'ice_thickness_flag']
    df = mosaic_thickness.parse_raw_combined_data(TESTPATH / test_file)
    assert all(df.columns == expected_columns)
