#!/bin/bash


<<comment
Uses the model tbabs*ztbabs*powerlaw with:

Fixed TBabs:nH = $NH_TBABS (Milky Way absorption; $NH_TBABS set in config.sh)
Fixed zTBabs:Redshift = 0.45

FREE zTBabs:nH (intrinsic absorption, at the source)
FREE powerlaw:PhoIndex
FREE powerlaw:norm
comment

# One and only command line argument is the config filename
CFG_FN=$1

source ${CFG_FN}

# Read as array, not string. Variables defined in CFG_FN.
read -a OID_ARRAY <<< "$OIDS"
read -a MODE_ARRAY <<< "$MODES"

length=${#OID_ARRAY[@]}
for ((j=0; j<length; j++)); do

oid=${OID_ARRAY[$j]}
mode=${MODE_ARRAY[$j]}


# Isolate USERPROD* and the numbers that follow in the directory name. I don't know how these numbers are determined.
userprod_dir_name=`basename ${BASE_DATA_DIR}/${oid}/USERPROD*`
# Directory with downloaded data products
data_dir=${BASE_DATA_DIR}/${oid}/${userprod_dir_name}/${SPEC_STEM}
# Output for XSpec analysis
xspec_outdir=${data_dir}/powlaw_ztbabs_tbabs

# Check if directory exists. Make it if it doesn't
if [ ! -d ${xspec_outdir} ]; then
  # Directory doesn't exist
  mkdir ${xspec_outdir}
fi

# `CHI2_GRP_SPEC` name must match what was used in grppha
CHI2_GRP_SPEC=${data_dir}/Obs_${oid}${mode}_chi2_grp.pi

PARAM_TBL=${xspec_outdir}/param_tbl.dat
STAT_TBL=${xspec_outdir}/stat_tbl.dat
DATA_TBL=${xspec_outdir}/spec_binned.dat
UNBINNED_DATA_TBL=${xspec_outdir}/spec_default_bin.dat
RESID_PLT=${xspec_outdir}/resid.png
PHFLUX=${xspec_outdir}/phflux.png
EFLUX=${xspec_outdir}/eflux.png

# Move already existing data files so they can be re-written within XSpec.
# File will be overwritten if it already exist in 'TRASH_DIR'
for i in $DATA_TBL $UNBINNED_DATA_TBL $PARAM_TBL $STAT_TBL 
do
  if [ -e "$i" ]; then
      # File exists. Move it so it can be rewritten.
      # echo "$i" "->" "$TRASH_DIR"
      mv "$i" "$TRASH_DIR"
  fi
done

# Help with tcl commands supplied by Gordon, Craig A via the XSpec help desk email

# See powlaw_tbabs.sh for annotations next to the commands
xspec << EOF > ${xspec_outdir}/${LOG_XSPEC}
`#XSPEC12>` data $CHI2_GRP_SPEC
`#XSPEC12>` ignore bad 
`#XSPEC12>` ignore **-0.3
`#XSPEC12>` ignore 10.0-** 
`#XSPEC12>` cpd /xw 
`#XSPEC12>` setplot energy keV 
`#XSPEC12>` abund wilm 
`#XSPEC12>` model tbabs*ztbabs(powerlaw) 
`#1:TBabs:nH>` $NH_TBABS 
`#2:zTBabs:nH>`
`#3:zTBabs:Redshift>` $REDSHIFT
`#4:powerlaw:PhoIndex>` 
`#5:powerlaw:norm>` 
`#XSPEC12>` freeze 1 
`#XSPEC12>` freeze 3 
`#XSPEC12>` fit
`#XSPEC12>` save all $xspec_outdir/fit 

`#XSPEC12>` error 1. 2 
`#XSPEC12>` error 1. 4-5
`#XSPEC12>` flux 2 10 err
`#XSPEC12>` set parFlux [tcloutr flux] 
`#XSPEC12>` set parZnH [tcloutr param 2] 
`#XSPEC12>` set parZnHErr [tcloutr error 2] 
`#XSPEC12>` set parIndex [tcloutr param 4]
`#XSPEC12>` set parIndexErr [tcloutr error 4]
`#XSPEC12>` set parNorm [tcloutr param 5]
`#XSPEC12>` set parNormErr [tcloutr error 5]
`#XSPEC12>` set rateEtc [tcloutr rate all] 
`#XSPEC12>` set cRate [lindex \$rateEtc 0] 
`#XSPEC12>` set cRateErr [lindex \$rateEtc 1] 
`#XSPEC12>` set cRateLow [expr {\$cRate - \$cRateErr}] 
`#XSPEC12>` set cRateHigh [expr {\$cRate + \$cRateErr}] 
`#XSPEC12>` set paramTable [open $PARAM_TBL w+] 
`#XSPEC12>` puts \$paramTable "[lindex name 0] [lindex param 0] [lindex param_low 0] [lindex param_high 0] [lindex error_string 0]" 
`#XSPEC12>` puts \$paramTable "[lindex ztbabs_nh 0] [lindex \$parZnH 0] [lindex \$parZnHErr 0] [lindex \$parZnHErr 1] [lindex \$parZnHErr 2]"
`#XSPEC12>` puts \$paramTable "[lindex PhoIndex 0] [lindex \$parIndex 0] [lindex \$parIndexErr 0] [lindex \$parIndexErr 1] [lindex \$parIndexErr 2]" 
`#XSPEC12>` puts \$paramTable "[lindex norm 0] [lindex \$parNorm 0] [lindex \$parNormErr 0] [lindex \$parNormErr 1] [lindex \$parNormErr 2]" 
`#XSPEC12>` puts \$paramTable "[lindex flux 0] [lindex \$parFlux 3] [lindex \$parFlux 4] [lindex \$parFlux 5] [lindex 0 0]"
`#XSPEC12>` puts \$paramTable "[lindex cRate 0] [lindex \$cRate 0] [lindex \$cRateLow 0] [lindex \$cRateHigh 0] [lindex 0 0]"
`#XSPEC12>` close \$paramTable
`#XSPEC12>` set nullProb [tcloutr nullhyp] 
`#XSPEC12>` set chiSq [tcloutr stat] 
`#XSPEC12>` set dof [tcloutr dof] 
`#XSPEC12>` set statTable [open $STAT_TBL w+]
`#XSPEC12>` puts \$statTable "[lindex chi_squared 0] [lindex deg_freedom 0] [lindex null_hyp_probability 0]" 
`#XSPEC12>` puts \$statTable "[lindex \$chiSq 0] [lindex \$dof 0] [lindex \$nullProb 0]"
`#XSPEC12>` close \$statTable

`#XSPEC12>` plot res 
`#XSPEC12>` setplot command rescale 0.3 10 
`#XSPEC12>` iplot
`#PLT>` hard $RESID_PLT/png 
`#PLT>` clear
`#PLT>` q

`#XSPEC12>` plot eemodel eeufspec
`#XSPEC12>` setplot command rescale 0.3 10 
`#XSPEC12>` plot eemodel eeufspec 
`#XSPEC12>` set xDataEnergy [tcloutr plot eeufspec x] 
`#XSPEC12>` set xDataEnergyErr [tcloutr plot eeufspec xerr] 
`#XSPEC12>` set yDataEFlux [tcloutr plot eeufspec y] 
`#XSPEC12>` set yDataEFluxErr [tcloutr plot eeufspec yerr] 
`#XSPEC12>` set modelDataEFlux [tcloutr plot eeufspec model] 
`#XSPEC12>` set unbinDataTable [open $UNBINNED_DATA_TBL w+] 
`#XSPEC12>` set len [llength \$xDataEnergy] 
`#XSPEC12>` for {set idx 0} {\$idx < \$len} {incr idx} {puts \$unbinDataTable "[lindex \$xDataEnergy \$idx] [lindex \$xDataEnergyErr \$idx] [lindex \$yDataEFlux \$idx] [lindex \$yDataEFluxErr \$idx] [lindex \$modelDataEFlux \$idx]" } 
`#XSPEC12>` close \$unbinDataTable

`#XSPEC12>` cpd /xw
`#XSPEC12>` plot eemodel eeufspec 
`#XSPEC12>` setplot command rescale 0.3 10
`#XSPEC12>` setplot rebin 100000 5 
`#XSPEC12>` plot eemodel eeufspec
`#XSPEC12>` iplot
`#PLT>` hard $EFLUX/png 
`#PLT>` clear
`#PLT>` q
`#XSPEC12>` cpd /xw
`#XSPEC12>` plot ufspec 
`#XSPEC12>` setplot command rescale 0.3 10
`#XSPEC12>` setplot rebin 100000 5
`#XSPEC12>` plot ufspec
`#XSPEC12>` iplot
`#PLT>` hard $PHFLUX/png
`#PLT>` clear
`#PLT>` q

`#XSPEC12>` set xDataEnergy [tcloutr plot eeufspec x] 
`#XSPEC12>` set xDataEnergyErr [tcloutr plot eeufspec xerr]
`#XSPEC12>` set yDataEFlux [tcloutr plot eeufspec y] 
`#XSPEC12>` set yDataEFluxErr [tcloutr plot eeufspec yerr] 
`#XSPEC12>` set modelDataEFlux [tcloutr plot eeufspec model] 
`#XSPEC12>` set datatable [open $DATA_TBL w+]
`#XSPEC12>` set len [llength \$xDataEnergy] 
`#XSPEC12>` for {set idx 0} {\$idx < \$len} {incr idx} {puts \$datatable "[lindex \$xDataEnergy \$idx] [lindex \$xDataEnergyErr \$idx] [lindex \$yDataEFlux \$idx] [lindex \$yDataEFluxErr \$idx] [lindex \$modelDataEFlux \$idx]" }
`#XSPEC12>` close \$datatable

`#XSPEC12>` model clear
`#XSPEC12>` cpd none
`#XSPEC12>` quit
`#Do you really want to exit? (y)` y
EOF

done