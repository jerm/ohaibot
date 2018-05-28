#!/usr/bin/env python
import os
from gpiozero import Button
from signal import pause

#  https://gpiozero.readthedocs.io/en/stable/api_input.html#button
ohai = 1
def do_shutdown(foo):
    os.system('shutdown -h now')

def do_ohai(foo):
    global ohai
    print "Ohai", ohai
    ohai += 1
    #os.system('shutdown -h now')

def do_kthxbai(foo):
    global ohai
    print "Kthxbai", ohai
    ohai += 1
    #os.system('shutdown -h now')

button = Button(4, hold_time=3, bounce_time=0.001)
button.when_held = do_shutdown
button.when_pressed = do_ohai
button.when_released = do_kthxbai
#button.wait_for_press()
def main():
    pause()
if __name__ == '__main__':
    main()
