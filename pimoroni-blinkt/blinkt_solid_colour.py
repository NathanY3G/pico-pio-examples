# Copyright 2021 Nathan Young
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import array
import board
import rp2pio
from adafruit_pioasm import assemble
from time import sleep

CLOCK_PIN = board.GP19
DATA_PIN = board.GP18

BRIGHTNESS = 1
PIXEL_VALUES = [
    (BRIGHTNESS << 24) | 0x0000FF,
    (BRIGHTNESS << 24) | 0x00FF00,
    (BRIGHTNESS << 24) | 0xFF0000,
]


def assemble_program(filename):
    with open(filename, "rt") as file:
        return assemble(file.read())


with rp2pio.StateMachine(
    assemble_program("blinkt_solid_colour.pio"),
    frequency=2_000_000,
    first_out_pin=DATA_PIN,
    out_pin_count=1,
    first_set_pin=DATA_PIN,
    set_pin_count=1,
    first_sideset_pin=CLOCK_PIN,
    sideset_pin_count=1,
    initial_set_pin_direction=3,
    out_shift_right=False,
) as state_machine:
    while True:
        for pixel_value in PIXEL_VALUES:
            state_machine.write(array.array("I", [pixel_value]))
            sleep(1)
