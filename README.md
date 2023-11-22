# Automated Data Dependent Acquisition for the timsTOF fleX via MALDI-TOF MS/MS

This workflow serves as an automated workflow that uses in house automation scripts to allow for automated acquisition 
of MALDI-TOF MS/MS spectra in a data dependent fashion on the Bruker timsTOF fleX in timsControl 4.1.2. Full scan MS 
data is first collected using standard data acquisition protocols utilizing automation through AutoXecute. 

## Installation

This workflow should be installed on the system used for data acquisition as it relies on local file paths.

#### Install Anaconda and Git on Windows.

1. Download and install Anaconda for [Windows](https://repo.anaconda.com/archive/Anaconda3-2023.07-2-Windows-x86_64.exe). 
Follow the prompts to complete installation.
2. Download and install [Git](https://git-scm.com/downloads) and ensure that the option to enable symbolic links was 
checked during installation if not already installed.
3. Run ```Anaconda Prompt```.

#### Set Up ```conda env```

4. Create a conda instance.
```
conda create -n maldi_dda python=3.11
```
5. Activate conda environment.
```
conda activate maldi_dda
```

#### Install This Workflow

6. Install with the following command.
```
pip install git+https://github.com/gtluu/flex_maldi_dda_automation.git --use-pep517
```

## Usage

To run with default parameters:

```
process_maldi_dda --autox autox_file.run
```

Use the following command for a list and description of parameters:

```
process_maldi_dda --help
```

#### Preprocessing Parameters

Default preprocessing parameters are specified in ```preprocessing.cfg```.

```
[preprocessing]
trim_spectra = yes
transform_intensity = yes
smooth_baseline = yes
remove_baseline = yes
normalize_intensity = yes
bin_spectra = yes
align_spectra = yes

[trim_spectra]
lower_mass_range = 100
upper_mass_range = 2000

[transform_intensity]
method = sqrt

[smooth_baseline]
method = SavitzkyGolay
window_length = 21
polyorder = 3
delta_mz = 0.2
diff_thresh = 0.01

[remove_baseline]
method = SNIP
min_half_window = 1
max_half_window = 100
decreasing = yes
smooth_half_window = None
filter_order = 2
sigma = None
increment = 1
max_hits = 1
window_tol = 0.000001
lambda_ = 100
porder = 1
repetition = None
degree = 2
gradient = 0.001

[normalize_intensity]
method = tic

[bin_spectra]
n_bins = 38000
lower_mass_range = 100
upper_mass_range = 2000

[align_spectra]
method = average
inter = whole
n = f
scale = None
coshift_preprocessing = no
coshift_preprocessing_max_shift = None
fill_with_previous = yes
average2_multiplier = 3

```

User defined parameters can be defined by copying this file and changing the parameters as needed. The 
```preprocessing``` section specifies whether that preprocessing step should be run. Parameters for each preprocessing 
step are specified and can be modified in their respective sections. ```yes``` and ```no``` represent the boolean 
values ```True``` and ```False```, respectively.

After editing your custom preprocessing parameters, run this workflow with the following command:

```
process_maldi_dda --autox autox_file.run --preprocessing /path/to/custom_preprocessing.cfg
```