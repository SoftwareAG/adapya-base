"""
ecscodec - mapping ECS encodings to Python codecs
=================================================

ECS is the acronym for Entire Conversion Services, a text conversion
library used with Adabas.



.. note:: currently not all ECS encodings and Python codecs are listed.
          Non-existent codepage numbers could be mapped to the
          Python encodings per default 'cp%d' % i

"""
import string

py2ecs={\
  #Codec, ECS encoding
  'cp037':      37,
  'cp273':     273,
  'cp437':     437,
  'cp500':     500,
  'iso-8859-1': 819,
  'latin_1':   819,
  'utf8':      4091,
  'utf16':     4095    # utf16 includes byte order mark (BOM)
  }

ecs2py={\
  #ECS encoding, codec
  37:   'cp37',      #EBCDIC: USA, Canada, Brazil, Australia, New Zealand
  273:  'cp273',     #EBCDIC: Austria, Germany, de_deu
  437:  'cp437',     #PC: English
  500:  'cp500',     #EBCDIC: Belgium, Canada, Switzerland
  819:  'iso-8859-1',# Latin-1
  4091: 'utf8',      # unicode UTF-8
  4095: 'utf16'      # unicode
  }


def getcodec(ecskey):
    "return the Python codec name given the ECS encoding key"
    if ecskey == 0:
        return ''
    if ecskey in ecs2py:
        return ecs2py[ecskey]
    else:
        return 'cp%d' % ecskey

def getecs(codec):
    "return the ECS encoding key given the Python codec name"
    if codec == '':
        return 0
    if codec in py2ecs:
        return py2ecs[codec]
    else:
        if codec.startswith('cp'):
            return int(codec[2:])
        else:
            return py2ecs[codec]

#
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
#
#  $Date: 2017-05-17 20:51:16 +0200 (Wed, 17 May 2017) $
#  $Rev: 768 $
