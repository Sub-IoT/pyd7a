#
# Copyright (c) 2015-2019 University of Antwerp, Aloxy NV.
#
# This file is part of pyd7a
# (see https://github.com/MOSAIC-LoPoW/pyd7a).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

# author: Christophe VG <contact@christophe.vg>
# class for representing compressed time

# The compressed time format allows compressing to 1 byte a time duration ranged
# from 0 to 507904 Ti (0 to 496 s) with variable Ti resolution. It can be 
# converted to Ti using the following formula: T = (4^EXP)x(MANT) Ti

import math

from cerberus import Validator

# Compressed Time
#
# b7-b5 EXP   Exponent (ranging from 0 to 7)
# b4-b0 MANT  Mantissa (ranging from 0 to 31)

from d7a.support.schema import Validatable
  
class CT(Validatable):
  
  SCHEMA = [{
    "exp"  : { "type": "integer", "min" : 0, "max":  7 },
    "mant" : { "type": "integer", "min" : 0, "max": 31 }
  }]

  def __init__(self, exp=0, mant=0):
    self.exp  = exp
    self.mant = mant
    super(CT, self).__init__()

  def __int__(self):
    return int(math.pow(4, self.exp) * self.mant)

  def __iter__(self):
    yield self.compressed_value()

  def compressed_value(self):
    byte = 0
    byte |= self.exp << 5
    byte += self.mant
    return byte

  @staticmethod
  def parse(s):
    exp  = s.read("uint:3")
    mant = s.read("uint:5")
    return CT(exp=exp, mant=mant)

  @staticmethod
  def compress(value, ceil=True):
    for i in range(8):
      if(value <= math.pow(4, i) * 31):
        mantissa = int(value / math.pow(4, i))
        remainder = value % math.pow(4, i)

        if(ceil and remainder):
          mantissa = mantissa + 1
        return CT(i, mantissa)

  def decompress(self):
    return int(math.pow(4, (self.compressed_value() >> 5))) * (self.compressed_value() & 0b11111)

  def __str__(self):
    return "exp={} mant{}".format(self.exp, self.mant)