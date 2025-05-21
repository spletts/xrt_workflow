"""
Various utilities for the workflow, regarding the output of the swifftools product generator; reading the outputs/inputs prior to use of XSpec).
e.g. guidance for which mode PC/WT to use, reading the config (.cfg) file with Python, read observation date from spectra (.pi)
TODO this script is a random assortment of things.. organize better
"""


from astropy.io import fits
import glob
import argparse
import os
from astropy.time import Time
import logging


def get_livetime_from_spec(fn_pi):
    """Get deadtime corrected livetime in seconds.

    Parameters
    ----------
    fn_pi : str
        Name of spectrum output by swifttools
        e.g. Obs_00032646039pc.pi, Obs_00032646038wtsource.pi, Obs_00032646038wtback.pi
        Could also use Obs_00032646038wt_chi2_grp.pi (not created by swifttools, but created in this package)

    Returns
    -------
    Deadtime corrected livetime in seconds
    """

    hdul = fits.open(fn_pi)
    livetime_sec = hdul[0].header["LIVETIME"]

    return float(livetime_sec)


def get_observation_start_date(fn_pi):
    """Get deadtime corrected livetime in seconds.

    Parameters
    ----------
    fn_pi : str
        Name of spectrum output by swifttools
        e.g. Obs_00032646039pc.pi, Obs_00032646038wtsource.pi, Obs_00032646038wtback.pi
        Could also use Obs_00032646038wt_chi2_grp.pi (not created by swifttools, but created in this package)

    Returns
    -------
    Deadtime corrected livetime in seconds
    """

    hdul = fits.open(fn_pi)
    # YYYY-MM-DDThh:mm:ss
    date_isot = hdul[0].header["DATE-OBS"]
    t = Time(date_isot, format='isot')

    return t.mjd


def load_cfg(filename):
    """Read config file `filename` formatted as e.g. src/config_example.cfg
    Return config file contents.
    
    Returns
    -------
    oid : list[str]
    email, base_data_dir, spec_stem, targ_name : str
        Define in config_example.cfg 
    """

    variables = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()

            # Skip comments or empty lines
            if not line or line.startswith('#'):
                continue

            # Find variable declaration
            if '=' in line:
                key, value = map(str.strip, line.split('=', 1))
                # Remove surrounding quotes
                value = value.strip('"').strip("'")
                # Store as list if contains space
                if ' ' in value:
                    value = value.split()
                variables[key] = value

    oids = variables["OIDS"]
    # Make this a one-element list if there is only one ObsID, because `oids` is looped over later
    if type(oids) is str:
        oids = [oids]
    email = variables["EMAIL"]
    base_data_dir = variables["BASE_DATA_DIR"]
    spec_stem = variables["SPEC_STEM"]
    targ_name = variables["SOURCE_NAME"]

    return oids, email, base_data_dir, spec_stem, targ_name


def get_mode(base_data_dir, obsid, spec_stem, modes=("pc", "wt")):
    """Determine which mode to use, PC or WT, if there are observations for both for one ObsID `oid`.
    If there are both PC and WT observations, typically XRT started in one mode and switched to the other due to the count rate.
    So, use the longer observation. In my experience the shorter observation is VERY short, < 20 seconds.
    """

    livetimes = {}
    for m in modes:
        pi_dir = os.path.join(base_data_dir, obsid, "USERPROD*", spec_stem, f"*{m}source.pi")
        pi_fn = glob.glob(pi_dir)
        # Check if list is empty
        if len(pi_fn) == 0:
            msg = f"ObsID {obsid} does not have a {m} observation, looking in directory {pi_dir}"
            print(msg)
            # TODO add logger
        else:
            # This is expected to be a one element list
            livetimes[m] = get_livetime_from_spec(pi_fn[0])

    msg = f"Mode and livetime (sec): {livetimes}. If observations were conducted in both modes, use the larger livetime.\n"
    print(msg)
    logging.info(msg)

    # TODO how to connect this part of the workflow with the rest?
    
    return livetimes



if __name__ == "__main__":
    # There is one command line argument: the name of the config file
    parser = argparse.ArgumentParser(description="Various utils")
    # *Optional* argument with default
    parser.add_argument(
        "--cfg_fn", type=str, default="default_config.cfg", help="Config filename formatted as in the default; see that file for example.")
    args = parser.parse_args()
    cfg_filename = args.cfg_fn

    oids, email, base_data_dir, spec_stem, targ_name = load_cfg(cfg_filename)

    logging.basicConfig(filename=os.path.join(base_data_dir, "_mode_obs_times.log"),
                    level=logging.INFO,
                    format='%(levelname)s - %(funcName)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )
    
    for obsid in oids:
        get_mode(base_data_dir, obsid, spec_stem)
