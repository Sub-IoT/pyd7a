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
# unit tests for D7A ALP responses

import unittest
import sys

from d7a.alp.operations.responses import ReturnFileData
from d7a.alp.operands.file        import Data

class TestReturnFileData(unittest.TestCase):
  def test_constructor_and_op_code(self):
    data = Data([0x01, 0x02, 0x03, 0x04])
    rfd  = ReturnFileData(operand=data)
    self.assertEqual(rfd.op, 32)
    self.assertIs(rfd.operand, data)
    self.assertEqual(rfd.operand.length.value, 4)
  
  def test_byte_generation(self):
    data  = Data([0x01, 0x02, 0x03, 0x04])
    rfd   = ReturnFileData(operand=data)
    bytes = bytearray(rfd)
    self.assertEqual(len(bytes), 7)
    self.assertEqual(bytes[0], int('00000000', 2)) # offset
    self.assertEqual(bytes[1], int('00000000', 2)) # offset
    self.assertEqual(bytes[2], int('00000100', 2)) # length = 4
    self.assertEqual(bytes[3], int('00000001', 2))
    self.assertEqual(bytes[4], int('00000010', 2))
    self.assertEqual(bytes[5], int('00000011', 2))
    self.assertEqual(bytes[6], int('00000100', 2))

if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(TestNoOperation)
  unittest.TextTestRunner(verbosity=2).run(suite)
