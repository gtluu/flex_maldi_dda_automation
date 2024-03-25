Installation
------------
Simply unzip the folder and run "ms1_autox_generator.exe" to start the program.

Usage
-----
MALDI Plate Map
Click on "Browse" to select a *.csv format plate map. Example plate maps for 48, 96, 384, 1536, and 6144 format plates are provided.

Methods
Click on the load methods button to load a single timsControl method (*.m directory) or a directory containing multiple *.m directories.
All methods will be loaded in the table below.
For each method loaded, a Spot Group will be greated for the AutoXecute sequence and named after the sample name + method name.
For example, if your plate map contains "sample1" and "sample2", and you loaded "method1.m" and "method2.m, four spot groups will be created:
"sample1_method1"
"sample2_method1"
"sample1_method2"
"sample2_method2"
To remove one or more methods from the list of methods, select the row(s) and click "Remove Methods".

MALDI Plate Geometry
Available plate geometries are loaded from the directory containing MALDI plate geometries.
By default, this is D:\Methods\GeometryFiles.
If no options are displayed in the dropdown menu, the GeometryFiles directory may need to be changed.
This can be done in "Settings" > "Edit Path to GeometryFiles Directory" and select the new directory where the geometry files (*.xeo files) are found.

timsControl Version
This program will attempt to detect the current version of timsControl that is installed.
However, if no installation of timsControl is found, it will default to using the version of timsControl distributed with Compass 2024b SR1.