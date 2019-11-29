# -*- coding: utf-8 -*-
"""Show the Mapping features of the datamap module

1. Define datamap with field of each format
2. Assign values
3. Dump buffers
4. Pretty print buffers

Windows platform: When running this script in command line the value
    cha1 may not come out as the copyright symbol unless non-raster
    font is being used and the Windows codepage 65001 for UTF-8 is set:

    CHCP 65001   (on the command line)


$Date: 2018-11-09 15:31:28 +0100 (Fri, 09 Nov 2018) $
$Rev: 878 $
"""
from __future__ import print_function          # PY3

from adapya.base.defs import Abuf
from adapya.base.datamap import *
from adapya.base.dump import dump
from datetime import datetime

cm=None

def try_all_formats():
    global cm

    p = Datamap( 'test_all_formats p',
        String( 'str8', 8),
        Unicode('uni4', 4),   # unicode 4 chars = 8 bytes
        Utf8(   'utf8', 8),
        Bytes(  'byt4', 4),
        Char(   'cha1'),
        Int1(   'int1'),
        Uint1(  'uin1'),
        Int2(   'int2'),
        Uint2(  'uin2'),
        Int4(   'int4'),
        Uint4(  'uin4', opt=T_STCK),    # Uint4 STCK display as time
        Int8(   'int8'),
        Uint8(  'uin8', opt=T_STCK),    # Uint8 STCK display as timestamp
        Float(  'flo4'),
        Double( 'dou8'),
        Packed( 'pac4', 4),
        Unpacked( 'unp1', 1),
        Unpacked( 'unp8', 8),
        Unpacked( 'datetime', 14, dt='DATETIME'),    # Python datetime object
        Unpacked( 'timestamp', 20, dt='TIMESTAMP'),  # Python datetime object
        Unpacked( 'date', 8, dt='DATE'),  # Python date object
        Unpacked( 'time', 6, dt='TIME'),  # Python time object
        Packed( 'natdate', 4, dt='NATDATE'),  # Python date object
        Packed( 'nattime', 7, dt='NATTIME'),  # Python datetime object
        Uint4( 'unixtime', dt='UNIXTIME'),  # Python datetime object
        Int8( 'xtimestamp', dt='XTIMESTAMP'),  # Python datetime object
        )

    cm=p

    sz=p.getsize()  # return size of datamap
    dtnow = datetime.now()

    print()
    print( '--- Datamap=%s, size=%d ---\n' % (p.dmname, sz))

    print( '    datetime now: %s' % dtnow)

    p.buffer = Abuf(sz)

    # set field values
    p.str8='Maßkrüge'          # string
    p.uni4='ßöäü'              # unicode
    p.utf8='äßö'               # utf8
    p.byt4=b'\xC1\xC4\xC1\x4B'  # non-ASCII bytes are displayed in HEX
    p.cha1='©'                 # copyright character
    # p.cha1='c'
    p.int1=-128
    p.uin1=255

    p.int2=-32768
    p.uin2=65535

    p.int4=-0x80000000
    p.uin4= 0xaee3efa4  # 1.1.1997

    p.int8=-0x8000000000000000
    p.uin8= 0xb1962f9305180000  # 1.1.1999

    p.flo4 = 2.0
    p.dou8 = 0.5

    p.pac4 = -1234567
    p.unp1 = 1
    p.unp8 = -12345678


    p.datetime = dtnow
    p.date     = dtnow.date()
    p.time     = dtnow.time()
    p.nattime  = dtnow
    p.natdate  = dtnow.date()
    p.timestamp = dtnow

    p.unixtime = dtnow
    p.xtimestamp = dtnow

    print( '-- print some numbers --')
    print( 'pac8', p.pac4)
    print( 'unp1', p.unp1)
    assert p.unp1 == 1
    print( 'unp8', p.unp8)
    assert p.unp8 == -12345678
    print( 'datetime', p.datetime)   # datetime() str() method

    print( '--- Dumping datamap structure ---')
    dump(p.buffer)

    print( '---Printing datamap structure with dprint() ---\n')
    p.dprint()  # print datamap

    print( '---Printing datamap structure with lprint() ---\n')
    p.lprint(header=1)  # print datamap header
    p.lprint()          # print datamap
    p.lprint()          # print datamap

    try:
        print( '--- Assigning to undefined field xx ---')
        p.xx=123
    except DatamapError as e:
        print( '\t',e.value)
        dump(e.dmap.buffer)

    return p

