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

import argparse

import logging
import platform
import signal
import sys
import traceback

import time
import json



from examples.gateway_hass.custom_files.custom_files import CustomFiles
from examples.gateway_hass.custom_files.button_file import ButtonFile
from examples.gateway_hass.custom_files.pir_file import PirFile

import paho.mqtt.client as mqtt

from modem.modem import Modem
from util.logger import configure_default_logger


class Modem2Mqtt():

  def __init__(self):
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-d", "--device", help="serial device /dev file modem",
                           default="/dev/ttyACM0")
    argparser.add_argument("-r", "--rate", help="baudrate for serial device", type=int, default=115200)
    argparser.add_argument("-v", "--verbose", help="verbose", default=False, action="store_true")
    argparser.add_argument("-b", "--broker", help="mqtt broker hostname",
                             default="homeassistant.local")

    self.config = argparser.parse_args()
    configure_default_logger(self.config.verbose)

    self.modem = Modem(self.config.device, self.config.rate, self.on_command_received, custom_files_class=CustomFiles)
    self.modem.connect()
    self.connect_to_mqtt()


  def connect_to_mqtt(self):
    self.connected_to_mqtt = False

    self.mq = mqtt.Client("", True, None, mqtt.MQTTv31)
    self.mq.on_connect = self.on_mqtt_connect
    self.mq.on_publish = self.on_published
    # self.mq.on_message = self.on_mqtt_message
    self.mq.username_pw_set("shelly", "shelly_password")

    self.mq.connect(self.config.broker, 1883, 60)
    self.mq.loop_start()
    while not self.connected_to_mqtt: pass  # busy wait until connected
    logging.info("Connected to MQTT broker on {}".format(
      self.config.broker
    ))

  def on_mqtt_connect(self, client, config, flags, rc):
    # self.mq.subscribe(self.mqtt_topic_outgoing)
    self.connected_to_mqtt = True

  def on_mqtt_message(self, client, config, msg):
    # downlink is currently not handled yet
    logging.info("gotten downlink {}".format(msg.payload))
    

  def __del__(self): # pragma: no cover
    try:
      self.mq.loop_stop()
      self.mq.disconnect()
    except: pass

  def on_published(self, client, userdata, mid):
    logging.info("published message with id {} successfully".format(mid))

  def on_command_received(self, cmd):
    try:
      transmitter = cmd.interface_status.operand.interface_status.addressee.id
      transmitterHexString = hex(transmitter)[2:-1]
      operation = cmd.actions[0].operation
      if operation.file_type is None or operation.file_data_parsed is None:
        logging.info("received random data: {} from {}".format(operation.operand.data, transmitterHexString))
        return
      fileType = operation.file_type
      parsedData = operation.file_data_parsed
      logging.info("Received {} content: {} from {}".format(fileType.__class__.__name__,
                                              parsedData, transmitterHexString))


      if fileType.__class__ is ButtonFile:
        unique_id = '{}_button{}'.format(transmitterHexString, parsedData.button_id)
        state_topic = 'homeassistant/{}/{}/state'.format(parsedData.component, unique_id)
        config_topic = 'homeassistant/{}/{}/config'.format(parsedData.component, unique_id)
        device = {
            'manufacturer': 'Kwiam',
            'name': 'Push7_{}'.format(transmitterHexString),
            'identifiers': [transmitterHexString],
            # 'sw_version' : could read from version file
        }
        config = {
          'device': device,
          # 'icon': we could choose a custom icon
          # 'json_attributes_topic': ?
          'name': 'Button_{}'.format(parsedData.button_id),
          'qos': 1,
          'unique_id': unique_id,
          'state_topic': state_topic
        }
        self.mq.publish(config_topic, json.dumps(config))
        self.mq.publish(state_topic, 'ON' if (1 << parsedData.button_id) & parsedData.state.value else 'OFF')

        logging.info("published state: {} to topic {}".format('ON' if (1 << parsedData.button_id) & parsedData.state.value else 'OFF', state_topic))
        
        unique_voltage_id = '{}_voltage'.format(transmitterHexString)
        battery_voltage_state_topic = 'homeassistant/sensor/{}/state'.format(unique_voltage_id)
        battery_voltage_config_topic = 'homeassistant/sensor/{}/config'.format(unique_voltage_id)
        battery_voltage_config = {
          'device': device,
          'name': 'Voltage',
          'qos': 1,
          'unique_id': unique_voltage_id,
          'entity_category': 'diagnostic',
          'state_topic': battery_voltage_state_topic,
          'state_class': 'measurement',
          'unit_of_measurement': 'mV',
          'icon': 'mdi:sine-wave'
        }
        self.mq.publish(battery_voltage_config_topic, json.dumps(battery_voltage_config))
        self.mq.publish(battery_voltage_state_topic, parsedData.battery_voltage)

      if fileType.__class__ is PirFile:

        device = {
            'manufacturer': 'Kwiam',
            'name': 'Push7_{}'.format(transmitterHexString),
            'identifiers': [transmitterHexString],
            # 'sw_version' : could read from version file
        }

        unique_id = '{}_pir'.format(transmitterHexString)
        state_topic = 'homeassistant/button/{}/state'.format(parsedData.component, unique_id)
        config_topic = 'homeassistant/{}/{}/config'.format(parsedData.component, unique_id)

        config = {
          'device': device,
          # 'icon': we could choose a custom icon
          # 'json_attributes_topic': ?
          'name': 'Pir_state',
          'qos': 1,
          'unique_id': unique_id,
          'state_topic': state_topic
        }
        self.mq.publish(config_topic, json.dumps(config))
        self.mq.publish(state_topic, 'ON' if (parsedData.pir_state) else 'OFF')
        
        unique_voltage_id = '{}_voltage'.format(transmitterHexString)
        battery_voltage_state_topic = 'homeassistant/sensor/{}/state'.format(unique_voltage_id)
        battery_voltage_config_topic = 'homeassistant/sensor/{}/config'.format(unique_voltage_id)
        battery_voltage_config = {
          'device': device,
          'name': 'Voltage',
          'qos': 1,
          'unique_id': unique_voltage_id,
          'entity_category': 'diagnostic',
          'state_topic': battery_voltage_state_topic,
          'state_class': 'measurement',
          'unit_of_measurement': 'mV',
          'icon': 'mdi:sine-wave'
        }
        self.mq.publish(battery_voltage_config_topic, json.dumps(battery_voltage_config))
        self.mq.publish(battery_voltage_state_topic, parsedData.battery_voltage)



      # data = cmd.actions[0].operation.operand.data
      # logging.info("Command received: binary ALP (size {})".format(len(data)))

      # temperature = (data[0] * 0x100 + data[1]) / 10.0
      # result_temperature = {'active': 'ON', 'Temperature': temperature}
      # result_json_temperature = json.dumps(result_temperature)

      # led_status = data[2] != 0
      # result_led_status = {'state': 'ON' if led_status else 'OFF'}
      # result_json_led_status = json.dumps(result_led_status)

      # logging.info("Gotten temperature {} and led is {}".format(temperature, "on" if led_status else "off"))

      # #pass temperature and led status to seperate topics. This can also be done to the same topic
      # self.mq.publish(self.mqtt_topic_temperature, result_json_temperature)
      # self.mq.publish(self.mqtt_topic_led_status, result_json_led_status)
    except (AttributeError, IndexError):
      # probably an answer on downlink we don't care about right now
      return
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
      trace = "".join(lines)
      logging.error("Exception while processing command: \n{}".format(trace))

  def run(self):
    logging.info("Started")
    keep_running = True
    while keep_running:
      try:
        if platform.system() == "Windows":
          time.sleep(1)
        else:
          signal.pause()
      except KeyboardInterrupt:
        logging.info("received KeyboardInterrupt... stopping processing")
        keep_running = False

if __name__ == "__main__":
  Modem2Mqtt().run()
