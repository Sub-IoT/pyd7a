#!/usr/bin/env python
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
import time

from datetime import datetime

import struct
from threading import Thread
import threading

import logging
import serial
from bitstring import ConstBitStream

from d7a.alp.operands.file import DataRequest
from d7a.alp.operands.length import Length
from d7a.alp.operands.offset import Offset
from d7a.alp.operations.requests import ReadFileData
from d7a.alp.operations.responses import ReturnFileData
from d7a.alp.regular_action import RegularAction
from d7a.serial_modem_interface.parser import Parser, MessageType

from d7a.alp.command import Command
from d7a.system_files.firmware_version import FirmwareVersionFile
from d7a.system_files.uid import UidFile

from d7a.system_files.system_file_ids import SystemFileIds

class Modem:
  def __init__(self, device, baudrate, unsolicited_response_received_callback=None, rebooted_callback=None, skip_alp_parsing=False, custom_files_class=None):
    self.log = logging.getLogger(__name__)
    self.parser = Parser(skip_alp_parsing, custom_files_class)
    self.config = {
      "device"   : device,
      "baudrate" : baudrate
    }
    self.lock=threading.Lock()
    self.uid = None
    self.firmware_version = None
    self.skip_alp_parsing = skip_alp_parsing
    self._sync_execution_response_cmds = []
    self._sync_execution_tag_id = None
    self._sync_execution_completed = False
    self._unsolicited_responses_received = []
    self._rebooted_received = []
    self._read_async_active = False
    self.unsolicited_response_received_callback = unsolicited_response_received_callback
    self.rebooted_callback = rebooted_callback
    self.connected = False
    self.dev = serial.Serial(
      port     = self.config["device"],
      baudrate = self.config["baudrate"],
      timeout  = None,
      parity = serial.PARITY_NONE,
      stopbits = serial.STOPBITS_ONE,
      bytesize = serial.EIGHTBITS,
      xonxoff = False,
      rtscts = False,
      dsrdtr = False,
      exclusive = True,
    )

    self.dev.flush() # ignore possible buffered data

    self.start_reading()

  def connect(self, check_alive=True):
    if self.connected:
      return

    if not check_alive:
      self.connected = True
      return True

    read_modem_info_action = Command.create_with_read_file_action_system_file(UidFile())
    read_modem_info_action.add_action(
      RegularAction(
        operation=ReadFileData(
          operand=DataRequest(
            offset=Offset(id=FirmwareVersionFile().id, offset=Length(0)),  # TODO offset size
            length=FirmwareVersionFile().length
          )
        )
      )
    )

    if self.skip_alp_parsing:
      self.log.info("Running in skip_alp_parsing mode, not checking if we can receive the modem's UID")
      self.connected = True
      self.execute_command_async(read_modem_info_action)
      return True

    resp_cmd = self.execute_command(read_modem_info_action, timeout_seconds=10)

    if len(resp_cmd) == 0:
      self.log.warning("Timed out reading node information")
      return False

    for action in resp_cmd[0].actions:
      if type(action) is RegularAction and type(action.operation) is ReturnFileData:
          if action.operand.offset.id == SystemFileIds.UID.value:
            self.uid = '{:x}'.format(struct.unpack(">Q", str(bytearray(action.operand.data)))[0])
          if action.operand.offset.id == SystemFileIds.FIRMWARE_VERSION.value:
            self.firmware_version = FirmwareVersionFile.parse(ConstBitStream(bytearray(action.operand.data)), action.operand.offset.offset.value, action.operand.length.value)

    if self.uid and self.firmware_version:
      self.connected = True


    if self.connected:
      self.log.info("connected to {}, node UID {} running D7AP v{}, application \"{}\" with git sha1 {}".format(
        self.config["device"], self.uid, self.firmware_version.d7ap_version,
        self.firmware_version.application_name, self.firmware_version.git_sha1)
      )
      return True
    else:
      return False


  def execute_command_async(self, alp_command):
    self.execute_command(alp_command, timeout_seconds=0)

  def execute_command(self, alp_command, timeout_seconds=10):
    if self.skip_alp_parsing:
      self.log.info("Running in skip_alp_parsing mode, execute_command() synchronously is not possible in this mode,"
                    "executing async instead ")
      timeout_seconds = 0

    data = self.parser.build_serial_frame(alp_command)
    self._sync_execution_response_cmds = []
    self._sync_execution_tag_id = None
    self._sync_execution_completed = False
    if(timeout_seconds > 0):
      assert self._sync_execution_tag_id is None
      self._sync_execution_tag_id = alp_command.tag_id
    with self.lock:
      self.dev.write(data)
      self.dev.flush()
    self.log.info("Sending command of size %s" % len(data))
    self.log.debug("> " + " ".join(map(lambda b: format(b, "02x"), data)))
    if timeout_seconds == 0:
      return []

    self.log.info("Waiting for response (max {} s)".format(timeout_seconds))
    start_time = datetime.now()
    while not self._sync_execution_completed and (datetime.now() - start_time).total_seconds() < timeout_seconds:
      time.sleep(0.05)

    if not self._sync_execution_completed:
      self.log.info("Command timeout (tag {})".format(alp_command.tag_id))
      return []

    return self._sync_execution_response_cmds


  def start_reading(self):
    self._read_async_active = True
    self.read_thread = Thread(target=self._read_async)
    self.read_thread.daemon = True
    self.read_thread.start()

  def stop_reading(self):
    self._read_async_active = False
    self.dev.cancel_read()
    self.read_thread.join()

  def get_unsolicited_responses_received(self):
    return self._unsolicited_responses_received

  def clear_unsolicited_responses_received(self):
    self._unsolicited_responses_received = []

  def get_rebooted_received(self):
    return self._rebooted_received

  def clear_rebooted_received(self):
    self._rebooted_received = []

  def _read_async(self):
    self.log.info("starting read thread")
    data_received = bytearray()
    while self._read_async_active:
      try:
        data_received = self.dev.read()
      except serial.SerialException as e:
        self.log.warning("SerialException {} received, trying to reconnect".format(e.errno))
        self.dev.close()
        time.sleep(5)
        self.dev.open()

      if len(data_received) > 0:
        # self.log.debug("< " + " ".join(map(lambda b: format(b, "02x"), bytearray(data_received))))
        (message_types, cmds, info) = self.parser.parse(data_received)
        for error in info["errors"]:
          error["buffer"] = " ".join(map(lambda b: format(b, "02x"), bytearray(data_received)))
          self.log.warning("Parser error: {}".format(error))
        cmd_cnt = 0
        for cmd in cmds:
          if not self.skip_alp_parsing and hasattr(cmd, 'tag_id') and self._sync_execution_tag_id != None and self._sync_execution_tag_id == cmd.tag_id and message_types[cmd_cnt] <= MessageType.PING_RESPONSE:
            self.log.info("Received response for sync execution")
            self._sync_execution_response_cmds.append(cmd)
            if cmd.execution_completed:
              self.log.info("cmd with tag {} done".format(cmd.tag_id))
              self._sync_execution_completed = True
            else:
              self.log.info("cmd with tag {} not done yet, expecting more responses".format(cmd.tag_id))

          elif self.unsolicited_response_received_callback != None and self.connected and message_types[cmd_cnt] <= MessageType.PING_RESPONSE: # skip responses until connected
            self.unsolicited_response_received_callback(cmd)
          elif message_types[cmd_cnt] == MessageType.REBOOTED:
            if self.rebooted_callback != None:
              self.rebooted_callback(cmd)
            else:
              self._rebooted_received.append(cmd)
          elif  message_types[cmd_cnt] == MessageType.LOGGING:
            self.log.info("logging: {}".format(cmd))
          elif message_types[cmd_cnt] <= MessageType.PING_RESPONSE:
            self.log.info("Received a response which was not requested synchronously or no async callback provided")
            self._unsolicited_responses_received.append(cmd)
          cmd_cnt += 1

    self.log.info("end read thread")


class ModemConnectionError(Exception):
  pass
