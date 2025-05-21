"""
This script has functions for reading the out of this workflow: XSpec-produced spectra and model fits.
If no changes were made to the XSpec bash scripts, they were saved with basenames:
    spec_default_bin.dat
    stat_tbl.dat
    param_tbl.dat
"""


from astropy.table import Table
from dataclasses import dataclass
import sys
import os
import numpy as np


def read_tcloutr_spec_data(fn_sed):
    """Read data file `fn_sed` created by user in XSpec **using `tcloutr`** (not `wd`). This plot has an implicit header.
    The format of this file (order of the columns and so their meanings) is completely determined by the user.
    Check the XSpec commands that were issued to make sure this file is correctly read.

    Below is the relevant excerpt of the commands used to make `fn_sed`:
    `#XSPEC12>` set xDataEnergy [tcloutr plot eeufspec x] `#'xDataEnergy' is x-axis of eeufspec = energies in keV`
    `#XSPEC12>` set xDataEnergyErr [tcloutr plot eeufspec xerr] `#'xDataEnergy' is half bin width in keV`
    `#XSPEC12>` set yDataEFlux [tcloutr plot eeufspec y] `#'yDataEFlux' is y-axis of eeufspec = energy flux in keV/cm^2/s`
    `#XSPEC12>` set yDataEFluxErr [tcloutr plot eeufspec yerr] `#'$yDataEFluxErr' is error on energy flux in keV/cm^2/s`
    `#XSPEC12>` set modelDataEFlux [tcloutr plot eeufspec model] `#'$modelDataEFlux' is energy flux from the model in keV/cm^2/s`
    `#XSPEC12>` set unbinDataTable [open $UNBINNED_DATA_TBL w+] `#Prepare to write data to file`
    `#XSPEC12>` set len [llength \$xDataEnergy] `#'$xDataEnergy' is set within 'EOF ... EOF' so it needs to be preceded by '\'`
    `#XSPEC12>` for {set idx 0} {\$idx < \$len} {incr idx} {puts \$unbinDataTable "[lindex \$xDataEnergy \$idx] [lindex \$xDataEnergyErr \$idx] [lindex \$yDataEFlux \$idx] [lindex \$yDataEFluxErr \$idx] [lindex \$modelDataEFlux \$idx]" } `#Format file headers: energy (keV), energy half bin width, eflux (keV/cm^2/s), eflux_error, model_eflux`

    Parameters
    ----------
    fn_sed : str
        SED filename
        Ex - logpar_tbabs/spec_default_bin.dat, spec_binned.dat

    Returns
    -------
    energy : array_like[float]
        Energy in keV
    energy_half_bin_width : array_like[float]
        Half bin width of energy bin in keV
    eflux : array_like[float]
        Energy flux in keV/cm^2/s from unfolded spectrum (eeufspec)
    eflux_err : array_like[float]
        Energy flux error in keV/cm^2/s
    mdl_eflux : array_like[float]
        Energy flux in keV/cm^2/s from model e.g. logpar*tbabs
    """

    t = Table.read(fn_sed, format='ascii.no_header')
    # In keV
    energy = t[t.colnames[0]].data
    energy_half_bin_width = t[t.colnames[1]].data
    # This is an energy flux (in keV/cm^2/s) if `eeufspec` was used to write this file
    eflux = t[t.colnames[2]].data
    eflux_err = t[t.colnames[3]].data
    mdl_eflux = t[t.colnames[4]].data

    return energy, energy_half_bin_width, eflux, eflux_err, mdl_eflux
    

def read_param_tbl(fn_param):
    """Read parameter table param_tbl.dat.
    The format of this table depends on the model used in XSpec. The explicit header is
    name       param        param_low      param_high   error_string
    but the number of rows (i.e. the number of parameters and their names depends on the model used.)

    Parameters
    ----------
    fn_param : str
        e.g. param_tbl.dat

    Returns
    -------
    param_names : list[str]
        List of parameter names. 
        e.g. powerlaw_ztbabs_tbabs: ['ztbabs_nh', 'PhoIndex', 'norm', 'flux', 'cRate']
    params_low, params_high : list[float]
        The lower and upper values/bounds for the parameters
    err_str : list[str]
        Error strings reported by XSpec; one error string per parameter 
    """

    t = Table.read(fn_param, format='ascii')
    param_names = t[t.colnames[0]].data
    params = t[t.colnames[1]].data
    params_low = t[t.colnames[2]].data
    params_high = t[t.colnames[3]].data
    err_str = t[t.colnames[4]].data

    return param_names, params, params_low, params_high, err_str


