#!/bin/bash

<<comment
Uses the model tbabs*powerlaw with:

Fixed TBabs:nH = $NH_TBABS (Milky Way absorption; $NH_TBABS set in config.sh)

FREE powerlaw:PhoIndex
FREE powerlaw:norm
comment

# One and only command line argument is the config filename
CFG_FN=$1

source ${CFG_FN}


# Read as array, not string. Variables defined in CFG_FN.
read -a OID_ARRAY <<< "$OIDS"
read -a MODE_ARRAY <<< "$MODES"
# echo $OIDS
# echo $MODES
# echo $OID_ARRAY
# echo $MODE_ARRAY

length=${#OID_ARRAY[@]}

for ((j=0; j<length; j++)); do

oid=${OID_ARRAY[$j]}
mode=${MODE_ARRAY[$j]}

# Isolate USERPROD* and the numbers that follow in the directory name. I don't know how these numbers are determined.
userprod_dir_name=`basename ${BASE_DATA_DIR}/${oid}/USERPROD*`
# Directory with downloaded data products
data_dir=${BASE_DATA_DIR}/${oid}/${userprod_dir_name}/${SPEC_STEM}
# Output for XSpec analysis
xspec_outdir=${data_dir}/powlaw_tbabs

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

# Variables set *within* EOF need to be referenced with a backslash in front of the $ (e.g. \$xDataEnergy)
# Ref: https://stackoverflow.com/questions/47551672/variable-not-getting-picked-up-inside-eof

# Format for below: `#{command prompt}>` command `#{comment}`
# Lots of the comments are directly from the XSpec Users’ Guide for version 12.12.1
# Avoiding comments above code because a blank line represents the Enter key
xspec << EOF > ${xspec_outdir}/${LOG_XSPEC}
`#XSPEC12>` data $CHI2_GRP_SPEC `#Load spectral file grouped by grppha`
`#XSPEC12>` ignore bad `#Ignore bad channels`
`#XSPEC12>` ignore **-0.3 `#Ignore energies below 0.3 keV`
`#XSPEC12>` ignore 10.0-** `#Ignore energies above 10 keV`
`#XSPEC12>` cpd /xw `#Set plot device`
`#XSPEC12>` setplot energy keV `#Set the x-axis to energy in keV`
`#XSPEC12>` abund wilm `#Most up to date adundannces`
`#XSPEC12>` model tbabs(powerlaw) `#Galactic absorbed power law`
`#1:tbabs:nH>` $NH_TBABS `#Galactic nH. Units are 10^22 atoms/cm^2`
`#2:powerlaw:PhoIndex>` `#Use default value`
`#3:powerlaw:norm>` `#Use default value`
`#XSPEC12>` freeze 1 `#Fix nH`
`#XSPEC12>` fit
`#XSPEC12>` save all $xspec_outdir/fit `#Save all XSpec commands issued thus far in a file`

`#XSPEC12>` error 1. 2-3 `#1 sigma range(?) for parameters 2-3 (PhoIndex and norm, respectively)`
`#XSPEC12>` flux 2 10 err `#Calc integral flux between 2-10 keV and the 68% confidence interval (flux with absorption)`
`#XSPEC12>` set parFlux [tcloutr flux] `#6 values: val errLow errHigh (in ergs/cm2) val errLow errHigh (in photons); The flux is given in units of photons/cm2/s and ergs/cm2/s`
`#XSPEC12>` set parIndex [tcloutr param 2] `#Term in brackets returns: 'value, delta, min, low, high, max' for parameter 2 (PhoIndex)`
`#XSPEC12>` set parIndexErr [tcloutr error 2] `#'Writes last confidence region calculated'. This is 1sigma if this was the previously specified 'error 1.'. If everything went well, the error string should be FFFFFFFFF. 'tcloutr error 1. 2' results in no output`
`#XSPEC12>` set parNorm [tcloutr param 3]  `#Value for norm`
`#XSPEC12>` set parNormErr [tcloutr error 3] `#Get parameter bounds for norm`
`#XSPEC12>` set rateEtc [tcloutr rate all] `#Count rate, uncertainty, model rate, and percentage of net flux (no background) compared to total flux`
`#XSPEC12>` set cRate [lindex \$rateEtc 0] `#Count rate (cts/s)`
`#XSPEC12>` set cRateErr [lindex \$rateEtc 1] `#Count rate uncertainty (cts/s)`
`#XSPEC12>` set cRateLow [expr {\$cRate - \$cRateErr}]  `#Count rate lower bound`
`#XSPEC12>` set cRateHigh [expr {\$cRate + \$cRateErr}] `#Count rate higher bound`
`#XSPEC12>` set paramTable [open $PARAM_TBL w+] `#Prepare to write data to file PARAM_TBL`
`#XSPEC12>` puts \$paramTable "[lindex name 0] [lindex param 0] [lindex param_low 0] [lindex param_high 0] [lindex error_string 0]" `#Add header`
`#XSPEC12>` puts \$paramTable "[lindex PhoIndex 0] [lindex \$parIndex 0] [lindex \$parIndexErr 0] [lindex \$parIndexErr 1] [lindex \$parIndexErr 2]" `#0th index of parIndex contains 'value'. 0th index of parIndexErr has the lower bound on the parameter, 1st has upper bound.`
`#XSPEC12>` puts \$paramTable "[lindex norm 0] [lindex \$parNorm 0] [lindex \$parNormErr 0] [lindex \$parNormErr 1] [lindex \$parNormErr 2]" `#Write 3rd row of table`
`#XSPEC12>` puts \$paramTable "[lindex flux 0] [lindex \$parFlux 3] [lindex \$parFlux 4] [lindex \$parFlux 5] [lindex 0 0]"
`#XSPEC12>` puts \$paramTable "[lindex countrate 0] [lindex \$cRate 0] [lindex \$cRateLow 0] [lindex \$cRateHigh 0] [lindex 0 0]"
`#XSPEC12>` close \$paramTable
`#XSPEC12>` set nullProb [tcloutr nullhyp] `#Null hypothesis probability. 'If this probability is small then the model is not a good fit.'`
`#XSPEC12>` set chiSq [tcloutr stat] `#Value of fit statistic. In this file, Fit statistic  : Chi-Squared`
`#XSPEC12>` set dof [tcloutr dof] `#Degrees of freedom in fit, and the number of channels.`
`#XSPEC12>` set statTable [open $STAT_TBL w+]
`#XSPEC12>` puts \$statTable "[lindex chi_squared 0] [lindex deg_freedom 0] [lindex null_hyp_probability 0]" `#Add header`
`#XSPEC12>` puts \$statTable "[lindex \$chiSq 0] [lindex \$dof 0] [lindex \$nullProb 0]"
`#XSPEC12>` close \$statTable

`#XSPEC12>` plot res `#Plot residual with default binning. Look at the residuals with default binning (do not rebinn the residuals)`
`#XSPEC12>` setplot command rescale 0.3 10 `#Set x-axis limits to 0.3-10 keV`
`#XSPEC12>` iplot
`#PLT>` hard $RESID_PLT/png `#Save file with name RESID_PLT`
`#PLT>` clear
`#PLT>` q

`#XSPEC12>` plot eemodel eeufspec `#Make 2 subplots: 1. E^2 dN/dE from model 2. E^2 dN/dE from unfolded spectrum (model dependent)`
`#XSPEC12>` setplot command rescale 0.3 10 `#Set x-axis limits to 0.3-10 keV`
`#XSPEC12>` plot eemodel eeufspec `#Replot so the commands above are implemented`
`#XSPEC12>` set xDataEnergy [tcloutr plot eeufspec x] `#'xDataEnergy' is x-axis of eeufspec = energies in keV`
`#XSPEC12>` set xDataEnergyErr [tcloutr plot eeufspec xerr] `#'xDataEnergy' is half bin width in keV`
`#XSPEC12>` set yDataEFlux [tcloutr plot eeufspec y] `#'yDataEFlux' is y-axis of eeufspec = energy flux in keV/cm^2/s`
`#XSPEC12>` set yDataEFluxErr [tcloutr plot eeufspec yerr] `#'$yDataEFluxErr' is error on energy flux in keV/cm^2/s`
`#XSPEC12>` set modelDataEFlux [tcloutr plot eeufspec model] `#'$modelDataEFlux' is energy flux from the model in keV/cm^2/s`
`#XSPEC12>` set unbinDataTable [open $UNBINNED_DATA_TBL w+] `#Prepare to write data to file`
`#XSPEC12>` set len [llength \$xDataEnergy] `#'$xDataEnergy' is set within 'EOF ... EOF' so it needs to be preceded by '\'`
`#XSPEC12>` for {set idx 0} {\$idx < \$len} {incr idx} {puts \$unbinDataTable "[lindex \$xDataEnergy \$idx] [lindex \$xDataEnergyErr \$idx] [lindex \$yDataEFlux \$idx] [lindex \$yDataEFluxErr \$idx] [lindex \$modelDataEFlux \$idx]" } `#Format file headers: energy (keV), energy half bin width, eflux (keV/cm^2/s), eflux_error, model_eflux`
`#XSPEC12>` close \$unbinDataTable

`#XSPEC12>` cpd /xw
`#XSPEC12>` plot eemodel eeufspec `#Make 2 subplots of E^2 dN/dE of model and also unfolded spectrum; energy flux`
`#XSPEC12>` setplot command rescale 0.3 10 `#Set x-axis limits to 0.3-10 keV`
`#XSPEC12>` setplot rebin 100000 5 `#Rebin until signal:noise=100000 or 5 bins combined into one. This is intended to implement 5 bins combined into one.`
`#XSPEC12>` plot eemodel eeufspec `#Replot so the commands above are implemented`
`#XSPEC12>` iplot
`#PLT>` hard $EFLUX/png `#Save energy flux plot as a png`
`#PLT>` clear
`#PLT>` q
`#XSPEC12>` cpd /xw
`#XSPEC12>` plot ufspec `#Plot photon flux dN/dE`
`#XSPEC12>` setplot command rescale 0.3 10
`#XSPEC12>` setplot rebin 100000 5
`#XSPEC12>` plot ufspec
`#XSPEC12>` iplot
`#PLT>` hard $PHFLUX/png
`#PLT>` clear
`#PLT>` q

`#XSPEC12>` set xDataEnergy [tcloutr plot eeufspec x] `#'xDataEnergy' is x-axis of eeufspec = energies in keV`
`#XSPEC12>` set xDataEnergyErr [tcloutr plot eeufspec xerr] `#'xDataEnergy' is half bin width in keV`
`#XSPEC12>` set yDataEFlux [tcloutr plot eeufspec y] `#'yDataEFlux' is y-axis of eeufspec = energy flux in keV/cm^2/s`
`#XSPEC12>` set yDataEFluxErr [tcloutr plot eeufspec yerr] `#'$yDataEFluxErr' is error on energy flux in keV/cm^2/s`
`#XSPEC12>` set modelDataEFlux [tcloutr plot eeufspec model] `#'$modelDataEFlux' is energy flux from the model in keV/cm^2/s. 'Data by themselves only give the instrument-dependent count rateEtc. The model, on the other hand, is an estimate of the true spectrum emitted.'`
`#XSPEC12>` set datatable [open $DATA_TBL w+]
`#XSPEC12>` set len [llength \$xDataEnergy]
`#XSPEC12>` for {set idx 0} {\$idx < \$len} {incr idx} {puts \$datatable "[lindex \$xDataEnergy \$idx] [lindex \$xDataEnergyErr \$idx] [lindex \$yDataEFlux \$idx] [lindex \$yDataEFluxErr \$idx] [lindex \$modelDataEFlux \$idx]" } `#Format file headers: energy (keV), energy half bin width, eflux (keV/cm^2/s), eflux_error, model_eflux`
`#XSPEC12>` close \$datatable

`#XSPEC12>` model clear
`#XSPEC12>` cpd none
`#XSPEC12>` quit
`#Do you really want to exit? (y)` y
EOF

done