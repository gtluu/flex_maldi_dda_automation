About
=====
This workflow uses a modified version of `TIMSCONVERT <https://github.com/gtluu/timsconvert>`_ to take multiple raw
MALDI-qTOF Dried Droplet MS datasets from the Bruker timsTOF fleX from successive AutoXecute runs with different,
non-overlapping mass range windows and combines them into a single consensus spectrum with the "full" mass range.

Installation
============

Installing on Windows
---------------------
1. Download and install `Anaconda for Windows <https://repo.anaconda.com/archive/Anaconda3-2023.07-2-Windows-x86_64.exe>`_ if not already installed. Follow the prompts to complete installation.

2. Download and install `Git for Windows <https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe>`_ if not already installed.

3. Run ``Anaconda Prompt``.

4. Create a conda instance.

   .. code-block::

        conda create -n maldi_polymerization python=3.11

5. Activate conda environment.

   .. code-block::

        conda activate maldi_polymerization

6. Install dependencies.

   .. code-block::

        pip install -r https://raw.githubusercontent.com/gtluu/flex_maldi_dda_automation/gui/maldi_polymerization/requirements.txt

7. Simply clone the `flex_maldi_dda_automation <https://github.com/gtluu/flex_maldi_dda_automation>`_ repo or download the standalone script `here <https://github.com/gtluu/flex_maldi_dda_automation/blob/gui/maldi_polymerization/maldi_polymerization.py>`_.

8. See below for usage information and example.

Installing on Linux
-------------------
1. If not already installed, download and install `Anaconda for Linux <https://repo.anaconda.com/archive/Anaconda3-2023.07-2-Linux-x86_64.sh>`_. Anaconda3-2023.07-2 for Linux is used as an example here.

   * Alternatively, the script can be downloaded in the ``Terminal`` using the following command.

   .. code-block::

        wget https://repo.anaconda.com/archive/Anaconda3-2023.07-2-Linux-x86_64.sh

2. If not already installed, install ``git``. On Ubuntu 23.04.3 LTS, this can be done using the following command.

   .. code-block::

        sudo apt-get install git

3. Install Anaconda for Linux via the bash script that was downloaded. After installation, restart the terminal (or open a new terminal window).

   .. code-block::

        bash [path to]/Anaconda3-2023.07-2-Linux-x86_64.sh

4. In the terminal, create a conda virtual environment.

   .. code-block::

        conda create -n maldi_polymerization python=3.11

5. Activate conda environment.

   .. code-block::

        conda activate maldi_polymerization

6. Install dependencies.

   .. code-block::

        pip install -r https://raw.githubusercontent.com/gtluu/flex_maldi_dda_automation/gui/maldi_polymerization/requirements.txt

7. Simply clone the `flex_maldi_dda_automation <https://github.com/gtluu/flex_maldi_dda_automation>`_ repo or download the standalone script `here <https://github.com/gtluu/flex_maldi_dda_automation/blob/gui/maldi_polymerization/maldi_polymerization.py>`_.

8. See below for usage information and example.

Usage
=====
This workflow is run from the command line.

Parameters
----------
``--input``: One or more MALDI-MS .d directories acquired from the timsTOF fleX in successive AutoXecute runs with
different, non-overlapping mass range windows.

``--output``: Name of the resulting mzML file.

``--mode``: Choose whether to export to spectra in ``profile``, ``centroid``, or ``raw`` mode. Defaults to centroid.

``--compression``: Choose between ZLIB compression (``zlib``) or no compression (``none``). Defaults to ``zlib``.

``--encoding``: Choose encoding for binary arrays: 32-bit (``32``) or 64-bit (``64``). Defaults to 64-bit.

``--barebones_metadata``: Only use basic mzML metadata. Use if downstream data analysis tools throw errors with
descriptive CV terms.

Example
-------

    .. code-block::

        python maldi_polymerization/maldi_polymerization.py --input strain1_mr1.d strain1_mr2.d strain1_mr3.d --output test.mzML
