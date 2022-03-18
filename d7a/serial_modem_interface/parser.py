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

# a parser for ALP commands wrapped in serial interface frames
import binascii

from bitstring                    import ConstBitStream, ReadError
from d7a.alp.parser               import Parser as AlpParser
from d7a.parse_error              import ParseError
import enum
from d7a.support.Crc import calculate_crc
from pprint import pprint



class MessageType(enum.IntEnum):
  ALP_DATA = 1
  PING_REQUEST = 2
  PING_RESPONSE = 3
  LOGGING = 4
  REBOOTED = 5

class Parser(object):

  def __init__(self, skip_alp_parsing=False, custom_files_class=None):
    self.buffer = bytearray()
    self.skip_alp_parsing = skip_alp_parsing
    self.up_counter = 0
    self.down_counter = 0
    self.error_counter = 0
    self.alp_parser = AlpParser(custom_files_class)

  def shift_buffer(self, start):
    self.buffer = self.buffer[start:]
    return self

  def parse(self, msg):
    self.buffer.extend(msg)
    return self.parse_buffer()


#|sync|sync|counter|message type|length|crc1|crc2|
  def build_serial_frame(self,command):
    buffer = bytearray([ 0xC0, 0])
    alp_command_bytes = bytearray(command)
    buffer.append(self.up_counter)
    buffer.append(MessageType.ALP_DATA.value)
    buffer.append(len(alp_command_bytes))
    crc = calculate_crc(bytes(alp_command_bytes))
    buffer = buffer + bytes(bytearray(crc)) + alp_command_bytes
    self.up_counter = self.up_counter + 1
    if self.up_counter > 255:
      self.up_counter = 0
    return buffer


  def parse_buffer(self):
    parsed = 0
    cmds   = []
    errors = []
    message_types = []

    while True:
      (message_type, cmd, info) = self.parse_one_command_from_buffer()
      errors.extend(info["errors"])
      if cmd is None: break
      parsed += info["parsed"]
      message_types.append(message_type)
      cmds.append(cmd)

    info["parsed"] = parsed
    info["errors"] = errors
    return (message_types, cmds, info)

  def parse_one_command_from_buffer(self):
    retry       = True    # until we have one or don't have enough
    errors      = []
    cmd         = None
    message_type = None
    bits_parsed = 0
    while retry and len(self.buffer) > 0:
      try:
        s           = ConstBitStream(bytes=self.buffer)
        cmd_length, message_type = self.parse_serial_interface_header(s)
        if message_type == MessageType.REBOOTED.value:
          cmd = s.read("uint:8")
        elif message_type == MessageType.LOGGING.value:
          cmd = (s.readlist('bytes:b', b=cmd_length)[0])
        else:
          if self.skip_alp_parsing:
            if s.length < cmd_length:
              raise ReadError

            cmd = s.read("bytes:" + str(cmd_length))
          else:
            cmd = self.alp_parser.parse(s, cmd_length)

        bits_parsed = s.pos
        self.shift_buffer(bits_parsed/8)
        retry = False         # got one, carry on
      except ReadError:       # not enough to read, carry on and wait for more
        retry = False
      except Exception as e: # actual problem with current buffer, need to skip
        errors.append({
          "error"   : e.args[0],
          "buffer"  : " ".join(map(lambda b: format(b, "02x"), self.buffer)),
          "pos"     : s.pos,
          "skipped" : self.skip_bad_buffer_content()
        })

    info = {
      "parsed" : bits_parsed,
      "buffer" : len(self.buffer) * 8,
      "errors" : errors
    }
    return (message_type, cmd, info)

  def skip_bad_buffer_content(self):
    # skip until we find 0xc0, which might be a valid starting point
    try:
      self.buffer.pop(0)                      # first might be 0xc0
      pos = self.buffer.index(b'\xc0')
      self.buffer = self.buffer[pos:]
      return pos + 1
    except IndexError:                        # empty buffer
      return 0
    except ValueError:                        # empty buffer, reported by .index
      skipped = len(self.buffer) + 1          # popped first item already
      self.buffer = bytearray()
      return skipped

  # |sync|sync|counter|message type|length|crc1|crc2|
  def parse_serial_interface_header(self, s):
    b = s.read("uint:8")
    if b != 0xC0:
      raise ParseError("expected 0xC0, found {0}".format(b))
    version = s.read("uint:8")
    if version != 0:
      raise ParseError("Expected version 0, found {0}".format(version))
    counter = s.read("uint:8")
    message_type = s.read("uint:8") #TODO different handler?
    cmd_len = s.read("uint:8")
    crc1 = s.read("uint:8")
    crc2 = s.read("uint:8")
    if len(self.buffer) - s.bytepos < cmd_len:
      raise ReadError("ALP command not complete yet, expected {0} bytes, got {1}".format(cmd_len, s.len - s.bytepos))
    payload = s.peeklist('bytes:b', b=cmd_len)[0]
    crc = calculate_crc(bytes(payload))
    self.down_counter = self.down_counter + 1
    if self.down_counter > 255:
      self.down_counter = 0
    if counter != self.down_counter:
      self.error_counter += 1
      pprint("counters not equal") #TODO consequence?
      self.down_counter = counter #reset counter
    if crc[0] != crc1 or crc[1] != crc2:
      raise ParseError("CRC is incorrect found {} {} and expected {} {}".format(crc1, crc2, crc[0], crc[1]))

    return cmd_len, message_type

