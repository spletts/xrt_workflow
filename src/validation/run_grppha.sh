#!/bin/bash
#  Run 'grppha' to create grouped spectrum `CHI2_GRP_SPEC` for chi-squared statistics with a minimum of 20 counts per bin. 
# Overwrite grouped spectrum if it already exists.


# One and only command line argument is the config filename
CFG_FN=$1

source ${CFG_FN}
read -a MODE_ARRAY <<< "$MODES"
mode=${MODE_ARRAY[0]}

# Read as arrays, not string. OIDS and MODES defined in CFG_FN.

        # Isolate USERPROD* and the numbers that follow in the directory name. I don't know how these numbers are determined.
        base_ddir=`basename ${BASE_DATA_DIR}/USERPROD*`
        # Directory with downloaded data products
        DDIR=${BASE_DATA_DIR}/${base_ddir}/${SPEC_STEM}
		echo ${DDIR}
        ARF=${DDIR}/spec${mode}.arf
		echo ${ARF}
        BKG_SPEC=${DDIR}/spec${mode}back.pi
        # Grouped for C-stats: $"{DDIR}/Obs_${oid}${mode}.pi"
        RMF=${DDIR}/spec${mode}.rmf
        CHI2_GRP_SPEC=${DDIR}/spec${mode}_chi2_grp.pi
        SRC_SPEC=${DDIR}/spec${mode}source.pi

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
