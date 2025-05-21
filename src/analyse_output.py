"""Tools for analysing the output of this workflow: XSpec-produced spectra and model fits.
If no changes were made to the XSpec bash scripts, they were saved with basenames:
    spec_default_bin.dat
    stat_tbl.dat
    param_tbl.dat
This script compares different models tested in XSpec by making SEDs and lightcurves with the various models.
The lightcurve is made with one point per ObsID using the integral flux from the ObsID's SED.
It seems somewhat specific to the type of comparisons a user may wish to do, so it is separated from read_output.py
"""


import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import itertools
import numpy as np
import re
from astropy.time import Time
from astropy.table import Table
import argparse
import os
import glob
import logging

import read_output
import utils

import matplotlib as mpl
mpl.rcParams['axes.formatter.useoffset'] = False


# These must match the directory names specified in xspec_models/*sh
MODELS = ["powlaw_tbabs", "logpar_tbabs", "powlaw_ztbabs_tbabs"]

# This is for plot legends e.g. Galactic absorbed powerlaw will display instead of powlaw_tbabs
MODELS_PLOT_DICT = {
                    "powlaw_tbabs": "Galactic absorbed powerlaw",
                    "logpar_tbabs": "Galactic absorbed logparabola",
                    "powlaw_ztbabs_tbabs": "Galactic + intrinsic absorbed powerlaw",
                    }

# These error messages are directly from the XSpec Users’ Guide for version 12.12.1: Section 5.3.12 tclout
ERR_STR_DICT = {
                0: "new minimum found",
                1: "non-monotonicity detected",
                2:" minimization may have run into problem",
                3:"hit hard lower limit",
                4:"hit hard upper limit",
                5: "parameter was frozen",
                6: "search failed in -ve direction",
                7: "search failed in +ve direction",
                8: "reduced chi-squared too high",
                }


def check_fit_success_using_error_string(fn_param):
    """Check for errors XSpec's calculation of any parameters.
    Some fits may have failed according to the error string, but files (e.g. spectra) were still written.
    
    Parameters
    ----------
    fn_param : str
        Path to param_tbl.dat created by the bash files in xspec_models/
        e.g. ../output/00032646038/USERPROD_223833/powlaw_tbabs/param_tbl.dat

    Returns
    -------
    total_fit_succes : bool
        True if there were no errors in the calculation of any of the parameters in `fn_param`
        False if there is one or more error(s); details are logged and also printed to terminal
    """

    # This is the error string if there were NO errors in the parameter calculation 
    fit_success_msg = 'FFFFFFFFF'

    # True for elements/parameters where there is no error
    fit_succes = []

    # Get the error strings for each parameter in `fn_param` (parameters depend on the model)
    param_names, _, _, _, err_strs = read_output.read_param_tbl(fn_param)
    
    # Loop over multiple parameters
    for i, err_str in enumerate(err_strs):
        # 0 is a placeholder for quantities with no error strings e.g. flux
        if fit_success_msg in err_str or '0' in err_str:
            fit_succes.append(True)
        else:
            fit_succes.append(False)

    # If everything has no errors, return True
    if np.all(fit_succes):
        total_fit_succes = True
    if False in fit_succes:
        total_fit_succes = False

    # If there were errors, get more details
    if total_fit_succes is False or total_fit_succes == False:
        idx = np.where(total_fit_succes is False)[0]
        msg1 = f"There is an issue in the calculation of the parameter(s) error: {param_names[idx]} in {fn_param}."
        print(msg1)
        logging.warning(msg1)
        msg2 = "HOWEVER, the parameter may still have a reported best fit value and bounds. Consider refitting or treat these values carefully?"
        print(msg2)
        logging.warning(msg2)
        for i in idx:
            # Find all occurrences of 'T' 
            t_idx = [match.start() for match in re.finditer('T', err_strs[i])]
            for t in t_idx:
                msg = f"\tFor parameter {param_names[i]}, the fit failed because: {ERR_STR_DICT[t]}"
                print(msg)
                logging.error(msg)

    return total_fit_succes


