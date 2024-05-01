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