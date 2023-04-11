"""Generates test files for parsing snow depth data.  Files are distinguished by:

1. Different numbers of columns.
2. Different column headings

The different column headings are based on the set of possible columns headings in
the raw data files.

In [6]: columns = []

In [7]: for fp in path.glob('20*/magna+gem2*.csv'):
   ...:     with open(fp) as f:
   ...:         line = f.readline()
   ...:     columns.append(line)
   ...: 

In [8]: set(columns)
Out[8]: 
{'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m)\n',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m),\n',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Ice Thickness f1525Hz_hcp_i (m), Ice Thickness f1525Hz_hcp_q (m) Ice Thickness f5325Hz_hcp_i (m), Ice Thickness f5325Hz_hcp_q (m), Ice Thickness f18325Hz_hcp_i (m), Ice Thickness f18325Hz_hcp_q (m), Ice Thickness f63025Hz_hcp_i (m),Ice Thickness f63025Hz_hcp_q (m), Ice Thickness f93075Hz_hcp_i (m), Ice Thickness f93075Hz_hcp_q (m)\n',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Melt Pond Depth (m), Surface Type, Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m)\n',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Melt Pond Depth (m), Surface Type, Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m),\n',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Melt Pond Depth (m), Surface Type, Ice Thickness 18kHz q (m), Ice Thickness 63kHz q (m), Ice Thickness 93kHz q (m)\n',
 'Date/Time, Lon, Lat, local X, Local Y, Snow Depth (m), Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m),\n'}

"""

from pathlib import Path

import pandas as pd
import numpy as np


header = ['Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m)',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Ice Thickness f1525Hz_hcp_i (m), Ice Thickness f1525Hz_hcp_q (m) Ice Thickness f5325Hz_hcp_i (m), Ice Thickness f5325Hz_hcp_q (m), Ice Thickness f18325Hz_hcp_i (m), Ice Thickness f18325Hz_hcp_q (m), Ice Thickness f63025Hz_hcp_i (m),Ice Thickness f63025Hz_hcp_q (m), Ice Thickness f93075Hz_hcp_i (m), Ice Thickness f93075Hz_hcp_q (m)',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Melt Pond Depth (m), Surface Type, Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m),',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m),',
 'Date/Time, Lon, Lat, local X, Local Y, Snow Depth (m), Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m),',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Melt Pond Depth (m), Surface Type, Ice Thickness 18kHz q (m), Ice Thickness 63kHz q (m), Ice Thickness 93kHz q (m)',
 'Date/Time, Lon, Lat, Local X, Local Y, Snow Depth (m), Melt Pond Depth (m), Surface Type, Ice Thickness 18kHz ip (m), Ice Thickness 5kHz ip (m), Ice Thickness 93kHz ip (m)']

nindex = 5

date = pd.date_range('2023-04-09T06:00:00', periods=nindex, freq='T')
date.name = header[0].split(',')[0]

data = {
    'lon': [0.]*nindex,
    'lat': [90.]*nindex,
    'local x': np.arange(nindex, dtype=float),
    'local y': np.arange(nindex, dtype=float),
    'snow depth (m)': [0., 0.3, 0.3, 0.0, -1.],
    'melt pond depth (m)': [0., 0.3, 0.0, 0.3, -1.],
    'surface type': [2, 1, 1, -1., 2],
    'ice thickness 18khz ip (m)': [10]*nindex,
    'ice thickness f18325hz_hcp_i (m)': [11]*nindex,
    'ice thickness 18khz q (m)': [12]*nindex,
    'ice thickness f18325hz_hcp_q (m)': [13]*nindex,
    'ice thickness 93khz q (m)': [20]*nindex,
    'ice thickness f93075hz_hcp_q (m)': [21]*nindex,
    'ice thickness 93khz ip (m)': [22]*nindex,
    'ice thickness f93075hz_hcp_i (m)': [23]*nindex,
    'ice thickness 63khz q (m)': [30]*nindex,
    'ice thickness f63025hz_hcp_q (m)': [31]*nindex,
    'ice thickness f63025hz_hcp_i (m)': [32]*nindex,
    'ice thickness 5khz ip (m)': [30]*nindex,
    'ice thickness f5325hz_hcp_i (m)': [31]*nindex,
    'ice thickness f5325hz_hcp_q (m)': [32]*nindex,
    'ice thickness f1525hz_hcp_i (m)': [40]*nindex,
    'ice thickness f1525hz_hcp_q (m)': [41]*nindex,
    }

for i, h in enumerate(header):
    columns = h.split(',')[1:]
    if columns[-1] == '':
        columns = columns[:-1]
    data_dict = {c: data.get(c.strip().lower()) for c in columns}
    df = pd.DataFrame(data_dict, columns=columns, index=date)

    outfile = Path('.') / 'tests' / f'magna+gem2-transect-test_file_{i:02d}.csv'
    with open(outfile, 'w') as of:
        of.write(h+'\n')
        df.to_csv(of, header=False)
