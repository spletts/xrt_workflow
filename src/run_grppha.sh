#!/bin/bash
#  Run 'grppha' to create grouped spectrum `CHI2_GRP_SPEC` for chi-squared statistics with a minimum of 20 counts per bin. 
# Overwrite grouped spectrum if it already exists.


# One and only command line argument is the config filename
CFG_FN=$1

source ${CFG_FN}

# Read as arrays, not string. OIDS and MODES defined in CFG_FN.
read -a OID_ARRAY <<< "$OIDS"
read -a MODE_ARRAY <<< "$MODES"

length=${#OID_ARRAY[@]}
for ((i=0; i<length; i++)); do
        oid=${OID_ARRAY[$i]}
        mode=${MODE_ARRAY[$i]}
        # Isolate USERPROD* and the numbers that follow in the directory name. I don't know how these numbers are determined.
        base_ddir=`basename ${BASE_DATA_DIR}/${oid}/USERPROD*`
        # Directory with downloaded data products
        DDIR=${BASE_DATA_DIR}/${oid}/${base_ddir}/${SPEC_STEM}
        ARF=${DDIR}/Obs_${oid}${mode}.arf
        BKG_SPEC=${DDIR}/Obs_${oid}${mode}back.pi
        # Grouped for C-stats: $"{DDIR}/Obs_${oid}${mode}.pi"
        RMF=${DDIR}/Obs_${oid}${mode}.rmf
        CHI2_GRP_SPEC=${DDIR}/Obs_${oid}${mode}_chi2_grp.pi
        SRC_SPEC=${DDIR}/Obs_${oid}${mode}source.pi

        # Group spectrum
        # '!' overwrites the file if it exists.
        # A blank line represents the Enter key
        # Format for below: `#{command prompt}>` command
        grppha << EOF > ${DDIR}/${LOG_GRPPHA}
        `#Please enter PHA filename` $SRC_SPEC
        `#Please enter output filename` !$CHI2_GRP_SPEC
        `#GRPPHA` chkey backfile $BKG_SPEC
        `#GRPPHA` chkey respfile $RMF
        `#GRPPHA` chkey ANCRFILE $ARF
        reset all
        `#GRPPHA` bad 0-29
        `#GRPPHA` group min 20
        `#GRPPHA` exit
EOF
echo "Logged to" ${DDIR}/${LOG_GRPPHA}
done
