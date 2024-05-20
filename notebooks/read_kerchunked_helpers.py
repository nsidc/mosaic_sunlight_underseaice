import pandas as pd

def sample_by_time(ds, hour=None, minute=None):
    """Sample data for a given hour"""

    # Assume sample on-the-hour if minute None
    if hour and not minute:
        idx = ((ds.time.dt.hour == hour) & 
               (ds.time.dt.minute == 0))
    elif hour and minute:
        idx = ((ds.time.dt.hour == hour) & 
               (ds.time.dt.minute == minute))
    elif not hour and minute:
        idx = (ds.time.dt.minute == 0)
    else:
        raise AttributeError("One of hour or minute must be set")

    return ds.sel(time=idx)
    
    
def get_midday_location(ds, longitude="lon", latitude="lat"):
    """Get coordinates for midday"""
    dssub = sample_by_time(ds, hour=12)
    return dssub[longitude], dssub[latitude]


def get_valid_obs(ds):
    """Only get valid observations of skin temperature"""
    obs = ["skin_temp_surface", "lon", "lat"]
    valid = ds[obs].notnull().to_dataframe().any(axis=1).values
    return ds.time.loc[valid]


def event_start(x):
    return x.index[0]

def event_end(x):
    return x.index[-1]

def duration(x):
    return len(x)

def get_missing_stats(x):
    return pd.DataFrame(
        {
            "start": x.apply(event_start),
            "end": x.apply(event_end),
            "duration": x.apply(duration),
        }
    )


def find_missing_periods(s: pd.Series) -> pd.DataFrame:
    """Returns a dataframe containing the start and end dates of periods of missing data,
    and the duration of the missing period.

    s : series to evaluate

    Returns
    -------
    start date, end date and duration of missing periods as DataFrame
    """
    # Code data as missing
    ismissing = s.isnull()
    # Code contiguous missing periods
    missing_coded = (ismissing.diff(1) != 0).cumsum()
    # Group missing periods
    missing_grouped = ismissing[ismissing].groupby(missing_coded[ismissing])
    # Return stats
    return get_missing_stats(missing_grouped)