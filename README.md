<!--
Copyright (c) 2015-2021 University of Antwerp, Aloxy NV.

This file is part of pyd7a.
See https://github.com/Sub-IoT/pyd7a for further info.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# DASH7 Python Support
A collection of Python modules, supporting the DASH7 Alliance Protocol in general,
and [Sub-IoT](https://github.com/Sub-Iot/Sub-IoT-Stack) in particular.

## Introduction

This repository contains a collection of Python modules that can help when working with the Dash7 Alliance Wireless Sensor and Actuator Network Protocol.

## Installation

We are currently targeting python v2.7.
Use the following commands to get started:

```bash
$ git clone https://github.com/Sub-IoT/pyd7a.git
$ cd pyd7a
$ sudo pip install -r requirements.txt
```

You can verify that the installation succeeded by running the unit tests:
```bash
$ make test
*** running all tests
.................................................................................................................................
----------------------------------------------------------------------
Ran 129 tests in 1.064s

OK
```
If all tests ran without any errors, you're good to go.

## Modules

### ALP Parser

A parser/generator for Application Layer Protocol commands. From the specification:

"_ALP is the D7A Data Elements API. It is a generic API, optimized for usage with the D7A Session Protocol. It can be encapsulated in any other communication protocol. ALP defines a standard method to manage the Data Elements by the Application.
Any application action, data exchange method or protocol is mapped into manipulation of D7A Data Elements and their properties by means of ALP Commands._"

### DLL Parser

A parser for D7AP frames as transmitted over the air.

### Sub-Iot Serial console interface parser

A parser for frames used by the serial console interface by Sub-IoT-Stack nodes

### Sub-IoT Modem interface

Allows to use a serial connected Sub-IoT-Stack node as a modem. By sending ALP commands you can access the node's filesystem, or use the node's DASH7 interface to access the filesystem of nodes in the network.

## Examples

### Gateway_hass

A gateway script for connecting a dash7 gateway to a running Home Assistant instance using MQTT.
