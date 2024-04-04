"""Reformats Combined MagnaProbe and Gem2 data

Remove trailing , in header
Fix column headings
Check all rows have same number of fields
"""
import re
from pathlib import Path

from mosaic_underice_sunlight.mosaic_thickness import combined_files


REFORMAT_PATH = Path('/home/apbarret/Data/Sunlight_under_seaice/MOSAiC_Observations/reformat/MOSAiC_magnaprobe')

ACTIVITY_PATTERN = re.compile(r"(\d{8})[_-]*(PS122-\d+[_-]\d+[_-]\d+)")


def check_column_counts(header, data):
    """Checks number of header columns match number of data columns

    Assume files are csv
    """
    passed = True
    
    nheader = len(header.split(','))
    nfield = [len(l.split(',')) for l in data]

    count_match = [nheader == nf for nf in nfield]

    if len(set(count_match)) > 1:
        print("More than one mismatching row length in data: {set(nfield)}")
        passed = False

    if not all(set(count_match)):
        print(f"Found {nheader} header columns and {set(nfield)} data columns")
        passed = False
    
    return passed


def read_combined_file(fp):
    """Reads combined file for reformatting"""
    with open(fp) as f:
        header = f.readline().strip()
        data = [l.strip() for l in f.readlines()]
    return header, data


def remove_trailing_comma(header):
    """Removes trailing comma from header"""
    return header[:-1]


def check_missing_comma_in_header(header):
    """Checks for a missing comma between header column names

    In some files Ice Thickness columns are missing a comma delimiter

    e.g. "Ice Thickness f1525Hz_hcp_i (m), Ice Thickness f1525Hz_hcp_q (m) Ice Thickness f5325Hz_hcp_i (m),"
    """
    return re.findall(r"\(m\) ", header)


def fix_missing_comma_in_header(header):
    """Add missing comma between column headings"""
    return re.sub(r"\(m\) ", "(m), ", header)


def reformat_header(header):
    """Converts header to lower case, removes brackets and replaces
    whitespace in header"""
    return ','.join(['_'.join(s.strip().lower().replace('(','').replace(')','').split())
            for s in header.split(',')])


def write_reformatted_data(header, data, outfile):
    """Write a new file with reformated data"""
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with open(outfile, "w") as of:
        of.write(header+"\n")
        [of.write(l+"\n") for l in data]


def make_output_filepath(fp):
    """Generates output filepath"""
    activity_dir, filename = fp.parts[-2:]
    return REFORMAT_PATH / fix_activity(activity_dir) / fix_filename(filename)


def check_data_fields(header, data):
    """Checks number of data fields matches number of column headings.

    Assumes header is correct
    """
    nheader = len(header.split(','))
    nfield = [len(l.split(',')) for l in data]

    return all([nf == nheader for nf in nfield])


def fix_data_line(nheader, line):
    if line.endswith(','):
        line = line[:-1]
    fields = line.split(',')
    nfield = len(fields)
    nmissing = nheader - nfield
    return ','.join(fields + ['nan']*nmissing)


def fix_data_fields(header, data):
    nheader = len(header.split(','))

    full_columns = lambda x: len(x.split(',')) == nheader

    newdata = [fix_data_line(nheader, line) if not full_columns(line) else line for line in data]
    return newdata


def reformat_combined_file(fp, verbose=False):
    """Fixes formatting issues in combined Magnaprobe files"""
    if verbose: print(f"Checking {fp}")
    
    header, data = read_combined_file(fp)

    # Check header column count matches data column count
    if not check_column_counts(header, data):

        # Fix header
        if header.endswith(','):
            header = remove_trailing_comma(header)

        if check_missing_comma_in_header(header):
            header = fix_missing_comma_in_header(header)

        if check_data_fields(header, data):
            data = fix_data_fields(header, data)
            
        if not check_column_counts(header, data):
            raise ValueError("Mismatch between header and data columns persists")
        
    header = reformat_header(header)

    outpath = make_output_filepath(fp)
    if verbose: print(f"Writing reformatted data to {outpath}")
    write_reformatted_data(header, data, outpath)


def fix_activity(s):
    m = ACTIVITY_PATTERN.search(s)
    if m:
        date, activity = m.groups()
    else:
        raise ValueError("No match for date and activity pattern")
    return '_'.join([date, activity])


def parse_filename(fn):
    """Returns date, leg, activity, and location info from filename"""
    p = re.compile(r"(\d{8})[_-]*(PS122[_-]\d+)[_-]*(\d+[_-]+\d*)_(.*).csv")
    m = p.search(fn)
    if m:
        return m.groups()
    else:
        raise ValueError("No match for filename pattern")
    
    
def fix_filename(fn):
    """Modifies filename to contain only characters that
    are in the Portable Filename Character set.

    A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    a b c d e f g h i j k l m n o p q r s t u v w x y z
    0 1 2 3 4 5 6 7 8 9 . _ -
    """
    date, leg, activity, location = parse_filename(fn)
    return f"magnaprobe_and_gem2_transect_{date}_{leg}_{activity}_{location}.csv"


def fix_transect_path(fp):
    """Converts transect ID in path and filename to a common format"""
    activity_dir, filename = fp.parts[-2:]
    return fp.parents[2] / fix_activity(activity_dir) / fix_filename(filename)


def reformat_combined_files(verbose=False):
    filepath = combined_files()
    nfile = len(filepath)

    for fp in filepath:
        try:
            reformat_combined_file(fp, verbose=verbose)
        except Exception as err:
            print(err)
    

if __name__ == "__main__":
    reformat_combined_files(verbose=True)
