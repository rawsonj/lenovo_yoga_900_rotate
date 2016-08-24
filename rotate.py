#!/usr/bin/python

from time import sleep
from os import path
import sys
from subprocess import check_call
from glob import glob


# Find your devices for your touchpad and touchscreen.
# These can be either X device ID's or their names
# from `xinput --list --name-only`.
touchpad = '10'
touchscreen = '11'

# Figure out which device enumerated to be the accelerometer,
# because it moves on every boot.
for basedir in glob('/sys/bus/iio/devices/iio:device*'):
    with open(path.join(basedir, 'name')) as fd:
        if 'accel' in fd.read():
            break
else:
    sys.stderr.write("Can't find an accelerometer device!\n")
    sys.exit(1)


def read_accel():
    '''
    Go fetch the current accelerometer value.
    '''
    axis_vals = []
    for axis in ['x', 'y', 'z']:
        with open(path.join(basedir, 'in_accel_' + axis + '_raw')) as fd:
            axis_vals.append(float(fd.read()))

    return axis_vals


def choose_state():
    '''
    When the accelerometer is below the 65000 mark, we're basically
    facing that direction and it's a really stable value.

    We don't handle "left" right now. It doesn't
    make sense really since the power and rotation-freeze buttons
    are on that side for the Yoga 900.

    You can play with the numbers here to get different behaviors.
    '''
    # Get accelerator values
    x, y, z = read_accel()

    if 64700 > x and x > 64000:
        return "right"
    elif 64600 > z and z > 64000 or 65500 > y and y > 64000:
        return "normal"
    else:
        return "inverted"

# This establshes touchscreen orientation.
coordinates = {"normal": ['1', '0', '0', '0', '1', '0', '0', '0', '1'],
               "inverted": ['-1', '0', '1', '0', '-1', '1', '0', '0', '1'],
               "right": ['0', '1', '0', '-1', '0', '1', '0', '0', '1']
               }


def rotate(state):
    # TODO: Disable the touchpad if the keyboard is flipped
    # to behind the screen, since it also makes sense not
    # to have that input if we're being a tablet.
    # This is apparently harder than what it sounds on the yoga.

    # Set the screen orientation.
    check_call(['xrandr', '-o', state])

    # Disable the touchpad if the orientation isn't normal.
    if state != 'normal':
        check_call(['xinput', 'disable', touchpad])
    else:
        check_call(['xinput', 'enable', touchpad])

    # Set the touchscreen orientation.
    touchscreen_command = ['xinput', 'set-prop', touchscreen,
                           'Coordinate Transformation Matrix']
    touchscreen_command.extend(coordinates[state])
    check_call(touchscreen_command)


if __name__ == '__main__':
    current_state = 'normal'

    while True:
        next_state = choose_state()

        if current_state != next_state:
            current_state = next_state
            rotate(current_state)

        # Fundamentally, we have to poll the accelerometer, so
        # we will be spending cpu cycles doing that and updating state.
        # If you want a more responsive screen orientation, reduce the
        # amount of time you sleep. If you want to save processing
        # cycles, increase the amount you sleep.
        sleep(0.7)
