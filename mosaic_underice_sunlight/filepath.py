from pathlib import Path


DATAPATH = Path.home() / 'Data' / 'Sunlight_under_seaice' / 'MOSAiC_Observations'
RAW_DATAPATH = DATAPATH / 'raw'
REFORMAT_DATAPATH = DATAPATH / 'reformat' / 'MOSAiC_magnaprobe'
PROCESSED_DATAPATH = DATAPATH / 'processed'
CLEAN_DATAPATH = DATAPATH / 'clean'

MET_DATAPATH = DATAPATH / 'Meteorology'
MET_TOWER_DATAPATH = MET_DATAPATH / 'tower' / '3_level_archive' / 'level3.4'
MET_ASFS30_DATAPATH = MET_DATAPATH / 'asfs30' / '3_level_archive_asfs30' / 'level3.4'
MET_ASFS40_DATAPATH = MET_DATAPATH / 'asfs40' / '3_level_archive_asfs40' / 'level3.4'
MET_ASFS50_DATAPATH = MET_DATAPATH / 'asfs50' / '3_level_archive_asfs50' / 'level3.4'

MET_DATAPATHS = {
    'tower': MET_TOWER_DATAPATH,
    'asfs30': MET_ASFS30_DATAPATH,
    'asfs40': MET_ASFS40_DATAPATH,
    'asfs50': MET_ASFS50_DATAPATH,
    }

FILLED_MET_DATAPATH = DATAPATH / 'Meteorology' / 'gap_filled'

VIRTUAL_ZARR_PATH = MET_DATAPATH / 'virtual_zarr'
VIRTUAL_ZARR_JSONS = {
    'tower': VIRTUAL_ZARR_PATH / 'mosaic_met_tower_combined.json',
    'asfs30': VIRTUAL_ZARR_PATH / 'mosaic_met_asfs30.json',
    'asfs40': VIRTUAL_ZARR_PATH / 'mosaic_met_asfs40.json',
    'asfs50': VIRTUAL_ZARR_PATH / 'mosaic_met_asfs50.json',
    }


def cleaned_transects():
    """Returns a list of paths to cleaned transect files"""
    return list((CLEAN_DATAPATH / "MOSAiC_magnaprobe").glob('*/*.csv'))

