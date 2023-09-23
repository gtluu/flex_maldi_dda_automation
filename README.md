# Automated Data Dependent Acquisition for the timsTOF fleX via MALDI-TOF MS/MS

This workflow serves as an automated workflow that uses in house automation scripts to allow for automated acquisition of MALDI-TOF MS/MS spectra in a data dependent fashion on the Bruker timsTOF fleX in timsControl 4.0.5. Full scan MS data is first collected using standard data acquisition protocols utilizing automation through AutoXecute. 

## Installation

This workflow should be installed on the system used for data acquisition as it relies on local file paths. Code from [TIMSCONVERT](https://github.com/gtluu/timsconvert) has been included locally.

#### Install Anaconda on Windows.

1. Download and install Anaconda for [Windows](https://repo.anaconda.com/archive/Anaconda3-2021.11-Windows-x86_64.exe). 
Follow the prompts to complete installation.
2. Run ```Anaconda Prompt (R-MINI~1)``` as Administrator.

#### Set Up ```conda env```

3. Create a conda instance. You must be using Python 3.7.
```
conda create -n maldi_dda python=3.7
```
4. Activate conda environment.
```
conda activate maldi_dda
```

#### Install This Workflow

5. Download this workflow by cloning the Github repo.
```
git clone https://www.github.com/gtluu/flex_maldi_dda_automation
```
6. Install dependencies.
```
pip install -r /path/to/flex_maldi_dda_automation/requirements.txt
```
7. You will also need to install [TIMSCONVERT](https://github.com/gtluu/timsconvert).
```
pip install git+https://github.com/gtluu/timsconvert.git
```

## Usage

To run with default parameters:

```
python run.py --autox autox_file.run
```

Use the following command for a list and description of parameters:

```
python run.py --help
```