def overplot_all_obsids_for_model(base_data_dir, obsid_list, spec_stem, model):
    """Plot data points (which are model dependent) of ObsIDs in `obsid_list` for one `model` on the same plot.
    Plot is saved as `base_data_dir`/spec_`model`_all_obsids.png
    This is done as one check of variability.

    Parameters
    ----------
    base_data_dir : str
        `BASE_DATA_DIR` as set in the config file.
    obsid_list : list[int]
        List of all ObsIDs to be plotted
    model : str
        This can be any of the elements in `MODELS`:
        MODELS = ["powlaw_tbabs", "logpar_tbabs", "powlaw_ztbabs_tbabs"]
    """

    # Global SED plot parameters
    plt.rcParams.update(
        {'font.size': 18, 'figure.figsize': (14, 10), 'axes.grid.which': 'both',
            'grid.color': 'lightgrey', 'grid.linestyle': 'dotted', 'axes.grid': True, 'axes.labelsize': 18,
            'legend.fontsize': 11})
    plt.style.use('tableau-colorblind10')
    marker_cycle = itertools.cycle(['o', '^', 's', 'D', '*', 'v', 'p', 'x'])

    plt.figure()

    for obsid in obsid_list:

        # Get name of file that contains the spectrum
        spec_dir = os.path.join(base_data_dir, obsid, "USERPROD*", spec_stem, model, "spec_default_bin.dat")
        spec_fn = glob.glob(spec_dir)

        # There is expected to be only one file in the lsit `spec_fn`. Check that this is the case. Proceed only if it is.
        if len(spec_fn) != 1:
            msg = f"Error with {spec_fn} attempting to glob {spec_dir} for spec_default_bin.dat. Expected one file from glob search but there are many or 0. Skipping this file." 
            print(msg)
            logging.warning(msg)
        else:
            energy, energy_half_bin_width, eflux, eflux_err, mdl_eflux = read_output.read_tcloutr_spec_data(spec_fn[0])
            plt.errorbar(energy, eflux, yerr=eflux_err, xerr=energy_half_bin_width, markerfacecolor="none", ls=" ", capsize=5, marker=next(marker_cycle), alpha=0.5,
                        label=f"ObsID {obsid}")
    plt.title(MODELS_PLOT_DICT[model])
    plt.xlabel("Energy [keV]")
    plt.ylabel(r"Flux(2-10 keV) [keV/cm$^2$/s]")
    plt.loglog()
    plt.legend()
    plot_path = os.path.join(base_data_dir, f"spec_{model}_all_obsids.png")
    plt.savefig(plot_path)
    msg = f"Wrote {plot_path}"
    print(msg)
    logging.info(msg)

    return None


def lightcurve_tbl(base_data_dir, fn_tbl):
    """Write lightcurve info to astropy Table saved as comma-separated file named `base_data_dir`/`fn_tbl`.
    The file has explicit header: mjd,flux,flux_errn,flux_errp,model
    The lightcurve is made with one point per ObsID using the integral flux from the ObsID's SED.
    This function will recursively search for *all* parameter files (param_tbl.dat) within `base_data_dir` that also include a subdirectory /USERPROD*/.

    Returns
    -------
    The astropy Table object with lightcurve data, so it is ready for plotting
    """

    # Dict to store all data to be saved to table `fn_tbl`
    data = {}

    # Array/list to save all data to
    flux_arr, flux_errn_arr, flux_errp_arr, mjd_arr, models = [], [], [], [], []

    # Find all instances where param_tbl.dat could be written
    # This will of course not include cases where the fit failed such that this file could not be written for certain models. This may happen in some cases
    files = glob.glob(f"{base_data_dir}/**/USERPROD*/**/param_tbl.dat", recursive=True)
    for f in files:
        # Photon flux
        flux, flux_errn, flux_errp = read_output.get_integral_phflux(f)
        flux_arr.append(flux)
        flux_errn_arr.append(flux_errn)
        flux_errp_arr.append(flux_errp)
        # ../output/00032646038/USERPROD_223833/powlaw_tbabs/param_tbl.dat -> ../output/00032646038/USERPROD_223833/
        pi_dir = os.path.dirname(os.path.dirname(f))
        # This is expected to be a one-element list ... TODO add check of this?
        fn_pi = glob.glob(f"{pi_dir}/*source.pi")[0]
        mjd = utils.get_observation_start_date(fn_pi)
        mjd_arr.append(mjd)
        # ../output/00032646038/USERPROD_223833/powlaw_ztbabs_tbabs/param_tbl.dat -> powlaw_ztbabs_tbabs
        models.append(os.path.basename(os.path.dirname(f)))

    data["mjd"] = mjd_arr
    data["flux"] = flux_arr
    data["flux_errn"] = flux_errn_arr
    data["flux_errp"] = flux_errp_arr
    data["model"] = models

    # Create table so user can plot it however they want
    t = Table(data)
    t.write(os.path.join(base_data_dir, fn_tbl), format='csv', overwrite=True) 
    msg = f"Wrote {os.path.join(base_data_dir, fn_tbl)}"
    print(msg)
    logging.info(msg)

    return t


