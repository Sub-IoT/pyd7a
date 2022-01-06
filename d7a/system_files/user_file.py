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

from d7a.system_files.file import File

class UserFile(File):

  def __init__(self, file_id, bytes=[], name="UserFile"):
    self.file_id = file_id
    self.bytes = bytes
    self.name = name
    File.__init__(self, file_id, len(bytes))

  def __iter__(self):
    for byte in bytearray(self.bytes):
      yield byte

