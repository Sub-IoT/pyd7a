#!/usr/bin/env python
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

import argparse
from d7a.alp.tag_request_action import TagRequestAction
import sys
import logging
import time
import signal

from d7a.alp.command import Command
from d7a.alp.interface import InterfaceType
from d7a.alp.operands.file import Data
from d7a.alp.operands.length import Length
from d7a.alp.operands.offset import Offset
from d7a.alp.operations.write_operations import WriteFileData
from d7a.alp.operands.file import DataRequest
from d7a.alp.operations.requests import ReadFileData
from d7a.alp.regular_action import RegularAction
from d7a.d7anp.addressee import Addressee, IdType
from d7a.alp.operations.tag_request import TagRequest
from d7a.alp.operands.tag_id import TagId

from d7a.phy.channel_id import ChannelID
from d7a.sp.configuration import Configuration
from d7a.sp.qos import ResponseMode, QoS, RetryMode
from d7a.system_files.engineering_mode import EngineeringModeFile, EngineeringModeMode
from d7a.system_files.factory_settings import FactorySettingsFile
from d7a.types.ct import CT

from modem.modem import Modem

from util.logger import configure_default_logger


def received_command_callback(cmd):
  logging.info("> " + " ".join(map(lambda b: format(b, "02x"), bytearray(cmd))))


def rebooted_callback(cmd):
  global stop
  logging.info("modem rebooted with reason {}".format(cmd))
  stop = True


argparser = argparse.ArgumentParser()
argparser.add_argument("-d", "--device", help="serial device /dev file modem",
                            default="/dev/ttyUSB0")
argparser.add_argument("-r", "--rate", help="baudrate for serial device", type=int, default=115200)
argparser.add_argument("-v", "--verbose", help="verbose", default=False, action="store_true")
argparser.add_argument("-p", "--period", help="period of monitoring", type=int, default=60)
config = argparser.parse_args()
configure_default_logger(config.verbose)

modem = Modem(config.device, config.rate, unsolicited_response_received_callback=received_command_callback,
              rebooted_callback=rebooted_callback, skip_alp_parsing=False)

status = 0
modem_period = config.period + 10

cmd = Command()
cmd.add_action(
  RegularAction(
    operation=ReadFileData(
      operand=DataRequest(
        offset=Offset(id=50, offset=Length(0)),
        length=17
      )
    )
  )
)

answ = modem.execute_command(cmd)
for answer in answ:
  print(answer)