def overplot_all_models_for_obsid(base_data_dir, obsid, spec_stem, model_list):
    """Plot data points of all models in `model_list` for one ObsID `obsid` on the same plot. 
    Plot is saved as `base_data_dir`/spec_all_models_`obsid`.png
    The chi-squared and degrees of freedom for each model are included in the plot legend.
    This is to check how much of an impact, if any, the choice of model has on the unfolded spectral points (`ufspec` in XSpec).
    This function will recursively search for *all* parameter files (param_tbl.dat) within `base_data_dir` that also include a subdirectory /USERPROD*/.
    """

    # Global SED plot parameters
    plt.rcParams.update(
        {'font.size': 18, 'figure.figsize': (14, 10), 'axes.grid.which': 'both',
            'grid.color': 'lightgrey', 'grid.linestyle': 'dotted', 'axes.grid': True, 'axes.labelsize': 18,
            'legend.fontsize': 11})
    plt.style.use('tableau-colorblind10')
    marker_cycle = itertools.cycle(['o', '^', 's', 'D', '*', 'v', 'p', 'x'])

    plt.figure()

    for model in model_list:
        
        spec_dir = os.path.join(base_data_dir, obsid, "USERPROD*", spec_stem, model, "spec_default_bin.dat")
        # This is expected to be a one-element list
        spec_fn = glob.glob(spec_dir)

        if len(spec_fn) != 1:
            msg = f"Error with {spec_fn} attempting to glob {spec_dir} for spec_default_bin.dat. Expected one file from glob search but there are many or 0. Skipping this." 
            print(msg)
            logging.error(msg)
        else:

            # Check that the XSpec fit encountered no issues
            param_fn = spec_fn[0].replace("spec_default_bin", "param_tbl")
            if os.path.exists(param_fn):
                total_fit_success = check_fit_success_using_error_string(param_fn)
            else:
                msg = f"No parameter file could be written. Looking for {param_fn}"
                print(msg)
                logging.warning(msg)
            
            # Get statistics to add to plot legend. If this file could not be written (for what reason?) then the plot is made with out the statistics info in the legend
            stat_fn = spec_fn[0].replace("spec_default_bin", "stat_tbl")
            if os.path.exists(stat_fn):
                chi_sq, dof, null_hyp_probability = read_output.read_stat_tbl(stat_fn)
            else:
                msg = f"No statistics file could be written. Looking for {stat_fn}"
                print(msg)
                logging.warning(msg)
                chi_sq, dof, null_hyp_probability  = None, None, None
            
            # Read data for plot
            energy, energy_half_bin_width, eflux, eflux_err, mdl_eflux = read_output.read_tcloutr_spec_data(spec_fn[0])
            plt.errorbar(energy, eflux, yerr=eflux_err, xerr=energy_half_bin_width, markerfacecolor="none", ls=" ", capsize=5, marker=next(marker_cycle),  alpha=0.5,
                        label=rf"{MODELS_PLOT_DICT[model]}; $\chi^2_r$={round(chi_sq, 2)}/{dof}={round(chi_sq/dof, 2)}")
    
    plt.title(f"ObsID {obsid}")
    plt.xlabel("Energy [keV]")
    plt.ylabel(r"Flux [keV/cm$^2$/s]")
    plt.loglog()
    plt.legend()
    plot_path = os.path.join(base_data_dir, f"spec_all_models_{obsid}.png")
    plt.savefig(plot_path)
    msg = f"Wrote {plot_path}"
    print(msg)
    logging.info(msg)

    return None


