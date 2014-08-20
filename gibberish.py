#!/usr/bin/env python

'''Gibberish output test for Prog'''

__author__ = 'admica <crazychickenhead@hotmail.com>'
__doc__ = 'Gibberish'

from time import sleep
import random
import string

print "Starting random percent incrementing with random gibberish output"

num_repeats = random.randint(1,3)
for repeat in range(1,num_repeats):

    for i in range(1, 100):
        size = random.randint(20, 200)
        chars = string.letters
        junk = ''.join(random.choice(chars) for x in range(size))

        print junk

        if not random.randint(0,5):
            print junk

        else:
            print junk[:10], '%s%%' % i, junk[:-10]

        sleep(.03)

print 'Test thing 100% complete.'
sleep(.25)
print 'Final gibberish before exiting.'

