#!/usr/bin/env python

import argparse
import os
from time import sleep
import sys
import logging

from d7a.alp.command import Command
from d7a.alp.interface import InterfaceType
from d7a.d7anp.addressee import Addressee, IdType
from d7a.dll.access_profile import AccessProfile
from d7a.dll.sub_profile import SubProfile
from d7a.phy.channel_id import ChannelID
from d7a.phy.subband import SubBand
from d7a.sp.configuration import Configuration
from d7a.sp.qos import QoS, ResponseMode
from d7a.system_files.access_profile import AccessProfileFile
from d7a.system_files.uid import UidFile
from d7a.system_files.engineering_mode import EngineeringModeFile, EngineeringModeMode
from d7a.system_files.system_file_ids import SystemFileIds
from d7a.phy.channel_header import ChannelHeader,ChannelCoding,ChannelClass,ChannelBand
from modem.modem import Modem

# This example can be used with a node running the gateway app included in OSS-7, which is connect using the supplied serial device.
# It will query the sensor file (file 0x40) from other nodes running sensor_pull, using adhoc synchronization and print the results.
from util.logger import configure_default_logger

waiting_for_requests = 0

def received_command_callback(cmd):
  global waiting_for_requests
  logging.info(cmd)
  if cmd.execution_completed:
    waiting_for_requests -= 1
    if waiting_for_requests <= 0:
      os._exit(0)

argparser = argparse.ArgumentParser()
argparser.add_argument("-d", "--device", help="serial device /dev file modem",
                            default="/dev/ttyUSB0")
argparser.add_argument("-r", "--rate", help="baudrate for serial device", type=int, default=115200)
argparser.add_argument("-v", "--verbose", help="verbose", default=False, action="store_true")
argparser.add_argument("-c", "--channel-id", help="for example 868LP000 ; format FFFRCIII where FFF={433, 868, 915}, R={L, N, H, R (LORA)}, C={P (PN9), F (FEC), C (CW)} III=000...280", default="868LP000")
modes = ["OFF", "CONT_TX", "TRANSIENT_TX", "PER_RX", "PER_TX"]
argparser.add_argument("-m", "--mode", choices=modes, required=True)
argparser.add_argument("-e", "--eirp", help="EIRP in dBm", type=int, default=0)
argparser.add_argument("-t", "--timeout", help="timeout", type=int, default=0)
config = argparser.parse_args()
configure_default_logger(config.verbose)

ch = ChannelID.from_string(config.channel_id)
print("Using mode {} for channel {} with TX EIRP {} dBm".format(config.mode, config.channel_id, config.eirp))
mode = EngineeringModeMode.from_string(config.mode)

modem = Modem(config.device, config.rate, unsolicited_response_received_callback=received_command_callback)
modem.connect()

emFile = EngineeringModeFile(mode=mode, flags=0, timeout=config.timeout, channel_id=ch, eirp=config.eirp)

modem.execute_command(
  alp_command=Command.create_with_write_file_action(
    file_id=5,
    data=list(emFile),
  )
)


try:
  while True:
    sleep(5)
except KeyboardInterrupt:
  sys.exit(0)
