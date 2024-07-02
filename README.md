# Application-3
The [official] repository for application3

IMPORTANT:
If you are using the application in U4, then change the initialization of ls370 to GPIB0, else it's GPIB1

Changelog
--------
version 3.5

Changes:
 - Bug: Start-Stop button responding slowly FIXED
 - Bug: "Slow acquisations only" mode not switching correctly FIXED
    - [The mode is automatically switched off after stopping acquisition]
 - New Feature: The current can now be changed in the new Current control tab
    - The slow and fast mode switching is now purely based on the On and Off times of the current
    - Stable time is deprecated and Stabilization Time now defines the time before and after applying current
    - The columns of the output file now look like this:
         [Time | AC370 Ch1 | I from AC370 | I from GS200 | V from Picoscope | AC370 Ch2 | AC370 Ch3 | AC370 Ch4]


version: 3.4
Changes:
 - ...