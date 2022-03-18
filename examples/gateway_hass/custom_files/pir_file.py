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

from d7a.support.schema import Validatable, Types
from d7a.system_files.file import File
# from examples.gateway_hass.custom_files.constants import CustomFileIds
from .custom_files import CustomFileIds

FILE_SIZE = 3

class PirFile(File, Validatable):
  SCHEMA = [{
    "pir_state": Types.INTEGER(min=0, max=0xFF),
    "battery_voltage": Types.INTEGER(min=0, max=0xFFFF)
  }]
  component = 'binary_sensor'

  def __init__(self, pir_state=0, battery_voltage=0):
    self.pir_state = pir_state
    self.battery_voltage = battery_voltage
    File.__init__(self, CustomFileIds.PIR.value, FILE_SIZE)
    Validatable.__init__(self)

  @staticmethod
  def parse(s, offset=0, length=FILE_SIZE):
    pir_state = s.read("uint:8")
    battery_voltage = s.read("uintle:16")
    return PirFile(pir_state=pir_state, battery_voltage=battery_voltage)

  def __iter__(self):
    yield self.pir_state
    for byte in bytearray(struct.pack(">H", self.battery_voltage)):
      yield byte


  def __str__(self):
    return "pir_state={}, battery_voltage={}".format(
      self.pir_state, self.battery_voltage
    )