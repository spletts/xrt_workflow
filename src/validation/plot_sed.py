import numpy as np
import matplotlib.pyplot as plt
from astropy.table import Table
import astropy.units as u
import pandas as pd
from nHDeabsorb import get_absorption
from dataclasses import dataclass
from math import isnan


FN_AGNPY_SED = '/home/vhep/mspletts/.conda/pkgs/agnpy-0.4.0-pyhd8ed1ab_0/site-packages/agnpy/data/mwl_seds/Mrk421_2011.ecsv'
# FN_SED = '/home/vhep/mspletts/swift_xrt/xrt_workflow/src/validation/output/USERPROD_233124/spec/logpar_tbabs/spec_default_bin.dat'
FN_SED = '/home/vhep/mspletts/swift_xrt/xrt_workflow/src/validation/output/USERPROD_233124/spec/logpar_phabs/spec_default_bin.dat'
FN_SED_BINNED = '/home/vhep/mspletts/swift_xrt/xrt_workflow/src/validation/output/USERPROD_233124/spec/logpar_phabs/spec_binned.dat'


def xspec_log10par(energy, norm, idx, beta):
    """XSpec log parabola is base 10"""
    return norm * np.power(energy, -(idx+beta*np.log10(energy)))


@dataclass
class Abdo2011Params:
    """Mkn421 parameters from A. A. Abdo et al 2011 ApJ 736 131"""
    norm, norm_err = 1.839 * 10**-1, 0.002*10**-1  # ph.cm/s/keV
    idx, idx_err =  2.178, 0.002
    beta, beta_err = 0.391, 0.004


def read_abdo_agnpy_xrt_sed(sed_path):
    """Get Swift-XRT data from A. A. Abdo et al 2011 ApJ 736 131.
    The data is provided as part of agnpy at `sed_path`
     
    Return the values in units of keV and keV/cm^2/s
    """
    
    table = Table.read(sed_path)
    table = table.group_by("instrument")
    table = table[table['instrument'] == "Swift/XRT"]
    energy = table['e_ref']  # eV
    energy = u.eV.to(u.keV, energy)    
    # for the `read_builtin` the default for alpha_norm is 1
    intr_flux = table['e2dnde']  # erg / (cm2 s)
    intr_flux_errn = table['e2dnde_errn']  # erg / (cm2 s)
    intr_flux_errp = table['e2dnde_errp']  # erg / (cm2 s)
    intr_flux, intr_flux_errn, intr_flux_errp = u.erg.to(u.keV, [intr_flux, intr_flux_errn, intr_flux_errp])

    print("If 0, error is symmetric", intr_flux_errn - intr_flux_errp)

    return energy, intr_flux, intr_flux_errn, intr_flux_errp


def read_tcloutr_spec_data(fn_sed):
    """Get Swift-XRT data from analysis in this repo"""  

    dat = pd.read_csv(fn_sed, header=None, delimiter=' ')
    # In keV
    energy = dat.iloc[:, 0].to_numpy()
    energy_half_bin_width = dat.iloc[:, 1].to_numpy()
    # This is an energy flux (in keV/cm^2/s) if `eeufspec` was used to write this file
    eflux = dat.iloc[:, 2].to_numpy()
    eflux_err = dat.iloc[:, 3].to_numpy()
    mdl_eflux = dat.iloc[:, 4].to_numpy()

    return energy, energy_half_bin_width, eflux, eflux_err, mdl_eflux


def ln_avg(emin, emax):
    avg = (emax-emin)/(np.log(emax) - np.log(emin))
    print(f"Log average of {emin}, {emax}: {avg}")
    if avg is np.nan or avg == np.nan or isnan(avg):
        # Log average of 1.394999981, 1.394999981: nan
        avg = emin
    return avg


def sed_plots(fn_agnpy, fn_workflow, fn_workflow_default_bins):
    plt.rcParams.update(
    {'font.size': 16, 'figure.figsize': (10, 8), 'axes.grid.which': 'both',
        'grid.color': 'gainsboro', 'grid.linestyle': 'dotted', 'axes.grid': True, 'axes.labelsize': 16,
        'legend.fontsize': 12})

    # From workflow; observed fluxes
    alphas = [0.2, 1]
    labels = ["", "rebinned"]
    for i, fn in enumerate([fn_workflow_default_bins, fn_workflow]):
        wf_energy, wf_energy_half_bin_width, wf_eflux, wf_eflux_err, wf_mdl_eflux = read_tcloutr_spec_data(fn)
        absorb = get_absorption.xspec_absorption_component(wf_energy - wf_energy_half_bin_width, wf_energy + wf_energy_half_bin_width, "tbabs_abund_wilm", True, 0.0161)
        #print(f"xrt_workflow xerr: {energy_half_bin_width}")
        # Intrinsic fluxes
        plt.errorbar(wf_energy, wf_eflux/absorb, wf_eflux_err/absorb, xerr=wf_energy_half_bin_width, label=f"xrt_workflow {labels[i]}", ls=' ', marker='d', alpha=alphas[i])
    
    energy, intr_flux, intr_flux_errn, intr_flux_errp = read_abdo_agnpy_xrt_sed(fn_agnpy)
    plt.errorbar(energy, intr_flux, yerr=intr_flux_errn, label="Abdo et al 2011", ls=" ", marker='.', color="k")

    energy_arr = np.logspace(np.log10(min(energy)), np.log10(max(energy)))
    plt.plot(energy_arr, energy_arr**2*xspec_log10par(energy_arr, Abdo2011Params.norm, Abdo2011Params.idx, Abdo2011Params.beta), color="k", 
             label="Abdo et al 2011 best fit")

    plt.ylabel(r'Intrinsic energy flux [keV/cm$^2$/s]')
    plt.loglog()
    plt.legend()
    plt.savefig("sed.png")
    plt.ylim([1e-2, 3e-1])
    plt.savefig("sed_ylims.png")
    

sed_plots(FN_AGNPY_SED, FN_SED_BINNED, FN_SED)
