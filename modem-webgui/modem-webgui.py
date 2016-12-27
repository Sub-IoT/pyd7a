#!/usr/bin/env python
import argparse
import json

import eventlet
import sys

from datetime import time, datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

from d7a.alp.command import Command
from d7a.alp.interface import InterfaceType
from d7a.d7anp.addressee import IdType, Addressee
from d7a.sp.configuration import Configuration
from d7a.sp.qos import QoS, ResponseMode
from d7a.system_files.system_files import SystemFiles
from d7a.system_files.system_file_ids import SystemFileIds
from modem.modem import Modem

app = Flask(__name__, static_url_path='/static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 # do not cache static assets for now

socketio = SocketIO(app)
eventlet.monkey_patch()
modem = None


@app.route('/')
def index():
  return render_template('index.html',
                         systemfiles=SystemFiles().get_all_system_files(),
                         qos_response_modes=ResponseMode.__members__,
                         id_types=IdType.__members__)

@app.route('/systemfiles')
def get_system_files():
  options = []
  for id, file in SystemFiles().get_all_system_files().iteritems():
    options.append({"id": id.value, "value": id.name  })

  return jsonify(options)

@app.route('/idtypes')
def get_id_types():
  id_types = []
  for name, member in IdType.__members__.items():
    id_types.append({'id': member.value, 'value': name})

  return jsonify(id_types)

@app.route('/responsemodes')
def get_response_modes():
  response_modes = []
  for name, member in ResponseMode.__members__.items():
    response_modes.append({"id": member.value, "value": name})

  return jsonify(response_modes)

@socketio.on('execute_raw_alp')
def on_execute_raw_alp(data):
  alp_hex_string = data['raw_alp'].replace(" ", "").strip()
  modem.send_command(bytearray(alp_hex_string.decode("hex")))

@socketio.on('read_local_system_file')
def on_read_local_system_file(data):
  print("read local system file")
  modem.send_command(
    Command.create_with_read_file_action_system_file(SystemFiles.files[SystemFileIds(int(data['system_file_id']))])
  )

@socketio.on('read_local_file')
def on_read_local_file(data):
  print("read_local_file")
  cmd = Command.create_with_read_file_action(
    file_id=int(data['file_id']),
    offset=int(data['offset']),
    length=int(data['length'])
  )

  modem.send_command(cmd)

@socketio.on('execute_command')
def execute_command(data):
  print("execute_command")
  print data

  interface_configuration = None
  interface_type = InterfaceType(int(data["interface"]))
  if interface_type == InterfaceType.D7ASP:
    id_type = IdType(int(data["id_type"]))
    id = int(data["id"])
    if id_type == IdType.NOID:
      id = None

    interface_configuration = Configuration(
      qos=QoS(resp_mod=ResponseMode(int(data["qos_response_mode"]))),
      addressee=Addressee(
        access_class=int(data["access_class"]),
        id_type=id_type,
        id=id
      )
    )

  cmd = Command.create_with_read_file_action(
    interface_type=interface_type,
    interface_configuration=interface_configuration,
    file_id=int(data["file_id"]),
    offset=int(data["offset"]),
    length=int(data["length"])
  )

  modem.send_command(cmd)
  return {'tag_id': cmd.tag_id}


@socketio.on('connect')
def on_connect():
  global modem
  if modem == None:
    modem = Modem(config.device, config.rate, command_received_callback)
    modem.start_reading()

  print("modem: " + str(modem.uid))
  emit('module_info', {
    'uid': hex(modem.uid),
    'application_name': modem.firmware_version.application_name,
    'git_sha1': modem.firmware_version.git_sha1,
    'd7ap_version': modem.firmware_version.d7ap_version
  }, broadcast=True)


@socketio.on('disconnect')
def on_disconnect():
  print('Client disconnected', request.sid)


def command_received_callback(cmd):
  print("cmd received: {}".format(cmd))
  with app.test_request_context('/'):
    socketio.emit("received_alp_command", {'ts': datetime.now().isoformat(), 'cmd': str(cmd)}, broadcast=True)
    print("broadcasted recv command")

@socketio.on_error_default
def default_error_handler(e):
  print("Error {} in {} with args".format(e, request.event["message"], request.event["args"]))

if __name__ == '__main__':
  argparser = argparse.ArgumentParser()
  argparser.add_argument("-d", "--device", help="serial device /dev file modem",
                         default="/dev/ttyUSB0")
  argparser.add_argument("-r", "--rate", help="baudrate for serial device", type=int, default=115200)
  argparser.add_argument("-p", "--port", help="TCP port used by webserver", type=int, default=5000)
  config = argparser.parse_args()
  modem = None
  socketio.run(app, debug=True, host="0.0.0.0", port=config.port)
