Usage
-----
usage: maldi_polymerization.py [-h] --input INPUT [INPUT ...] --output OUTPUT
                               [--mode {raw,centroid,profile}]
                               [--compression {zlib,none}]
                               [--encoding {64,32}] [--barebones_metadata]

options:
  -h, --help            show this help message and exit
  --input INPUT [INPUT ...]
                        One or more MALDI-MS .d directories acquired from the
                        timsTOF fleX in successive AutoXecute runs with
                        different, non-overlapping mass range windows.
  --output OUTPUT       Name of the resulting mzML file.
  --mode {raw,centroid,profile}
                        Choose whether export to spectra in raw or centroid
                        formats. Defaults to centroid.
  --compression {zlib,none}
                        Choose between ZLIB compression (zlib) or no
                        compression (none). Defaults to zlib.
  --encoding {64,32}    Choose encoding for binary arrays: 32-bit (32) or
                        64-bit (64). Defaults to 64-bit.
  --barebones_metadata  Only use basic mzML metadata. Use if downstream data
                        analysis tools throw errors with descriptive CV terms.

Example
-------
python maldi_polymerization/maldi_polymerization.py --input strain1_mr1.d strain1_mr2.d strain1_mr3.d --output test.mzML