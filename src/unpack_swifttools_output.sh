# Unzip and untar output of swifttools product generator

# One and only command line argument is the config filename
CFG_FN=$1

source ${CFG_FN}

# Read ObsIDS as array, not string
read -a OID_ARRAY <<< "$OIDS"

echo "All ObsIDs:" ${OID_ARRAY[@]}

# Unzip and untar
for oid in ${OID_ARRAY[@]}
	do
	for bdir in ${BASE_DATA_DIR}
		do
			# Unzip with destination folder set by -d
			# -n will SKIP files already extracted
			unzip -n ${BASE_DATA_DIR}/${oid}/${SPEC_STEM}.zip -d ${BASE_DATA_DIR}/${oid}

			# Then untar and extract in folder set by -C
			# SKIP files already extracted
			tar -xvf ${BASE_DATA_DIR}/${oid}/USERPROD*/${SPEC_STEM}/*tar.gz --skip-old-files -C ${BASE_DATA_DIR}/${oid}/USERPROD*/${SPEC_STEM}

		done
	done
