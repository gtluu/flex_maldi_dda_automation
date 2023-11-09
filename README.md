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
pip install git+https://github.com/gtluu/flex_maldi_dda_automation.git
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
