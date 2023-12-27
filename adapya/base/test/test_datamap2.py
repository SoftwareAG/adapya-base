# -*- coding: latin_1 -*-
"""Test the Mapping features of the datamap module
   Focus on string/bytes conversion to/from field encoding

1. Define datamap with field
2. Assign values
3. Dump buffers
4. Pretty print buffers



$Date: 2018-05-07 15:13:26 +0200 (Mon, 07 May 2018) $
$Rev: 818 $
"""
from __future__ import print_function          # PY3

from adapya.base.defs import Abuf
from adapya.base.datamap import *
from adapya.base.dump import dump
from datetime import datetime

cm=None

def try_string(ebcdic=0,encoding=''):
    global cm

    p = Datamap( 'Test strings encoding=%s, ebcdic=%d' % (encoding,ebcdic),
        String( 'str8', 8),
        String( 'str4', 4),
        String( 'str10', 10),
        encoding=encoding,ebcdic=ebcdic
        )

    cm=p

    sz=p.getsize()  # return size of datamap

    print()
    print( '=== Datamap=%s, size=%d ===\n' % (p.dmname, sz))
    print( '    encoding = %s' % (p.encoding))
    print( '    ebcdic   = %d' % (p.ebcdic))

    p.buffer = Abuf(sz)

    # set field values
    p.str8 = b'abcd56'       # string
    p.str4 = b'a1'           # string
    p.str10 = u'a+öäü'       # string

    print( '-- print some numbers --')
    print( p.str8)
    print( p.str4)
    print( p.str10)

    print( '--- Dumping datamap structure ---')
    dump(p.buffer)

    print( '---Printing datamap structure with dprint() ---\n')
    p.dprint()  # print datamap

    print( '---Printing datamap structure with lprint() ---\n')
    p.lprint(header=1)  # print datamap header
    p.lprint()          # print datamap

    return p


if __name__=='__main__':
  if 0:
    # select one function
    pass
  else:
    # run all demo functions and keep the datamap instances
    #  for use in interactive mode (python -i datamap2.py)
    dm_str_enc1 = try_string(encoding='')
    dm_str_enc2 = try_string(encoding='cp037')
    dm_str_enc3 = try_string(encoding='cp037',ebcdic=1)
    dm_str_enc4 = try_string(                 ebcdic=1)


#  Copyright 2004-2023 Software AG
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
