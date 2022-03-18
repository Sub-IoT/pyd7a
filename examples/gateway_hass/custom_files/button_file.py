#
# Copyright (c) 2015-2021 University of Antwerp, Aloxy NV.
#
# This file is part of pyd7a.
# See https://github.com/Sub-IoT/pyd7a for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import struct

from enum import Enum

from d7a.support.schema import Validatable, Types
from d7a.system_files.file import File
from .custom_file_ids import CustomFileIds

class ButtonStates(Enum):
    NO_BUTTON_PRESSED = 0
    BUTTON1_PRESSED = 1
    BUTTON2_PRESSED = 2
    BUTTON1_2_PRESSED = 3
    BUTTON3_PRESSED = 4
    BUTTON1_3_PRESSED = 5
    BUTTON2_3_PRESSED = 6
    ALL_BUTTONS_PRESSED = 7

FILE_SIZE = 6

class ButtonFile(File, Validatable):
  SCHEMA = [{
    "button_id": Types.INTEGER(min=0, max=0xFF),
    "mask": Types.INTEGER(min=0, max=0xFF),
    "elapsed_deciseconds": Types.INTEGER(min=0, max=0xFF),
    "state": Types.ENUM(ButtonStates),
    "battery_voltage": Types.INTEGER(min=0, max=0xFFFF)
  }]
  component = 'binary_sensor'


  def __init__(self, button_id=0, mask=0, elapsed_deciseconds=0, state=ButtonStates.NO_BUTTON_PRESSED, battery_voltage=0):
    self.button_id = button_id
    self.mask = mask
    self.elapsed_deciseconds = elapsed_deciseconds
    self.state = state
    self.battery_voltage = battery_voltage
    File.__init__(self, CustomFileIds.BUTTON.value, FILE_SIZE)
    Validatable.__init__(self)

  @staticmethod
  def parse(s, offset=0, length=FILE_SIZE):
    button_id = s.read("uint:8")
    mask = s.read("uint:8")
    elapsed_deciseconds = s.read("uint:8")
    state = ButtonStates(int(s.read("uint:8")))
    battery_voltage = s.read("uintle:16")
    return ButtonFile(button_id=button_id, mask=mask, elapsed_deciseconds=elapsed_deciseconds, state=state, battery_voltage=battery_voltage)

  def __iter__(self):
    yield self.button_id
    yield self.mask
    yield self.elapsed_deciseconds
    yield self.state.value
    for byte in bytearray(struct.pack(">H", self.battery_voltage)):
      yield byte


  def __str__(self):
    return "button_id={}, mask={}, elapsed_deciseconds={}, state={}, battery_voltage={}".format(
      self.button_id, self.mask, self.elapsed_deciseconds, self.state, self.battery_voltage
    )