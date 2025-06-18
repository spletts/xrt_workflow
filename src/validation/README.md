# Validation

To test this repository, I compare its results to the Swift-XRT SED from [A. A. Abdo et al 2011 ApJ 736 131](https://iopscience.iop.org/article/10.1088/0004-637X/736/2/131/pdf).

This is limited validation in that I get one SED per ObsID and do not stack the data; thus xrt_workflow does the same. The scripts in this folder are edited to stack the data over a period of time rather than analysing ObsIDs individually.

### SED
[SED plot](sed.png), [SED plot with truncated y axis](sed_ylims.png)

### Spectral parameters
* The fits in xrt_workflow failed due to the reduced chi squared being too high, using `fit 1000`; thus there are no errors on these values. The fits are performed on the unbinned data.

|                       | Abdo et al 2011                        | xrt_workflow     |
| -----------           | ------------------                     | -------          |
| K (ph/cm$^{-2}$/s/keV)  | (1.839 $\pm$ 0.002) $\times$ 10$^{−1}$ | 0.173946 $\pm$ ? |
| $\Gamma$              | 2.178 $\pm$ 0.002                      | 2.20472 $\pm$ ?  |
| $\beta$               | 0.391 $\pm$ 0.004                      | 0.277333 $\pm$ ? |


### Analysis similarities and differences 
The differences in the analysis are noted below:
* The Abdo et al 2011 paper stacked 46 observations from MJD 54858 to 54979. I search the dates MJD 54858 to 54979 (2009/01/27-2009/05/28) and get a stack of 48 observations.
* The details of the Swift-XRT analysis in Abdo et al 2011 are controlled by [xrt_prods](https://www.swift.ac.uk/user_objects/API). Those are unlikely the same now as they were at the time of the Abdo et al 2011. Such as:
    * Choice of source and background regions
    * Software versions (Abdo et al 2011 use XRTDAS. v2.5.0, HEASoft v.6.7, latest CALDB files, xrtmkarf)
    * etc
* Abdo et al 2011 applied ∼40 eV offset to the observed SED.
* Abdo et al 2011 corrected for absorption and *then* binned in 16 energy intervals. I rebinned within XSpec to get 16 bins and then corrected for absorption.

The similarities:
* Grouped 20 counts per bin
* Fit log parabola and ignored 1.4–2.3 keV

Unclear:
* I used `phabs` absorption model. Not sure what was used in Abdo et al 2011.
