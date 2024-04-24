"""Generates a kerchunk mapper files for MOSAiC met files

See notebooks/mosaic_met_kerchunker.ipynb for tutorial and description
"""
from pathlib import Path
import os
import ujson
import re
import warnings
from typing import List, Union
import tempfile
from urllib.parse import urlparse

import fsspec  # For interfacing with file systems
from kerchunk.hdf import SingleHdf5ToZarr  # The magic sauce
from kerchunk.combine import MultiZarrToZarr  # ... more magic sauce
import xarray as xr  # For opening the kerchunked dataset
from pqdm.threads import pqdm  # To parallelize 

from mosaic_underice_sunlight.filepath import MET_DATAPATHS


def get_filelist(url: str, glob: str="*") -> List:
    """Returns iterable of local or remote filepaths to create mappers

    fs : fileystem
    url : filepath or url
    glob : glob pattern to search for.  Default is all
    """
    fs = fsspec.filesystem(get_protocol(url)) 
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

    with fsspec.open(fname, **so) as infile:
        h5chunks = SingleHdf5ToZarr(infile, fname, inline_threshold=300)
        outf = make_json_name(fname, dout=outdir)
        outf.parent.mkdir(parents=True, exist_ok=True)
        with fsspec.open(outf, 'wb') as f:
            f.write(ujson.dumps(h5chunks.translate()).encode());

    return str(outf)


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
    args = [[f, outdir] for f in filelist]
    result = pqdm(args, gen_json, n_jobs=4, argument_type='args')
    return result


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
        jsonlist,
        concat_dims=['time'],
        coo_map = {"time": "cf:time"},
        )

    d = mzz.translate()
    with fsspec.open(multijson, 'wb') as f:
        f.write(ujson.dumps(d).encode())

    return None


def get_protocol(url):
    """Returns the protocol based on urllib scheme"""
    return urlparse(str(url)).scheme


def mosaic_met_kerchunker(site: str,
                          jsonname: Union[str, Path],
                          test: bool=False) -> None:
    """Generates multizarr json files for data from a MOSAiC met site

    Parameters
    ----------
    site : identifier for MOSAiC met site.  tower, asfs30, asfs40, asfs50
    jsonname : filepath for multizarr json file

    Returns
    -------
    None
    """

    tempdirname = Path('temp')
    
    try:
        url = MET_DATAPATHS[site]
    except KeyError as err:
        raise KeyError(f"Unknown met site identifier.  "
                       f"Expected one of {', '.join(MET_DATAPATHS.keys())}")

#    src_fs = fsspec.filesystem(get_protocol(url))
    filelist = get_filelist(url, "mosmet*.nc")

    if test:
        filelist = filelist[:10]
    
    jsonlist = generate_single_jsons(filelist, tempdirname, n_jobs=4)
    generate_multizarr_json(jsonlist, jsonname)

    cleanup(tempdirname)


def cleanup(tempdirname):
    for root, dirs, files in tempdirname.walk(top_down=False):
        for name in files:
            (root / name).unlink()
        for name in dirs:
            print(root / name)
    if ('.' / tempdirname).exists() & (str(tempdirname) != '.'):
        tempdirname.rmdir()
    else:
        warnings.warn(f"{tempdirname} is current working directory: did not remove it")


def load_metdata_zarr(jsonmzz: Union[str, Path]) -> xr.Dataset:
    """Loads a multizarr file"""
    backend_args = {
        "consolidated": False,
        "storage_options": {
            "fo": str(jsonmzz),
            }
        }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ds = xr.open_dataset(
            "reference://",
            engine="zarr",
            backend_kwargs=backend_args
            )
    return ds


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=("Generates a MultiZarr JSON reference file "
                                                  "for a MOSAiC met site"))
    parser.add_argument("site", type=str, choices=["tower", "asfs30", "asfs40", "asfs50"],
                        help="identifier for MOSAiC met site")
    parser.add_argument("jsonname", type=str,
                        help="filepath to save multizarr json reference file")
    parser.add_argument("--test", action='store_true',
                        help="run test.  Only processes first 10 files")

    args = parser.parse_args()

    mosaic_met_kerchunker(args.site, args.jsonname, test=args.test)