def lightcurve_plt(base_data_dir, fn_plot="lightcurve_phflux.png", fn_tbl="lightcurve.csv", models=["powlaw_tbabs", "logpar_tbabs", "powlaw_ztbabs_tbabs"]):
    """First make a table of lightcurve values save to `base_data_dir`/`fn_tbl`.
    Then plot this lightcurve using fluxes from all models in `models` (this can be a one-element list), and save it to `base_data_dir`/`fn_plot`.
    The lightcurve is made with one point per ObsID using the integral flux from the ObsID's SED.
    """

    # Keep colors and markers consistent throughout loop
    color_marker_dict = {
        "powlaw_tbabs": ["tab:blue", "s"],
        "logpar_tbabs": ["tab:orange", "o"],
        "powlaw_ztbabs_tbabs": ["tab:green", "d"],
        }

        # Global lightcurve plot parameters
    plt.rcParams.update(
        {'font.size': 18, 'figure.figsize': (16, 8), 'axes.grid.which': 'both',
            'grid.color': 'lightgrey', 'grid.linestyle': 'dotted', 'axes.grid': True, 'axes.labelsize': 18,
            'legend.fontsize': 11})
    plt.style.use('tableau-colorblind10')

    t = lightcurve_tbl(base_data_dir, fn_tbl)

    fig, ax1 = plt.subplots()
    # Make a plot separating out the different models
    for m in models:
        mask_t = t[t["model"] == m]
        ax1.errorbar(mask_t["mjd"], mask_t["flux"], yerr=[mask_t["flux_errp"], mask_t["flux_errn"]], color=color_marker_dict[m][0], marker=color_marker_dict[m][1], capsize=4, markerfacecolor="none",  alpha=0.5,
            label=MODELS_PLOT_DICT[m], ls=" ")


    # Put year at the top of the horizontal axis
    ax2 = ax1.secondary_xaxis('top', functions=(mjd_to_year, year_to_mjd))

    ax1.set_xlabel('MJD')
    ax1.set_ylabel(r'Photon flux [ph/cm$^2$/s]')
    plt.legend()
    plt.savefig(os.path.join(base_data_dir, fn_plot))
    msg = f"Wrote {os.path.join(base_data_dir, fn_plot)}"
    print(msg)
    logging.info(msg)

    return None


def mjd_to_year(t):
    return Time(t, format='mjd').decimalyear


def year_to_mjd(t):
    return Time(t, format='decimalyear').mjd


if __name__ == "__main__":
    # There is one command line argument: the name of the config file
    parser = argparse.ArgumentParser(description="Downloads XRT data products by querying the online tool, and reading user-made config file.")
    # *Optional* argument with default
    parser.add_argument(
        "--cfg_fn", type=str, default="default_config.cfg", help="Config filename formatted as in the default; see that file for example.")
    args = parser.parse_args()
    cfg_filename = args.cfg_fn

    oids, email, base_data_dir, spec_stem, targ_name = utils.load_cfg(cfg_filename)

    logging.basicConfig(filename=os.path.join(base_data_dir, "_analyse_output.log"),
                        level=logging.INFO,
                        format='%(levelname)s - %(funcName)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                        )

    lightcurve_plt(base_data_dir)
    overplot_all_obsids_for_model(base_data_dir, oids, spec_stem, "powlaw_tbabs")
    for obsid in oids:
        overplot_all_models_for_obsid(base_data_dir, obsid, spec_stem, MODELS)
        