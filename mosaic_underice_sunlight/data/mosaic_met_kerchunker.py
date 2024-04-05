"""Generates a kerchunk mapper files for MOSAiC met files

See notebooks/mosaic_met_kerchunker.ipynb for tutorial and description
"""
from pathlib import Path
import os
import ujson
import re
import warnings
from typing import List

import fsspec  # For interfacing with file systems
from kerchunk.hdf import SingleHdf5ToZarr  # The magic sauce
from kerchunk.combine import MultiZarrToZarr  # ... more magic sauce
import xarray as xr  # For opening the kerchunked dataset
from pqdm.threads import pqdm  # To parallelize 

from mosaic_underice_sunlight.filepath import MET_DATAPATHS


def get_filelist(fs: fsspec.filesystem, url: str, glob: str="*") -> List:
    """Returns iterable of local or remote filepaths to create mappers

    fs : fileystem
    url : filepath or url
    glob : glob pattern to search for.  Default is all
    """
    return fs.glob(f"{url}/{glob}")


def make_json_name(fname: str, dout: str='.') -> Path:
    """Returns a file path for the json sidecar file
    that contains the date for the data in the netcdf file.
    This is found from the netcdf filename.

    Parameters
    ----------
    fname : name of file
    dout : path to store JSON file

    Returns
    -------
    Path for JSON file
    """
    m = re.search(r"(\d{8}).*.nc", fname)
    return Path(dout) / f"{m.groups()[0]}.json"


def gen_json(fname: str, outdir: Union[str, Path]='.') -> Union[str, Path]:
    """Generate a single json sidecar file.

    Files are written to a temporary directory.

    Parameters
    ----------
    fname : path of file to be kerchunked
    outdir : directory path to save json files
    """
    so = dict(mode='rb', 
              anon=True, 
              default_fill_cache=False, 
              default_cache_type='first')

    with fs.open(fname, **so) as infile:
        h5chunks = SingleHdf5ToZarr(infile, fname, inline_threshold=300)
        outf = make_json_name(fname, dout='temp')
        outf.parent.mkdir(parents=True, exist_ok=True)
        with fs.open(outf, 'wb') as f:
            f.write(ujson.dumps(h5chunks.translate()).encode());

    return outf


def generate_single_jsons(filelist: List[str], outdir: str='.', n_jobs: int=4) -> List[str]:
    """Generate single JSON reference files for a list of files

    Parameters
    ----------
    filelist : list of files to create JSON reference files using kerchunk
    outdir : path to save files
    n_jobs : number of threads to use

    Returns
    -------
    List of filepaths to JSON reference files
    """
    result = pqdm(flist, gen_json, n_jobs=4)


def generate_multizarr_json(jsonlist: List[Union[str, Path]],
                            multijson: Union[str, Path]) -> Union[str, Path]:
    """Generates a multizarr json

    Parameters
    ----------
    jsonlist : list of filepaths for single jsons to combine
    multijson : path for multizarr json
    
    Returns
    -------
    None
    """
    mzz = MultiZarrToZarr(
        json_list,
        concat_dims=['time'],
        coo_map = {"time": "cf:time"},
        )

    d = mzz.translate()
    with fs.open(multijson, 'wb') as f:
        f.write(ujson.dumps(d).encode())

    return None


def mosaic_met_kerchunker(site: str, jsonname: Union[str, Path]) -> None:
    """Generates multizarr json files for data from a MOSAiC met site

    Parameters
    ----------
    site : identifier for MOSAiC met site.  tower, asfs30, asfs40, asfs50
    jsonname : filepath for multizarr json file

    Returns
    -------
    None
    """

    try:
        url = MET_DATAPATHS[site]
    except KeyError as err:
        raise KeyError(f"Unknown met site identifier.  "
                       f"Expected one of {', '.join(MET_DATAPATHS.keys())}")
        
    src_fs = fsspec.filesystem()
    filelist = get_filelist(src_fs, url, "mosmet*.nc")

    jsonlist = generate_single_jsons(filelist, outdir, n_jobs=4)

    generate_multizarr_json(jsonlist, jsonname)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=("Generates a MultiZarr JSON reference file "
                                                  "for a MOSAiC met site"))
    parser.add_argument("site", type=str, choices=["tower", "asfs30", "asfs40", "asfs50"],
                        help="identifier for MOSAiC met site")
    parser.add_argument("jsonname", type=str,
                        help="filepath to save multizarr json reference file")

    args = parser.parse_args()

    mosaic_met_kerchunker(args.site, args.jsonname)
