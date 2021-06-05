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
import pytest
from collections import deque
import subprocess
from pioemu import clock_cycles_reached, emulate, State

BITS_PER_BYTE = 8
NUMBER_OF_LEDS = 8
PIO_SOURCE_FILE = "blinkt_solid_colour.pio"


@pytest.fixture
def assembled_program():
    output = subprocess.run(
        ["pioasm", "-o", "hex", PIO_SOURCE_FILE], capture_output=True
    )

    if output.returncode != 0:
        raise ValueError(f"Unable to assemble PIO program {PIO_SOURCE_FILE}")

    return [int(opcode, 16) for opcode in output.stdout.decode("utf-8").split()]


def expected_pixel_sequence(red_on, green_on, blue_on):
    """Generates clock and data sequence expected by the Pimoroni Blinkt! for the colour specified"""

    zero = [(1, 0), (0, 0)]  # Clock and data sequence representing a zero (0)
    one = [(1, 1), (0, 1)]  # Clock and data sequence representing a zero (1)

    brightness = one * BITS_PER_BYTE

    return (
        brightness
        + (one if blue_on else zero) * BITS_PER_BYTE
        + (one if green_on else zero) * BITS_PER_BYTE
        + (one if red_on else zero) * BITS_PER_BYTE
    ) * NUMBER_OF_LEDS


def test_start_sequence(assembled_program):
    clock_and_data_sequence = emulate_program(assembled_program, 0)

    # The start sequence should consist of 32 zeros
    assert clock_and_data_sequence[0:64] == [(1, 0), (0, 0)] * 32


# fmt:off
@pytest.mark.parametrize(
    "fifo_input, expected_sequence",
    [
        pytest.param(0x01F00_00FF, expected_pixel_sequence(True, False, False), id="Bright Red"),
        pytest.param(0x01F00_FF00, expected_pixel_sequence(False, True, False), id="Bright Green"),
        pytest.param(0x01FFF_0000, expected_pixel_sequence(False, False, True), id="Bright Blue"),
        pytest.param(0x01FFF_FFFF, expected_pixel_sequence(True, True, True), id="Bright White"),
    ],
)
# fmt:on
def test_pixel_sequence(assembled_program, fifo_input, expected_sequence):
    clock_and_data_sequence = emulate_program(assembled_program, fifo_input)

    assert clock_and_data_sequence[64:-64] == expected_sequence


def test_end_sequence(assembled_program):
    clock_and_data_sequence = emulate_program(assembled_program, 0)

    # The end sequence should consist of 32 zeros
    assert clock_and_data_sequence[-64:] == [(1, 0), (0, 0)] * 32


def emulate_program(program, colour_value):
    stop_after_one_iteration = lambda _, state: state.program_counter >= len(program) - 1

    emulator_gen = emulate(
        program,
        initial_state=State(transmit_fifo=deque([colour_value])),
        stop_when=stop_after_one_iteration,
        side_set_base=1,
        side_set_count=1,
        shift_osr_right=False,
    )

    return [
        extract_clock_and_data(after.pin_values)
        for before, after in emulator_gen
        if before.pin_values != after.pin_values
    ]


def extract_clock_and_data(pin_values):
    return ((pin_values >> 1) & 1, pin_values & 1)
