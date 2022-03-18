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
# a parser for ALP commands
import struct

from d7a.alp.command              import Command
from d7a.alp.forward_action import ForwardAction
from d7a.alp.indirect_forward_action import IndirectForwardAction
from d7a.alp.interface import InterfaceType
from d7a.alp.operands.file_header import FileHeaderOperand
from d7a.alp.operands.indirect_interface_operand import IndirectInterfaceOperand
from d7a.alp.operands.interface_configuration import InterfaceConfiguration
from d7a.alp.operands.interface_status import InterfaceStatusOperand
from d7a.alp.operands.length import Length
from d7a.alp.operands.lorawan_interface_configuration_abp import LoRaWANInterfaceConfigurationABP
from d7a.alp.operands.lorawan_interface_configuration_otaa import LoRaWANInterfaceConfigurationOTAA
from d7a.alp.operands.query import QueryOperand
from d7a.alp.operations.break_query import BreakQuery
from d7a.alp.operations.forward import Forward
from d7a.alp.operations.indirect_forward import IndirectForward
from d7a.alp.operations.status import InterfaceStatus
from d7a.alp.operations.tag_response import TagResponse
from d7a.alp.operations.write_operations import WriteFileData
from d7a.alp.status_action import StatusAction, StatusActionOperandExtensions
from d7a.alp.regular_action import RegularAction
from d7a.alp.operations.responses import ReturnFileData, ReturnFileHeader
from d7a.alp.operations.requests  import ReadFileData
from d7a.alp.operands.file        import Data, DataRequest
from d7a.alp.operands.offset import Offset
from d7a.alp.tag_response_action import TagResponseAction
from d7a.parse_error              import ParseError
from d7a.sp.configuration import Configuration
from d7a.sp.status import Status
from d7a.d7anp.addressee import Addressee
from d7a.types.ct import CT
from d7a.alp.operands.tag_id import TagId
from d7a.alp.operations.tag_request import TagRequest
from d7a.alp.tag_request_action import TagRequestAction
from d7a.phy.channel_header import ChannelHeader
from d7a.alp.operations.file_management import CreateNewFile


