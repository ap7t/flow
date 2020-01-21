# flow
A program that changes the colour of an LIFX Bulb based on different sections of a song playonig on Spotify. 
Flow also can flash to the beats and change between strobing and breathing effects based on loudness and tempo changes.

usage: flow.py [-h] [-s] [-b] [-m] [-t]

optional arguments:

  -h, --help          show this help message and exit
  
  -s, --strobe        strobe to the BPM of a song (changes based on tempo
                      changes)
                 
  -b, --breathe       breathe to the BPM of a song (changes based on tempo
                      changes)
                 
  -m, --mixed         changes between stobing and breathing to BPM of a song
                      (changes based on loudness changes)
                 
  -t, --tempo         relative changes in tempo between sections will not
                      change the period of light effect
  
