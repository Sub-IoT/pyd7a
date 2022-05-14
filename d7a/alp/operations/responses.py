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

# author: Christophe VG <contact@christophe.vg>
# class implementation of responses
from bitstring import ConstBitStream

from d7a.alp.operands.file_header import FileHeaderOperand
from d7a.alp.operations.operation import Operation

from d7a.alp.operands.file        import Data
from d7a.system_files.system_files import SystemFiles


class ReturnFileData(Operation):
  def __init__(self, custom_files_class=None, *args, **kwargs):
    self.file_type = None
    self.file_data_parsed = None
    self.op     = 32
    self.operand_class = Data
    super(ReturnFileData, self).__init__(*args, **kwargs)
    self.try_parse_file(SystemFiles)
    if custom_files_class is not None:
      self.try_parse_file(custom_files_class)

  def try_parse_file(self, files_class):
    try:
      file_type = files_class().files[files_class.enum_class(int(self.operand.offset.id))]
    except:
      return
    if (file_type is not None) and (file_type.length >= self.operand.length.value):
      self.file_type = file_type
      try:
        self.file_data_parsed = file_type.parse(ConstBitStream(bytearray(self.operand.data)), self.operand.offset.offset.value, self.operand.length.value)
      except:
        self.file_type = None
        self.file_data_parsed = None

class ReturnFileHeader(Operation):
  def __init__(self, *args, **kwargs):
    self.op     = 33
    self.operand_class = FileHeaderOperand
    super(ReturnFileHeader, self).__init__(*args, **kwargs)