def try_multiple():
    print( "--- try_multiple() ---")
    global cm
    g = Datamap( 'mymap',
            String('foo' , 2, occurs=3),
            Int2('bar') )
    cm=g

    g.buffer=Abuf(8)
    g.buffer.value=b'abKIyz\x11\x00'
    dump(g.buffer)
    dir(g.foo)
    print( g.foo)
    print( g.foo[1])
    for i,v in enumerate(g.foo):
        print( i,v)
    print( "list(g.foo) =", list(g.foo))
    print( "g.bar=%d" % g.bar)
    g.foo[1]='QQQ'
    print( list(g.foo))
    g.foo=('hh','TT', 'ww')
    print( list(g.foo))
    dump(g.buffer)

    try:
        g.foo[3]='RRR'
    except StopIteration as e:
        print( "Caught StopIteration exception for g.foo[3]='RRR', continue")
        dir(e)
        print( e )
        pass
    return g


def try_periodic():
    print( "--- try_periodic() ---")
    global cm
    g = Datamap( 'mymap',
            Int2('i1'),
            Periodic(Datamap('pe',
                String('ps', 2),
                Int2('pi')),
                occurs=3),
            Int2('i2') )
    cm=g
    print( g.dmlen)
    g.buffer=Abuf(g.dmlen)
    g.buffer.value=b'\x11\x00ab\x01\x00KI\x02\x00yz\x03\x00\x22\x00'
    dump(g.buffer)
    dir(g.pe)
    print( g.pe)
    print( g.pe[1])
    for i,v in enumerate(g.pe):
        print( i,v,v.ps,v.pi)
    print( g.i2)
    g.pe[1].ps='QQQ'
    g.pe[2].pi=33
    dump(g.buffer)
    return g


def try_var_formats():
    print( "--- try_var_formats() ---")
    global cm

    p = Datamap( 'test_var_formats',
        String( 'sv1', 0, opt=T_VAR1),
        String( 'sv2', 0, opt=T_VAR2),
        String( 'sv4', 0, opt=T_VAR4),
        Unicode('uv1', 0, opt=T_VAR1),   # unicode 4 chars = 8 bytes
        Utf8(   'tv1', 0, opt=T_VAR1),
        # Bytes(  'bv1', 0, opt=T_VAR1),
        )


    p0 = Datamap( 'test_var_formats0',
        Uint1(  'iv1'),
        Uint2(  'iv2'),
        Uint4(  'iv4'),
        Uint1(  'ui1'),
        Uint1(  'ti1'),
        # Uint1(  'bi1'),
        )

    p1 = Datamap( 'test_var_formats1',
        Uint1(  'iv1'),
        String( 'sv1', 3),
        Uint2(  'iv2'),
        String( 'sv2', 2),
        Uint4(  'iv4'),
        String( 'sv4', 4),
        Uint1(  'ui1'),
        Unicode('uv1', 4),   # unicode 4 chars = 8 bytes
        Uint1(  'ti1'),
        Utf8(   'tv1', 8),
        # Uint1(  'bi1'),
        # Bytes(  'bv1', 4),
        )

    p2 = Datamap( 'test_var_formats2',
        Uint1(  'iv1'),
        String( 'sv1', 254),
        Uint2(  'iv2'),
        String( 'sv2', 256),
        Uint4(  'iv4'),
        String( 'sv4', 64000),
        Uint1(  'ui1'),
        Unicode('uv1', 126),   # unicode 4 chars = 8 bytes
        Uint1(  'ti1'),
        Utf8(   'tv1', 8),
        # Uint1(  'bi1'),
        # Bytes(  'bv1', 4),
        )

    cm=(p,p0,p1,p2)

    p0.buffer = Abuf(p0.getsize())
    p1.buffer = Abuf(p1.getsize())
    p2.buffer = Abuf(p2.getsize())

    p0.iv1=1
    p0.iv2=2
    p0.iv4=4
    p0.ui1=1
    p0.ti1=1

    p1.iv1=4
    p1.iv2=4
    p1.iv4=8
    p1.ui1=9
    p1.ti1=9
    p1.sv1='abc'
    p1.sv2='DE'
    p1.sv4='fghi'
    p1.uv1='JKLM'
    p1.tv1='nopqrstu'

    p2.iv1=255
    p2.iv2=258
    p2.iv4=64004
    p2.ui1=253
    p2.ti1=9
    p2.sv1='A'*254
    p2.sv2='b'*256
    p2.sv4='C'*64000
    p2.uv1='d'*126
    p2.tv1='E'*8


    p.buffer=p0.buffer
    dump(p.buffer)
    p.dprint()

    p.buffer=p1.buffer
    dump(p.buffer)
    p.prepare()
    p.dprint()

    p.buffer=p2.buffer
    dump(p.buffer)
    p.prepare()
    p.dprint()
    print(p.items())

    return p, p0, p1, p2


