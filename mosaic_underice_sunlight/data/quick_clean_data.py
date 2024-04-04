"""Does a quick clean and processing of MOSAiC combine transect files

This needs to be modified to replace the clean file generation script 
I deleted.

Check that activity id string in directory matches activity string in filename
This might need to be done to make sure all files are loaded.
"""
import re
from pathlib import Path

from mosaic_underice_sunlight.filepath import REFORMAT_DATAPATH, CLEAN_DATAPATH
from mosaic_underice_sunlight.mosaic_thickness import parse_raw_combined_data


def get_reformatted_files():
    return [fp for fp in REFORMAT_DATAPATH.glob("*/magnaprobe_and_gem2_transect*.csv")
            if re.search(r"\d{8}_PS122-\d_\d*-\d*_", fp.name)]


def fix_transect_path(f):
    m = re.match(r"(\d{8})(PS122.+)", f.parts[-2])
    return '-'.join(m.groups())


def quick_clean_transect_data():
    """Follows the parse and write new files workflow in parse_data_summary_spreadsheet"""

    p = re.compile(r"\d{8}-PS122-\d+_\d+-\d+")

    for i, f in enumerate(get_reformatted_files()):
#        if not p.match(f.parts[-2]):
#            transect_path = fix_transect_path(f)
#        else:
#            transect_path = f.parts[-2]

        outpath = Path(f.parents[3], "clean", *f.parts[-3:-1])
    
        try:
            df = parse_raw_combined_data(f)
        except Exception as err:
            print(err)
            continue

        print(f"{i} {outpath / f.name}")
        
        outpath.mkdir(parents=True, exist_ok=True)
        df.to_csv(outpath /  f.name)


if __name__ == "__main__":

    quick_clean_transect_data()
