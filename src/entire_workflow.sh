# Entire XRT workflow in one script. User must create config file `CFG_FN` first.

# One and only command line argument is the config filename
CFG_FN=$1

# Get data products
python3 swifttools_ana.py --cfg_fn ${CFG_FN}

# Unzip and untar data products
./unpack_swifttools_output.sh ${CFG_FN}

# Get exposure time of each observation
python3 utils.py --cfg_fn ${CFG_FN}

# Use grappha to re-group the data for chi-squared statistics. YOU NEED TO KNOW THE MODE (PC or WT) for each ObsID; this info is in the filenames.
# If there is more than one mode per ObsID, you need to set the mode by hand
./run_grppha.sh ${CFG_FN}

# XSpec to fit the data to multiple models
./xspec_models/powlaw_tbabs.sh ${CFG_FN}
./xspec_models/powlaw_ztbabs_tbabs.sh ${CFG_FN}
./xspec_models/logpar_tbabs.sh ${CFG_FN}

# Compare the tested models
python3 analyse_output.py --cfg_fn ${CFG_FN}
