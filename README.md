# Dash7 Python Support
A collection of Python modules, supporting Dash7.  
Christophe VG (<contact@christophe.vg>)

## Introduction

This repository contains a collection of Python modules that can help when working with the Dash7 Alliance Wireless Sensor and Actuator Network Protocol.

## Installation

### Dependencies

We use `Cerberus` for validating attributes. But we need a version &ge; 0.10, which is currently still a development version.

```bash
$ sudo pip install git+git://github.com/nicolaiarocci/cerberus.git
```

To run unit tests we use `nose`:

```bash
$ sudo pip install nose
```

For the manipulation of bitstrings, we use `bitstring`:

```bash
$ sudo pip install bitstring
```

### pyD7A

Minimal survival commands:

```bash
$ git clone <location to be determined>
$ cd pyd7a
$ make
*** running all tests
.......................................................
----------------------------------------------------------------------
Ran 55 tests in 0.746s

OK
*** generating unittest coverage report (based on last test run)
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
d7a/alp/action                    14      0   100%   
d7a/alp/command                    9      0   100%   
d7a/alp/operands/file             18      0   100%   
d7a/alp/operations/nop             6      0   100%   
d7a/alp/operations/operation      12      0   100%   
d7a/alp/operations/responses       7      0   100%   
d7a/alp/parser                    75      2    97%   89-90
d7a/alp/payload                    7      0   100%   
d7a/sp/configuration              17      0   100%   
d7a/sp/qos                        13      0   100%   
d7a/sp/session                     9      0   100%   
d7a/sp/status                     16      0   100%   
d7a/tp/addressee                  19      0   100%   
d7a/types/ct                      11      0   100%   
------------------------------------------------------------
TOTAL                            233      2    99%
```

If all tests ran without any errors, you're good to go.

## Modules

### ALP Parser

A parser for Application Layer Programming commands. From the specification: "_ALP is the D7A Application API. It is a generic API, optimized for usage with the D7A Session Protocol. It can be encapsulated in any other communication protocol. ALP defines a standard method to manage the Data Elements by the Application._"

#### Minimal Example

```python
>>> from d7a.alp.parser import Parser
>>> bytes = [
...       0xd7,                                           # interface start
...       0x04, 0x00, 0x00, 0x00,                         # fifo config
...       0x20,                                           # addr (originally 0x00)
...       0x24, 0x8a, 0xb6, 0x01, 0x51, 0xc7, 0x96, 0x6d, # ID
...       0x20,                                           # action=32/ReturnFileData
...       0x40,                                           # File ID
...       0x00,                                           # offset
...       0x04,                                           # length
...       0x00, 0xf3, 0x00, 0x00                          # data
...     ]
>>> (msg, info) = Parser().parse(bytes)
>>> from pprint import pprint
>>> pprint(msg.as_dict())
{'__CLASS__': 'Command',
 'interface': {'__CLASS__': 'Status',
               'addressee': {'__CLASS__': 'Addressee',
                             'cl': 0,
                             'hasid': True,
                             'id': 2633117048934733421L,
                             'vid': False},
               'fifo_token': 0,
               'missed': False,
               'nls': False,
               'request_id': 0,
               'response_to': {'__CLASS__': 'CT', 'exp': 0, 'mant': 0},
               'retry': False,
               'state': 4},
 'payload': {'__CLASS__': 'Payload',
             'actions': [{'__CLASS__': 'Action',
                          'group': False,
                          'operation': {'__CLASS__': 'ReturnFileData',
                                        'op': 32,
                                        'operand': {'__CLASS__': 'Data',
                                                    'data': [0,
                                                             243,
                                                             0,
                                                             0],
                                                    'offset': {'__CLASS__': 'Offset',
                                                               'id': 64,
                                                               'offset': 0,
                                                               'size': 1}}},
                          'resp': False}]}}
```

#### Status

Currently the parser only implements the minimal constructions to parse `ReturnFileData` messages. The parser will be kept in sync with the supported messages in the [OSS-7: Open Source Stack for Dash7 Alliance Protocol](https://github.com/MOSAIC-LoPoW/dash7-ap-open-source-stack).