class Parser(object):
  def __init__(self, custom_files_class = None):
    self.custom_files_class = custom_files_class

  def parse(self, s, cmd_length):
    actions = []
    if cmd_length != 0:
      alp_bytes_parsed = 0
      while alp_bytes_parsed < cmd_length:
        startpos = s.bytepos
        action = self.parse_alp_action(s)
        actions.append(action)
        alp_bytes_parsed = alp_bytes_parsed + (s.bytepos - startpos)

    cmd = Command(actions = actions, generate_tag_request_action=False)
    return cmd

  def parse_alp_action(self, s):
    # meaning of first 2 bits depend on action opcode
    b7 = s.read("bool")
    b6 = s.read("bool")
    op = s.read("uint:6")
    try:
      return{
        1  :  self.parse_alp_read_file_data_action,
        4  :  self.parse_alp_write_file_data_action,
        9  :  self.parse_break_query_action,
        17 :  self.parse_alp_create_file_action,
        32 :  self.parse_alp_return_file_data_action,
        33 :  self.parse_alp_return_file_header_action,
        34 :  self.parse_alp_return_status_action,
        35 :  self.parse_tag_response_action,
        50 :  self.parse_forward_action,
        51 :  self.parse_indirect_forward_action,
        52 :  self.parse_tag_request_action
      }[op](b7, b6, s)
    except KeyError:
      raise ParseError("alp_action " + str(op) + " is not implemented")

  def parse_alp_read_file_data_action(self, b7, b6, s):
    operand = self.parse_alp_file_data_request_operand(s)
    return RegularAction(group=b7,
                  resp=b6,
                  operation=ReadFileData(operand=operand))

  def parse_alp_write_file_data_action(self, b7, b6, s):
    operand = self.parse_alp_return_file_data_operand(s)
    return RegularAction(group=b7,
                  resp=b6,
                  operation=WriteFileData(operand=operand))

  def parse_alp_file_data_request_operand(self, s):
    offset = self.parse_offset(s)
    length = Length.parse(s)
    return DataRequest(length=length.value, offset=offset)

  def parse_break_query_action(self, b7, b6, s):
    return RegularAction(group=b7, resp=b6, operation=BreakQuery(operand=QueryOperand.parse(s)))

  def parse_alp_create_file_action(self, b7, b6, s):
    operand = FileHeaderOperand.parse(s)
    return RegularAction(group=b7,
                         resp=b6,
                         operation=CreateNewFile(operand=operand))

  def parse_alp_return_file_data_action(self, b7, b6, s):
    operand = self.parse_alp_return_file_data_operand(s)
    return RegularAction(group=b7,
                        resp=b6,
                        operation=ReturnFileData(custom_files_class=self.custom_files_class, operand=operand))

  def parse_alp_return_file_header_action(self, b7, b6, s):
    operand = FileHeaderOperand.parse(s)
    return RegularAction(group=b7,
                        resp=b6,
                        operation=ReturnFileHeader(operand=operand))

  def parse_alp_return_file_data_operand(self, s):
    offset = self.parse_offset(s)
    length = Length.parse(s)
    data   = s.read("bytes:" + str(length.value))
    return Data(offset=offset, data=map(ord,data))

  def parse_alp_return_status_action(self, b7, b6, s):
    if b7:
      raise ParseError("Status Operand extension 2 and 3 is RFU")

    if b6: # interface status
      interface_id = s.read("uint:8")
      length = s.read("uint:8")
      try:
        interface_status_operation = {
          0x00: self.parse_alp_interface_status_host,
          0xD7: self.parse_alp_interface_status_d7asp,
          0x01: self.parse_alp_interface_status_serial
        }[interface_id](s, length)
        return StatusAction(operation=interface_status_operation,
                            status_operand_extension=StatusActionOperandExtensions.INTERFACE_STATUS)
      except KeyError:
        raise ParseError("Received ALP Interface status for interface " + str(interface_id) + " which is not implemented")
    else: # action status
      pass # TODO

  def parse_tag_request_action(self, b7, b6, s):
    if b6:
      raise ParseError("bit 6 is RFU")

    tag_id = s.read("uint:8")
    return TagRequestAction(respond_when_completed=b7, operation=TagRequest(operand=TagId(tag_id=tag_id)))

  def parse_tag_response_action(self, b7, b6, s):
    tag_id = s.read("uint:8")
    return TagResponseAction(eop=b7, error=b6, operation=TagResponse(operand=TagId(tag_id=tag_id)))

  def parse_indirect_forward_action(self, b7, b6, s):
    interface_file_id = int(s.read("uint:8"))
    overload = b7
    overload_config = None
    if overload:
      # TODO we are assuming D7ASP interface here
      overload_config = Addressee.parse(s)

    return IndirectForwardAction(overload=overload, resp=b6, operation=IndirectForward(
      operand=IndirectInterfaceOperand(interface_file_id=interface_file_id, interface_configuration_overload=overload_config)))

  def parse_forward_action(self, b7, b6, s):
    if b7:
      raise ParseError("bit 7 is RFU")

    interface_id = InterfaceType(int(s.read("uint:8")))
    interface_config = None
    if(interface_id == InterfaceType.D7ASP):
      interface_config = Configuration.parse(s)
    elif(interface_id == InterfaceType.SERIAL):
      pass # no interface config
    elif(interface_id == InterfaceType.LORAWAN_ABP):
      interface_config = LoRaWANInterfaceConfigurationABP.parse(s)
    elif (interface_id == InterfaceType.LORAWAN_OTAA):
      interface_config = LoRaWANInterfaceConfigurationOTAA.parse(s)
    else:
      assert(False)

    return ForwardAction(resp=b6, operation=Forward(operand=InterfaceConfiguration(interface_id=interface_id,
                                                                                   interface_configuration=interface_config)))
  def parse_alp_interface_status_host(self, s, length):
    pass # no interface status defined for host interface

  def parse_alp_interface_status_d7asp(self, s, length):
    status = None
    if length > 0:
      status = Status.parse(s)

    return InterfaceStatus(
      operand=InterfaceStatusOperand(interface_id=0xd7, interface_status=status)
    )

  def parse_alp_interface_status_serial(self, s, length):
    return InterfaceStatus(operand=InterfaceStatusOperand(interface_id=0x01, interface_status=None))

  def parse_offset(self, s):
    return Offset.parse(s)
