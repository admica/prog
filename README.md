prog
====

Progress Bar GUI front end to run any command line application that provides completion output.

prog.py
=======
Execute any command line arguments you provide in a subprocess. Standard output from the
subprocess containing percentage completion text causes the progress bar to update. All stdout
is presented in an events window. The events are hidden by default. Clicking the details button
shows the scrollable events window.

Some parameters are easily configurable such as gui dimensions and scrollback history.

I made this as a simple front end for automated CD/DVD ripping, but just about anything with
human readable output should work. In the future I may add a counter for the number of progressions
and a setting to enable/disable auto-close after subprocess completion.

gibberish.py
============
This is a test driver for prog.py. It prints random strings with random occurences of incrementing
percentage completion text. It also randomly repeats between 1 and 3 cycles to simulate multiple
progress bars running sequentially.

Run it as the command argument to generate some output.
$ python prog.py ./gibberish.py

