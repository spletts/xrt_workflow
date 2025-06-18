# Unzip and untar output of swifttools product generator

# One and only command line argument is the config filename
CFG_FN=$1
source ${CFG_FN}
echo "All ObsIDs:" ${OID_ARRAY[@]}

# Unzip and untar
# Unzip with destination folder set by -d
# -n will SKIP files already extracted
unzip -n ${BASE_DATA_DIR}/${SPEC_STEM}.zip -d ${BASE_DATA_DIR}/${oid}
# Then untar and extract in folder set by -C
# SKIP files already extracted
tar -xvf ${BASE_DATA_DIR}/USERPROD*/${SPEC_STEM}/*tar.gz --skip-old-files -C ${BASE_DATA_DIR}/USERPROD*/${SPEC_STEM}