def try_multiple_1toN():
    print( "--- try_multiple_1toN() ---")

    global cm
    g = Datamap( 'mymap',
            Uint1('foo_count'),
            String('foo' , 2, occurs=lambda:g.foo_count),
            Int2('bar') )
    cm=g
    g.buffer=Abuf(1024)
    print( 'occurs=3')
    g.buffer.value=b'\x03abKIyz\x11\x00'
    g.prepare()
    dump(g.buffer)
    dir(g.foo)
    print( g.foo)
    print( g.foo[1])
    for i,v in enumerate(g.foo):
        print( i,v)
    print( list(g.foo))
    print( g.bar)
    g.foo[1]='QQQ'
    print( list(g.foo))
    g.foo=('hh','TT', 'ww')
    print( list(g.foo))
    dump(g.buffer)
    try:
        g.foo[3]='RRR'
    except StopIteration as e:
        dir(e)
        print( e )
        pass

    print( 'occurs=0')
    g.buffer.value=b'\x00\x11\x00'
    g.prepare()
    dump(g.buffer)
    dir(g.foo)
    print( g.foo)

    try:
        g.foo[0]='RRR'
    except StopIteration as e:
        dir(e)
        print( e )
        pass

    for i,v in enumerate(g.foo):
        print( i,v)
    print( list(g.foo) )
    print( g.bar)

    return g


def try_periodic_1toN():
    print( "--- try_periodic_1toN() ---")
    global cm
    g = Datamap( 'pemap',
            Int2('i1'),
            Uint1('pe_count'),
            Periodic(Datamap('pe',
                String('ps', 2),
                Int2('pi')),
            occurs=lambda:g.pe_count),
            Periodic(Datamap('qe',
                String('qs', 3),
                Uint1('qi')),
            occurs=2),
            Int2('i2') )
    print( g.dmlen)
    cm=g

    g.buffer=Abuf(1024)

    print( '\noccurs=0')
    g.buffer.value=b'\x11\x00\x00pa1\x01pa2\x02\x22\x00'
    g.prepare()

    dump(g.buffer)
    print( g.pe)
    try:
        print( g.pe[0])
    except StopIteration as e:
        dir(e)
        print( e )
        pass
    try:
        g.pe[1].ps='QQQ'
    except StopIteration as e:
        dir(e)
        print( e )
        pass
    for i,v in enumerate(g.pe):
        print( i, v, v.ps, v.pi )
    print( g.i2 )
    dump(g.buffer)

    print( '\noccurs=3' )
    g.buffer.value=b'\x11\x00\x03ab\x01\x00KI\x02\x00yz\x03\x00pa1\x01pa2\x02\x22\x00'
    g.prepare()

    dump(g.buffer)
    print( g.pe )
    print( g.pe[1] )
    for i,v in enumerate(g.pe):
        print( i, v, v.ps, v.pi )

    print( g.i2 )
    g.pe[1].ps='QQQ'
    g.pe[2].pi=33
    dump(g.buffer)

    g.dprint()

    return g


def try_MU_1toN_in_PE():
    print( "--- try_MU_1toN_in_PE() ---")
    global cm
    g = Datamap( 'pemap',
            Int2('i1'),
            Uint1('pg_count'),
            Periodic(
                Datamap('pg',
                    String('pe', 2),
                    Int1('pf')),
                occurs=lambda:g.pg_count),
            Periodic(
                Datamap('qg',
                    String('qe',2),
                    Uint1('mu_count'),
                    String('mu',2,occurs=lambda:-1) # count 1 byte before field
                    ),
                occurs=2),
            )
    print( g.dmlen)
    cm=g

    g.buffer=Abuf(1024)

    if 0:
        print( '\noccurs=0')
        g.buffer.value=b'\x01\x00\x01\x00\x02\x00'
        g.prepare()

        dump(g.buffer)
        print( g.pe)

        g.dprint()

        try:
            print( g.pe[0])
        except StopIteration as e:
            dir(e)
            print( e )
            pass

    if 1:
        print( '\noccurs=3, muocc=3,1' )
        g.buffer.value=b'\x02\x03P1\xffP2\xfeP3\xfdQ1\x03MaMeMiQ2\x01Na'
        g.prepare()

        dump(g.buffer)

        print( g.pg )
        print( g.pg[1] )
        for i,v in enumerate(g.pg):
            print( i, v, v.pe, v.pf )
        for i,v in enumerate(g.qg):
            print( i, v, v.qe, len(v.mu))
            for j,w in enumerate(v.mu):
                print('MU', j, w, w.mu)
        g.dprint()

    return g

if __name__=='__main__':
  if 1:
    # select one function
    dm_mupg = try_MU_1toN_in_PE()
  else:
    # run all demo functions and keep the datamap instances
    #  for use in interactive mode (python -i datamap2.py)
    dm_muv = try_multiple_1toN()
    dm_all = try_all_formats()
    dm_pg  = try_periodic()
    dm_var = try_var_formats()
    dm_pgv = try_periodic_1toN()
    dm_mu  = try_multiple()


#  Copyright 2004-ThisYear Software AG
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
