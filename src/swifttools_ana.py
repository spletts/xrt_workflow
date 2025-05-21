# Download Swift-XRT data products. This script is largely copied from the documentation at https://www.swift.ac.uk/user_objects/API/
# requires Python 3


import swifttools.ukssdc.xrt_prods as ux
import time
import os
import argparse

import utils


def submit_request_for_oid(oid, email, base_data_dir, spec_stem, targ_name, clobber=False):
    """Query data products for ObsID `oid`.
    See here for the data product options: https://www.swift.ac.uk/user_objects/API/RequestJob.md#global-parameters
    As is, this downloads a spectrum for `oid` only.

    Parameters
    ----------
    oid : str
        One ObsID. Cannot be a float due to how Python 3.6 handles numbers that start with 00...
    email : str
        Updates regarding the product download will be sent to this email
    base_data_dir : str
        Data will be downloaded in a folder with name {base_data_dir}/{oid}/{spec_stem}.zip
    targ_name : str
        Name of the source observed in `oid`
    clobber : bool
        If True, overwrites any already existing downloaded products

    Returns
    -------
    None. But data products are downloaded in `base_data_dir`.
    """

    # Make directories (including subdirectories if necessary) for downloaded data if it does not exist already
    data_dir = f'{base_data_dir}/{oid}'
    os.makedirs(data_dir, exist_ok=True)

    # Create an XRTProductRequest object
    myReq = ux.XRTProductRequest(email, silent=False)

    # Set the global parameters
    # See here for the options https://www.swift.ac.uk/user_objects/API/RequestJob.md#global-parameters
    myReq.setGlobalPars(name=targ_name, targ=oid, getCoords=True, centroid=True,
                        # the default is 1 on https://www.swift.ac.uk/user_objects/
                        posErr=1,
                        useSXPS=False,
                        notify=True)

    # Get SED per ObsID
    myReq.addSpectrum(hasRedshift=False, whichData='user', specStem=spec_stem, useObs=oid, timeslice='obsid',
                      doNotFit=True)
    # Submit the job - note, this can fail so we ought to check the return code in real life
    myReq.submit()
    # Check for errors
    try:
        print(myReq.submitError)
    except RuntimeError: 
        # RuntimeError: There is no submitError unless request submission failed, which it didn't:
        pass

    # Now wait until it's complete
    done = myReq.complete
    while not done:
        time.sleep(60)
        done = myReq.complete

    # And download the products
    myReq.downloadProducts(data_dir, format='zip', clobber=clobber)

    return None


if __name__ == "__main__":
    # There is one command line argument: the name of the config file
    parser = argparse.ArgumentParser(description="Downloads XRT data products by querying the online tool, and reading user-made config file.")
    # *Optional* argument with default
    parser.add_argument(
        "--cfg_fn", type=str, default="default_config.cfg", help="Config filename formatted as in the default; see that file for example.")
    args = parser.parse_args()
    cfg_filename = args.cfg_fn

    oids, email, base_data_dir, spec_stem, targ_name = utils.load_cfg(cfg_filename) 

    for obsid in oids:
        submit_request_for_oid(obsid, email, base_data_dir, spec_stem, targ_name)
