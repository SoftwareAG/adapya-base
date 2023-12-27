# -*- coding: utf-8 -*-
"""Experimenting
Create a condensed record from a base datamap so that
- unused fields are removed from the record
- in strings/Alpha fields no trailing blanks are stored
- the format is created accordingly

$Date: 2021-09-24 23:06:39 +0200 (Fri, 24 Sep 2021) $
$Rev: 1023 $
"""
from __future__ import print_function          # PY3

from adapya.base.defs import Abuf
from adapya.base.datamap import Datamap, String, Uint2, T_STRING
from adapya.base.dump import dump

class Vrecord(object):

    def makemap(self,dmname, *fieldlist, **kw):

        nflist = [] # new field list

        for v in fieldlist:

            # key - field name, fty - field type, odict - field options
            key, fty, size, odict = v

            vvalue = getattr(self,key,None) # Get field value if set in vrecord

            if vvalue is not None: # if value is set in Vrecord instance use it

                if fty in (T_STRING,): # field formats that are variable
                    vlen = len(vvalue)
                    if vlen == 0: # if string is empty we set it at size 1
                        size = 1
                    elif vlen < size:
                        size = vlen     # shorten field length
                    # else: leave size as is

                nflist.append( (key,fty,size,odict) )   # set this field for output record

        if len(nflist) == 0:
            raise Exception('Vrecord instance has no fields set for output record', self)

        self.vmap = Datamap(dmname, *nflist, **kw)
        self.fieldlist = nflist

        if 1:
            mybuf = Abuf(self.vmap.dmlen)
            self.vmap.buffer = mybuf
            self.setmap()

            print( self.vmap.genfb() )

            self.vmap.dprint()
            dump(mybuf)

        return self.vmap

    def setmap(self):

        for v in self.fieldlist:

            # key - field name, fty - field type, odict - field options
            key, fty, size, odict = v

            vvalue = getattr(self,key,None) # Get field value if set in vrecord

            if vvalue is not None: # if value is set in Vrecord instance use it
                setattr(self.vmap, key, vvalue)


myfields = ( Uint2('id',fn='ID'), String('firstname', 20, fn='FN'), String('lastname', 20, fn='LN'))

v1 = Vrecord()
v1.id = 1
v1.firstname = 'Hugo'
v1.lastname = 'Schmitt'
m1 = v1.makemap('v1', *myfields)

v2 = Vrecord()
v2.id = 2
v2.firstname = 'I'
v2.lastname = 'O'
m2 = v2.makemap('v2', *myfields)

v3 = Vrecord()
v3.id = 3
v3.firstname = ''
v3.lastname = 'O'
m2 = v3.makemap('v3', *myfields)

v4 = Vrecord()
v4.id = 4
v4.firstname = '12345678901234567890xxxx'
v4.lastname = 'Meier'
m4 = v4.makemap('v4', *myfields)

v5 = Vrecord()
v5.lastname = 'Only'
m6 = v5.makemap('v5', *myfields)


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
