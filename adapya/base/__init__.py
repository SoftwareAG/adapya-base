#! /usr/bin/env python
# -*- coding: latin1 -*-
"""
adapya.base
-----------

The adapya.base package contains se1.0.5 modules that are used
in adapya:

- conv: simple text codepage conversion functions
- datamap: storage data mapping to python objects
- defs: basic buffer access and logging
- dtconv: date and time conversions
- dump: storage image access and printing
- ecscodec: text encode/decode based on software-ag's code page numbers
- ftptoolz: extra z/OS ftp features
- jconfig: manage configuration data in JSON file
- recordio: process formated sequential files (variable blocked, etc.)
- stck: mainframe timestamp conversions
- xtea: simple encryption
- zos: PDS/E directory member listing for z/OS

"""
__all__=["conv","datamap","defs","dtconv","dump","ecscodec","ftptoolz",
        "future","jconfig","recipes","recordio","stck","touch","xtea",
        "zos"]

__version__ = '1.0.5'
if __version__ == '1.0.5':
    _svndate='$Date: 2019-03-26 18:20:13 +0100 (Tue, 26 Mar 2019) $'
    _svnrev='$Rev: 911 $'
    __version__ = 'Dev ' +  _svnrev.strip('$') + \
                  ' '.join(_svndate.strip('$').split()[0:3])

#  Copyright 2004-2019 Software AG
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
