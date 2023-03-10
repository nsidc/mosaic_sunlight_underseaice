<img alt="NSIDC logo" src="https://nsidc.org/themes/custom/nsidc/logo.svg" width="150" />


# MOSAiC Sunlight Under Sea Ice

`mosaic_sunlight_underseaice` is a collection of Jupyter notebooks and python scripts to estimate under-ice sunlight and photosynthetically active radiation (PAR) for GEM2 ice thickness and Magnaprobe snow depth transects collected during the MOSAiC expedition


## Level of Support

* This repository is not actively supported by NSIDC but we welcome issue submissions and
  pull requests in order to foster community contribution.

See the [LICENSE](LICENSE) for details on permissions and warranties. Please contact
nsidc@nsidc.org for more information.


## Requirements

You will a python installation for `python 3.10`.  The easiest way to do this is install Anaconda or Miniconda.

Underice sunlight and PAR are estimate using the [`seaice_rt`](https://github.com/andypbarrett/seaice_radiative_transfer) package, which is a python wrapper for the CESM2 Delta-Eddington sea ice radiative transfer model.  You will need to follow the installation instructions for this package.

In addition you will need:  
- Jupyter Lab to run the notebooks;  
- `pandas` for reading the transect data;  
- `numpy`;  
- `matplotlib` for plotting the results.  


## Installation

1. [Fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) the `mosaic_sunlight_underseaice` repoisitory into your own GitHub user account.  
2. [Clone](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) this fork onto your local computer.  This will create a `mosaic_sunlight_underseaice` directory.
3. Run the following commands.
```
cd mosaic_sunlight_underseaice
conda env create -f environment.yml
conda activate panarctic_underice_sunlight
```  
4. Follow the installation instructions for [`seaice_rt`](https://github.com/andypbarrett/seaice_radiative_transfer). 


## Usage

The best way to get started is to run the Jupyter notebook [`notebooks/getting_started.ipynb`]().

1. Start Jupyter Lab.  
2. Navigate to the `notebooks` folder.
3. Open `getting_started.ipynb`.  
4. Run the notebook from the drop-down menus **Run**->**Run All Cells**.  Alternatively, you can run each code cell using Shift+Enter. 


## Troubleshooting

If the notebook doesn't run.  Check that `seaice_rt` has been installed correctly.  Follow the troubleshooting procedure in [`seaice_rt`](https://github.com/andypbarrett/seaice_radiative_transfer)

## License

See [LICENSE](LICENSE).


## Code of Conduct

See [Code of Conduct](CODE_OF_CONDUCT.md).


## Credit

This software was developed by the National Snow and Ice Data Center with funding from
multiple sources.