def read_stat_tbl(fn_stats):
    """Read statistics table stat_tbl.dat.
    The explicit header is: chi_squared deg_freedom null_hyp_probability

    Parameters
    ----------
    fn_stats : str
        stat_tbl.dat

    Returns
    -------
    chi_sq : float
        Chi-squared
    dof : float
        Degrees of freedom
    null_hyp_probability : float
        Null hypothesis probability
    """

    t = Table.read(fn_stats, format='ascii')
    # First column: chi-sq. Get the 0th element, which is the only element. There is one row of data.
    chi_sq = t[0][0]
    # Second column: dof. Get the 0th element, which is the only element. There is one row of data.
    dof = t[0][1]
    null_hyp_probability = t[0][2]

    return chi_sq, dof, null_hyp_probability


def get_integral_phflux(fn_param):
    """Integral flux(2-10 keV) in units of ph/cm^2/s
    
    Returns
    -------
    flux : float
        Integral flux from 2-10 keV for some ObsID
    flux_errn : float
        Lower/negative error/uncertainty on `flux`
    flux_errp : float
        Upper/positive error/uncertainty on `flux`
    """
    # TODO ? add energy flux in erg/cm^2/s to the xspec bash script and then read it here
    param_names, params, params_low, params_high, _ = read_param_tbl(fn_param)
    # Index for flux
    i = -2
    if param_names[i] != "flux":
        sys.exit("Edit...") # TODO elaborate
    flux, flux_low, flux_high = params[i], params_low[i], params_high[i]
    flux_errn = flux - flux_low
    flux_errp = flux_high - flux

    return flux, flux_errn, flux_errp


def get_model_parameters(fn_param):
    # TODO Make is easier for user to read parameter table which is formatter row-wise ; 
    # this can be read with pandas easily but not easily in astropy

    # ../output/00032646038/USERPROD_223833/powlaw_ztbabs_tbabs/param_tbl.dat -> powlaw_ztbabs_tbabs
    model = os.path.basename(os.path.dirname(fn_param))
    param_names, params, params_low, params_high, _ = read_param_tbl(fn_param)

    # Reformat data in a more helpful way (?)
    data = {}

    if model == 'powlaw_tbabs':
        cls = PowlawTbabs
    elif model == 'logpar_tbabs':
        cls = LogparTbabs
    elif model == 'powlaw_ztbabs_tbabs':
        cls = PowlawZtbabsTbabs
    else:
        sys.exit(f"Unrecognized model {model}")
        # TODO add logger with function name etc

    param_names_index = cls().param_names_index
    # Names is the key, corresponding index is the value
    for i in list(param_names_index.values()):
        pname = list(param_names_index.keys())[i]
        j = np.where(param_names == pname)
        # Parameter value, lower bound, upper bound
        p, p_low, p_high = params[j], params_low[j], params_high[j]
        p_errn = p - p_low
        p_errp = p_high - p
    
        data[pname] = [p, p_errn, p_errp]
    # Create table to index a bit more easily
    t = Table(data)
    
    return t


@dataclass
class PowlawTbabs:
    """Store parameters from powlaw_tbabs.sh"""
    param_names_index = {
        "PhoIndex": 0,
        "norm" : 1
        }


@dataclass
class PowlawZtbabsTbabs:
    """Store parameters from powlaw_ztbabs_tbabs.sh"""
    param_names_index = {
                "ztbabs_nh" : 0,
                "PhoIndex": 1,
                "norm": 2,
                }


@dataclass
class LogparTbabs:
    """Store parameters from logpar_tbabs.sh"""
    param_names = {
                "alpha": 0, 
                "beta": 1, 
                "pivotE": 2, 
                "norm": 3
                }
