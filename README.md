# xrt_workflow
This repository describes the workflow for analysing Swift-XRT data for *point sources*. I have never analysed an extended source. The analysis is done per observation ID (ObsID) and produces spectra for each ObsID. Integral fluxes (for a lightcurve) are computed using XSpec's `flux` command. If you wish to stack the data of multiple ObsIDs, I believe this is done with XSpec (Step 6 below).

You will need the [dependencies](#requirements) installed.
This workflow uses Python and Bash and the two are clunkily linked together with one [config file](src/default_config.cfg). 
Note that to complete the config file you need to know the modes of each observation (Step 4 below).

An overview of the workflow is below. **You need to run scripts from within the src folder.**
1. Determine the list of ObsIDs you want to observe and write config file; [see here for an example config file](src/default_config.cfg). You should be able to follow along using [src/default_config.cfg](src/default_config.cfg) and [src/entire_workflow.sh](src/entire_workflow.sh).
2. `python swifttools_ana.py --cfg_fn CFG_FN`, where `CFG_FN` is the path to the config file
    * Download data products.
3. `./unpack_swifttools_output.sh CFG_FN`
    * Unzip and untar downloaded data products.
4. `python utils.py --cfg_fn CFG_FN`
    * Determine which mode (PC/WT) to use for the analysis. This script will output the mode and corresponding observation livetime. Sometimes, one ObsID has observations in both modes, and one is usually shorter than the other; use the longer duration observation.
5. `./run_grppha.sh CFG_FN`
    * Group the spectra to a minimum of 20 counts per bin, for chi-squared statistics.
6. `./xspec_models/powlaw_tbabs.sh CFG_FN`, `./xspec_models/powlaw_ztbabs_tbabs.sh CFG_FN`, `./xspec_models/logpar_tbabs.sh CFG_FN`
    * Fit the data with several models using XSpec.
7. `python analyse_output.py --cfg_fn CFG_FN`
    * Compare the XSpec models.

**The output of the full workflow is described in [Output](#output).**

The process is detailed below.

# Requirements
* [xrt_prods](https://www.swift.ac.uk/user_objects/API/). I am using v3.0.23, in case it matters
    * Alternately, you can download the data from the [website](https://www.swift.ac.uk/user_objects/), in which case you don't need to install xrt_prods. However the paths in this workflow assume the data was obtained from xrt_prods, and if not you will need to take care to edit the paths and rest of the code.
* XSpec (I downloaded XSpec as part of [HEASoft](https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/download.html)). I am using v12.12.1, in case it matters.
* Other standard Python packages are listed below. I noted the versions but I let the conda/pip install figure it out.
    * I am using Python 3.6.15 and I installed [dataclasses](https://pypi.org/project/dataclasses/) with pip. Alternately Python 3.7+ has dataclasses included.
    * astropy (I am using v4.1)
    * matplotlib (I am using v3.3.4)
    * numpy (I am using v1.19.5)


# Workflow

You should be able to follow along with [default_config.cfg](src/default_config.cfg) to produce the outputs along the way; minimally, **change `EMAIL`** and `BASE_DATA_DIR`.
Again, the output of the full workflow is described in [Output](#output).

## 1. Get ObsIDS and write config file

The ObsIDs can be found at [Browse: Swift Mission](https://heasarc.gsfc.nasa.gov/cgi-bin/W3Browse/swift.pl) by searching e.g. "Object Name"; the resulting page will have a table which includes a column named "obsid". 
Determine which ObsIDs you want to analyse.
Make a copy of default_config.cfg and edit `OIDS` to list the ObsIDS you want to analyse.
The variable `MODES` is not used until Step 5, so you can leave the variable as is for now.
**Please change `EMAIL` to your own!**
Also change the `BASE_DATA_DIR`.
The data and analysis will be in subfolders of `BASE_DATA_DIR`.

## 2. Download data products

-> `python swifttools_ana.py --cfg default_config.cfg`

Build Swift-XRT products using the [Build Swift-XRT products website](https://www.swift.ac.uk/user_objects/) or using Python (Python is recommended by me, and this is the method described below). 
For *point sources*, the online tools are the better option compared to following the [XRT threads](https://www.swift.ac.uk/analysis/xrt/); see [Why use the online tools?](#why-use-the-online-tools)

To use Python to download the data products, first install the xrt_prods module as described on the [The xrt_prods Python module page](https://www.swift.ac.uk/user_objects/API/). Read the documentation as well. 
You need to [Register for the XRT product tools](https://www.swift.ac.uk/user_objects/register.php); the email you register with needs to match the `EMAIL` in the config file.


The script [src/swifttools_ana.py](src/swifttools_ana.py) generates one spectrum per observation ID (ObsID); this script is nearly entirely copied from the [documentation for xrt_prods](https://www.swift.ac.uk/user_objects/API/). 
If you wish to download different data products (e.g. lightcurves), take a look at the [documentation for xrt_prods](https://www.swift.ac.uk/user_objects/API/RequestJob.md#configurable-parameters) and edit src/swifttools_ana.py accordingly. 

Running src/swifttools_ana.py will produce the following file per ObsID: `{BASE_DATA_DIR}/{OID}/{SPEC_STEM}.zip`. The variables `BASE_DATA_DIR` and `SPEC_STEM` are set in the config file; `OID` is each ObsID in `OIDS`.

## 3. Unpack data products

-> `./unpack_swifttools_output.sh default_config.cfg`

A script which does the necessary unzipping and untarring for many ObsIDs is `src/unpack_swifttools_output.sh`.
Unzip `{BASE_DATA_DIR}/{OID}/{SPEC_STEM}.zip` via `unzip`, which will produce a subfolder with name starting with USERPROD: 
`{BASE_DATA_DIR}/{OID}/{SPEC_STEM}/USERPROD*/{SPEC_STEM}/Obs_{OID}.tar.gz`; here `*` denotes a wildcard.
You need to untar `Obs_{OID}.tar.gz`  using `tar -xvf`.

Here is an example of the output for `OID=00032646038` and `SPEC_STEM=spec`. These are all downloaded within the directory `{BASE_DATA_DIR}`.

```shell
├──{BASE_DATA_DIR}
    ├── 00032646038
       ├── spec.zip
       └── USERPROD_224850
           └── spec
               ├── GRB_info.txt
               ├── Obs_00032646038.areas
               ├── Obs_00032646038.tar.gz
               ├── Obs_00032646038wt.arf
               ├── Obs_00032646038wtback.pi
               ├── Obs_00032646038wt_nofit_fit.fit
               ├── Obs_00032646038wt.pi
               ├── Obs_00032646038wt.rmf
               ├── Obs_00032646038wtsource.pi
               ├── README.txt
               └── scripts
                   ├── init.xcm
                   └── plot.xcm
```

Note that the SED points in `Obs_00032646038wt.pi` produced from the online tool are **not** nH-deabsorbed, as is required for use in modeling codes such as Bjet_MCMC. `Obs_00032646038wt.pi` was also binned/grouped for C-stats (addressed in Step 5).

## 4. Determine PC/WT mode for each ObsID and update config file

-> `python utils.py --cfg_fn default_config.cfg`

<details>
<summary> Expand for example output</summary>
<pre>
ObsID 00032646038 does not have a pc observation, looking in directory ../output/00032646038/USERPROD*/*pcsource.pi
Mode and livetime (sec): {'wt': 1121.192896262898}. If observations were conducted in both modes, use the larger livetime.

ObsID 00032646039 does not have a wt observation, looking in directory ../output/00032646039/USERPROD*/*wtsource.pi
Mode and livetime (sec): {'pc': 432.0327580237033}. If observations were conducted in both modes, use the larger livetime.
</pre>
</details>

Sometimes, one ObsID has observations in both PC and WT mode. In all my cases, one mode had a much shorter observation than the other (tens of seconds compared to hundreds-thousands of seconds); in these cases the observation likely started in one mode and then switched to other based on the count rate.

The script will print the livetimes of each mode. Use the longer one.
The ObsIDs given in the sample config only have one mode per ObsID; 00032646038 is a WT mode observation and 00032646039 is a PC mode observation.
Thus, update the config to read
```shell
OIDS="00032646038 00032646039"
MODES="wt pc"
```
where the first element of `OIDS` corresponds to the first element of `MODES` and so on.

## 5. Group spectra for chi-squared statistics

-> `./run_grppha.sh default_config.cfg`

The grouping by the online tools is a minimum of 1 count per bin for use with C-stats. Last I used the online tools, this could not be changed. 
I will rebin with `grppha` for 20 counts minimum per bin, for chi-squared statistics.  
If everything went well, this message will print to the screen `grppha 3.1.0 completed successfully`; also see [_grphha.log](default_output/00032646038/USERPROD_224850/_grppha.log).

The `grppha` command is part of [HEASoft](https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/download.html). 
([Here](https://docs.google.com/document/d/1LhPhsc2kH8Whkl2YHg6hduw-ML0f4T05MQQEEWHp3Os/edit?usp=sharing) is an old document describing how I downloaded some HEAsoft tools, but links within it are now dead...)


##  6. Fit data with XSpec/PyXspec using several models

First, find the Galactic nH value for your source and edit `NH_TBABS` in the config file.
You can use the tool [Galactic NH](https://www.swift.ac.uk/analysis/nhtot/index.php), which gives the atomic + molecular Hydrogen density.
XSpec has a tool which gives the atomic Hydrogen density.
Here is the relevant correspondance with the helpdesk:
> [`nh` command in XSpec] "gives the Galactic column density of HI - ie Hydrogen atoms only. 
> However, in reality there are also H2 molecules which absorb the photons as well. 
> There is an online tool to calculate total (HI+H2) column density here:  https://www.swift.ac.uk/analysis/nhtot/index.php 
> This is the value the product generator (https://www.swift.ac.uk/user_objects/) uses, since it gives a more accurate estimate."
 
You can use XSpec or PyXspec.

### XSpec

-> `./xspec_models/powlaw_tbabs.sh default_config.cfg`, `./xspec_models/powlaw_ztbabs_tbabs.sh default_config.cfg`, `./xspec_models/logpar_tbabs.sh default_config.cfg`

This fits the data with several models:
* powlaw_tbabs.sh: Galactic absorbed powerlaw with fixed nH. The normalization and photon index are free.
* powlaw_ztbabs_tbabs.sh: Galactic and intrinsic absorbed powerlaw. Galactic nH is fixed. Redshift is fixed. nH at the source is free. The normalization and photon index are free parameters.
* logpar_tbabs.sh: Galactic absorbed logparabola with fixed nH and fixed pivot energy. Free parameters: alpha, beta, normalization. This is **log base 10**.

Note that plots pop-up to the screen. This may be annoying. 
I don't know a way around it, if you want to make the plots.
If you run the Bash scripts with e.g. `nohup` and the close/logout the terminal, the process continues but the .png plots aren't made.

These XSpec bash scripts use tcl commands to write the data table. You can also use `wd` but note that the output of this depends on what you plotted with `iplot` and in what order you issued the commands (described a bit [here](https://www.facebook.com/groups/320119452570/posts/10156553313542571/)). 
Craig A. Gordon from the help desk provided immense help with writing to a table with tcl within XSpec.
Tools to read the tcl produced tables are in [src/read_output.py](src/read_output.py).

Outputs produced are described in [Output](#output).


### PyXspec
PyXspec users -- looking for input here.


## 7. Compare XSpec models

-> `python analyse_output.py --cfg_fn default_configs.cfg`

This produces some plots as described in [Output](#output) to compare the different models. Here are some things to consider, but this is not exhaustive:
* Is there a difference in the unfolded spectral points which will be used for modeling in Bjet_MCMC (for example)? If not, consider using the simplest model. 
* Is there a difference in the integral fluxes? If not, consider using the simplest model. 
* Are there differences in the reduced chi-squares? Does one model consistently have the best reduced chi-squared? If so, consider using this model.
* Is the beta parameter in the log parabola model consistent with zero? If so, use the powerlaw.
* Did any of the fits fail? Look at the `error_string` column in [param_tbl.dat](default_output/00032646038/USERPROD_224850/spec/logpar_tbabs/param_tbl.dat) and check for instances of 'T', which is done in `analyse_output.py`. If there were errors, the output may look like
```shell
There is an issue in the calculation of the parameter(s) error: ['ztbabs_nh'] in ../output/00032646038/USERPROD_224850/powlaw_ztbabs_tbabs/param_tbl.dat.
HOWEVER, the parameter may still have a reported best fit value and bounds. Consider refitting or treat these values carefully?
	For parameter ztbabs_nh, the fit failed because: hit hard lower limit
	For parameter ztbabs_nh, the fit failed because: search failed in -ve direction
```
This error string is described in "Section 5.3.12 tclout" of Xspec Users’ Guide for version 12.12.1.

# Output

You can read the output tables using functions in src/read_outputs.py.
Example output is in [default_output](default_output/); this should be identical to the results of following along with the example config, *with the exception of a different string of numbers after USERPROD in the pathnames.* I have not tested this workflow in the case of there being multiple USERPROD directories under one `OID` directory.

Below is a list of the final science outputs for each XSpec script; these are created for *each* model tested. Log files (filenames end with .log) are created along the way too. You can explore the full output of [default_output/](default_output/), as I only list the final produces here.
Recall - If you run the Bash scripts with e.g. `nohup` and the close/logout the terminal, the process continues but the eflux.png, phflux.png, and resid.png plots aren't made.

XSpec output:
* [eflux.png](default_output/00032646038/USERPROD_224850/spec/powlaw_tbabs/eflux.png)
    * XSpec-produced plots of energy flux; the upper plot is the model and the lower plot is the unfolded spectral points.
* [phflux.png](default_output/00032646038/USERPROD_224850/spec/powlaw_tbabs/phflux.png)
    * XSpec-produced plot of photon flux.
* [resid.png](default_output/00032646038/USERPROD_224850/spec/powlaw_tbabs/resid.png)
    * Plot of the residuals with default binning, as the rebinned residual are 'meaningless'; the fit is done with the default bins and rebinning does not change the fit.  
* [param_tbl.dat](default_output/00032646038/USERPROD_224850/spec/powlaw_tbabs/param_tbl.dat)
    * Parameter data table with explicit header: ***name param param_low param_high error_string***, which are the parameter name, its best fit value, its one-sigma lower bound, one-sigma upper bound, and error report.
    * The *uncertainties* on the parameters are `param - param_low` and `param_high - param`, as Xspec reports the bounds. The bounds are one-sigma bounds.
    * Note - "The screen output at the end of the fit shows the best-fitting parameter values, as well as approximations to their errors. These errors should be regarded as indications of the uncertainties in the parameters and should not be quoted in publications. The true errors, i.e. the confidence ranges, are obtained using the error command." (Source: XSpec Manual Users’ Guide for version 12.12.1). I used the error command.
    * error_string: 'If everything went well, the error string should be “FFFFFFFFF'" (Source: XSpec Manual Users’ Guide for version 12.12.1). I put 0 if there is no error string which is the case if the row does not refer to a model parameter. 
    * This table has rows for each of the parameters in the particular model, as well as a row for the integral `flux` (ph/cm^2/s) between 2-10 keV This is the flux *with* absorption (from 2-10 keV so there is not a lot of absorption). (The flux without absorption can be calculated with `cflux` maybe ?).
    * countrate: is in counts/second 
 
* [spec_default_bin.dat](default_output/00032646038/USERPROD_224850/spec/powlaw_tbabs/spec_default_bin.dat)
    * SED data table with default energy binning (the finest/smallest energy binning), with _implicit_ header: ***energy (keV), energy half bin width (keV), energy flux (keV/cm^2/s), energy flux error (keV/cm^2/s), model energy flux (keV/cm^2/s)***. This file does not actually have a header. The energy flux and model energy flux should be equal up to several decimal places (but not identical, as verified by the XSpec help desk).
* [stat_tbl.dat](default_output/00032646038/USERPROD_224850/spec/powlaw_tbabs/stat_tbl.dat)
    * Statistics data table with explicit header: ***chi_squared deg_freedom null_hyp_probability*** and one row.  
    * It contains the chi-squared, degrees of freedom, and null hypothesis probability
* spec_binned.dat
    * Binned spectrum. I never use this file, but I included it here in case the user wants to update the XSpec scripts to adjust the binning and use the resulting binned file instead of the default binned file.

Outputs from analyse_data.py:
* [lightcurve_phflux.png](default_output/lightcurve_phflux.png)
    * Lightcurve of photon flux (2-10 keV) calculated using all XSpec models and all ObsIDs.
* [lightcurve.csv](default_output/lightcurve.csv)
     * Table used to make lightcurve_phflux.png in case user wants to plot the table themselves.
* [spec_all_models_{OID}.png](default_output/spec_all_models_00032646038.png)
    * `OID` is a placeholder for the ObsID. This overplots all XSpec models. This is a way to check the impact of the choice of models on the points that are used for SED modeling.
* [spec_powlaw_tbabs_all_obsids.png](default_output/spec_powlaw_tbabs_all_obsids.png)
    * This plots the Galactic absorbed powerlaw spectral points for all ObsIDs. This is one check for variability. The user can edit the code to plot a different model.

---

# Why use the online tools?
<details>
<summary>Why use the online tools?</summary>

Use the online tools for **point sources**.

swifthelp@leicester.ac.uk highly recommends using the [Build Swift-XRT products website](https://www.swift.ac.uk/user_objects/) when analysing point sources.
Their reasoning, taken from emails from swifthelp@leicester.ac.uk to mspletts@ucsc.edu in 2023-2024:
> "The reason I updated our online threads to suggest using the online tool is partly that almost everyone who uses it find it saves so much time and effort - and even now, after it's been available for so long, a good few people emailing the helpdesk have still not actually stumbled across it! It's also more accurate than the "quick and easy" by-hand method we go through in the threads if you have data from multiple observations combined together. The tool checks for pile-up on a much finer time scale than humans would usually bother to do, re-centroids the extraction region for each snapshot, and accurately count-weighting ARFs, rather than just creating a mean one as our threads explain how to do, for example. None of these differences are huge on their own (the methods should typically agree well within the errors), but over all computers are usually more accurate for things like this."

> "the online tools do everything (pile-up, bad column corrections, etc) - they're used by the Swift team all the time. As long as you're working with point sources, rather than large extended ones, the online tools are almost always the easiest and best way!"

> "Anyway, the apparent positionin the XRT frame can certainly change a bit between observations; in fact, within the online product generator, by default the algorithm centroids on the source in each individual snapshot (ie continuous pointing) where there are at least 40 source counts when building spectra or light-curves. This is one of the many reasons why we recommend using the product generator, since it does these things more accurately than the typical human would care to do! I don't know what you're doing with your data, so I can't really advise much further at the moment. However, you should ensure that the extraction region is well-centred on the source in any observation you are using (or just use the product generator!)."

> "are you aware of our online product generator at https://www.swift.ac.uk/user_objects/ ? The spectra that builds will always be already binned to 1 count per bin, and automatically fitted with C-statistics."
</details>

---

# SED modeling
You will need to deabsorb the SED points for use with Bjet_MCMC. You can use [nHDeabsorb](https://github.com/spletts/nHDeabsorb/)


# TODO
* Averaging X-ray data: ... make `src/average_data.py`. This requires [nHDeabsorb](https://github.com/spletts/nHDeabsorb/)
* PyXspec users could probably write one script that groups all this together?
    * Make it possible to run the package from anywhere? Might require the above bullet point so everything is in Python?


# Acknowledgements

Craig A. Gordon from the XSpec help desk provided instructions to isolate the absorption component. He also wrote a sample tcl script (via email exchange) to write values to data tables within XSpec.