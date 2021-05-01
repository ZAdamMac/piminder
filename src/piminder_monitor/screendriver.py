"""
This script is a component of the monitoring service for the Piminder alert management utility..
It is the full set of display drivers for interfacing between the monitor code and the screen itself.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
A Kensho Security Labs utility.
Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Piminder
"""

from gfxhat import lcd, backlight
from . import font


def print_line(line_index, input_string):
    """ Prints the displayed text on one of the 5 output rows. Strings too long to be displayed will be truncated.

    :param line_index: integer from 1:5 addressing the line to e written to.
    :param input_string: Output string not to exceed 16 characters.
    :return:
   """
    line_absolute = dict_absolute_line_indexes[line_index]
    # a dictionary of the positions of the upper row of each printable "line"
    char_index = 0
    input_string = "%-16s" % input_string
    for i in range(0, 16):
        this_character = input_string[i]
        line_offset = 0
        for line in range(0, 8):
            pixel_offset = 0
            for pixel in font.font[this_character][line_offset]:
                addr_x = char_index + pixel_offset
                addr_y = line_absolute + line_offset
                lcd.set_pixel(addr_x, addr_y, pixel)
                pixel_offset += 1
            line_offset += 1
        char_index += 8

    lcd.show()


def kill_backlight():
    backlight.set_all(0, 0, 0)
    backlight.show()


def backlight_set_hue(hue):
    """Expects a colour code in the usual HTML format, and sets that colour to be the RGB background colour.

    :param hue:
    :return:
    """
    red = int(hue[1:3], 16)
    green = int(hue[3:5], 16)
    blue = int(hue[5:7], 16)
    backlight.set_all(red, green, blue)
    backlight.show()


def clear_screen():
    lcd.clear()
    lcd.show()

# This small dictionary allows us to address the lines as lines of text rather than individual pixel-tall lines
dict_absolute_line_indexes = {
    0: 0,
    1: 8,
    2: 16,
    3: 24,
    4: 32,
    5: 40,
    6: 48,
    7: 56
}
