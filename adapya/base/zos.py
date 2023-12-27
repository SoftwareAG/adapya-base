#!/usr/bin/env python2
"""zos.py contains a set of z/OS related functions:

 - pdsdir() - open and read a partitioned dataset (extended) and return
              directory entries (generator function)
"""
from __future__ import print_function          # PY3

from collections import namedtuple
from fnmatch import fnmatch

from adapya.base.dump import dump

from adapya.base.datamap import Datamap,Bytes,String,\
    NETWORKBO,String,Packed,Uint1,Uint2,Uint4

class Member(namedtuple('Member','name changed size id alias')):
    """ Member describes information of one member in a directory listing
    of a partitioned dataset (PDS).

    Samples of member info displays on various systems:

    *ISPF (TSO)
    SASCX                       16   1998/11/04   1999/06/14 21:31:48    MM
    SAVF

    *NSPF (Natural Process)
    MEMBER            VV.MM  CREATED  MODIFIED TIME  SIZE   INIT   TID   ID
    SASCX             01.22  19981104 19990614 21:31     16     74       MM
    SAVF                              19950829 11:09     22          224 MM
    PARMEL

    *UPDS (COM-PLETE)
    SASCX         00000016 REC SAVE:14.06.1999 21:31   USER  MM
    SAVF          00000022 REC SAVE:29.08.1995 11:09 TID0224 MM
    """

    __slots__ = ()
    def __str__(self):
        return '%-8s  %5d  %s %-8s%s' % (self.name, self.size,
                    self.changed, self.id, 'Alias' if self.alias else '' )


class Drlen(Datamap):
    """Directory record length half word"""
    def __init__(self,**kw):
        Datamap.__init__(self, 'DRL',
            Uint2('drlen'), # directory entry length for directory record
            byteOrder=NETWORKBO
            )


MIINDSCLM = 0x80 # SCLM indicator (member and SCLM info are in sync)
MIINDXSTA = 0x20 # extended statistics (size,init and chgd are valid)

class MemberInfo(Datamap):
    """Member information entry in PDS directory"""
    def __init__(self,**kw):
        Datamap.__init__(self, 'DRL',
            String('name',8),
            Bytes('ttr',3),
            Uint1('flag'),  # Alias flag 0x80 and user half words (max 0x1f * 2)

            # --- if length in flag is 0x0f, ie. 30 bytes ISFP statistics follow
            Uint1('vv'),    # version (set by SCLM?)
            Uint1('mm'),    # modifications (range 0-99)
            Uint1('ind'),   # SCLM indicator
            Uint1('ss'),    # time last modified (second part)
            Packed('credate',4),    # ibm creation date  0119001f = 20190101
            Packed('moddate',4),    # date last modified 0099032f = 19990201
            Uint2('hhmm'),  # time last modified 0xhhmm
            Uint2('size2'), # current number of lines, 655
            Uint2('init2'), # initial number of lines
            Uint2('chgd2'), # number of lines changed
            String('id',8),  # user id of last modification

            # --- the following is only set if hw length in flag is 0x14 (=40 bytes)
            #     then ind & MIINDXSTA will be set
            Uint4('size'),  # current number of lines
            Uint4('init'),  # initial number of lines
            Uint4('chgd'),  # number of lines changed

            byteOrder=NETWORKBO,
            **kw
            )

    def getinfo(self):
        uinfolen = 2 * self.flag&0x1f

        if uinfolen:
            hhmm = unpackos(self.hhmm)  # unpacked number w/o sign 0x2459 to integer
            s   = unpackos(self.ss)     #                          0x59
            h,m = gethhmm(hhmm)
            changed = i2dt( self.moddate, 0).replace(hour=h,minute=m,second=s)
            size = self.size if self.ind&MIINDXSTA else self.size2
            return Member(self.name,changed,size, self.id, self.flag&0x80 == 0x80)
        else:
            return Member(self.name,None,0,'', self.flag&0x80 == 0x80)


def pdsdir( pdsname, mmatch='', info=0, encoding='cp037', verbose=0):
    """pdsdir - generator function to read directory entries
    in a partitioned dataset (extended)

    :param pdsname: name of the partitioned datset

    :param mmatch: matching pattern according to fnmatch
                    modules rules (optional)

    :param info:   return member names (info=0) or Memberinfo tuple
                   (info=1)

    Example:

    >>> for name in pdsdir('mm.source', mmatch='COBL*'):
            print(name)

    >>> for member in pdsdir('mm.source', mmatch='COBL*', info=1):
            print(member.name, member.changed, member.size,
                member.id, member.alias)

    """
    mi = MemberInfo(encoding=encoding)

    mmatch = mmatch.upper()  # convert to upper case

    with open("//'%s'" % pdsname ,'rb') as f:
        print('pdsname=%s opened'%pdsname)
        drl = Drlen()

        while 1:
            drlbuf = f.read(2)
            if len(drlbuf)<2:
                return
            drl.buffer = drlbuf
            restlen = drl.drlen - 2
            membuf = f.read(254)        # earch dir record is 256 bytes
            mi.buffer = membuf
            mi.offset = 0

            if verbose > 2:
                dump(membuf)

            while restlen >= 12:
                if mi.ttr == b'\x00\x00\x00': # last and empty entry in directory?
                    if verbose:
                        print('leaving pdsdir()')
                    return
                uinfolen = 2*(mi.flag&0x1f)
                restlen -= uinfolen+12 # basic member entry len + user info

                if not mmatch or fnmatch(mi.name, mmatch):  # case insensitive match
                    if verbose:
                        print(mi.name,'\tfound')
                    if verbose>1:
                        dump(membuf[mi.offset:mi.offset+12+uinfolen])

                    if info:
                        yield mi.getinfo() # return Member named tuple
                    else:
                        yield mi.name      # return the member name

                elif verbose > 2:
                    print('%08s not matched' %  mi.name)

                mi.offset += uinfolen+12
            continue

def unpackos(n):
    """ unpack packed number without sign
    :param p: integer

    >>> unpackos(0x2459)
    2459

    """
    t = 0
    p = 1
    while n>0:
        t += (n & 0x0f) * p
        p *= 10
        n >>= 4

    return t

def gethhmm(i):
    """ extract hour, minute from integer

    >>> gethhmm(2459)
    (24, 59)
    """
    return i//100, i%100


def idate(i):
    " Return string from IBM date 0cyyddd "
    if i > 100000:
        return '20%02d.%03d' % ( (i-100000)/1000, i%1000 )
    else:
        return '19%02d.%03d' % (i/1000, i%1000)

def i2dt(idat,itim):
    """Convert industry date time to datetime object

        :param idat: integer IBM industry date 0cyyddd
        :param itim: integer IBM time in 100ths of a second in day
    """
    from datetime import datetime, timedelta
    hh=mm=ss=hs=0

    if idat > 100000:
        yy = 2000 + (idat-100000) // 1000
    else:
        yy = 2000 + idat // 1000
    tdays = timedelta(idat%1000 - 1) # day in year starting with 0

    if itim:
        hh = itim/(100*3600)
        mm = itim/(100*60) - hh*60
        ss = itim/100 - hh*60*60 - mm*60
        hs = itim%100
    return datetime(yy,1,1,hh,mm,ss,hs*10000)+tdays


if __name__=='__main__':

    import getopt, sys

    def usage():
        print(
"""zos.py - z/OS PDS directory

 Usage: python zos.py --dataset <pds-dataset> [options]

 Options:

    -h, --help              display this help
    -d, --dataset <pds>     PDS or PDSE dataset name
    -i, --info              display member information
    -s, --select <pattern>  selection pattern for member name (see below)
    -v, --verbose

 Selection pattern with fnmatch syntax:
     *      matches everything
     ?      matches any single character
     [seq]  matches any character in seq
     [!seq] matches any character not in seq


 Example (short parameter form):
 -  select all members in PDS mm.source starting with COBL and show member info

    python zos.py -id mm.source -s COBL*

""")
        return  # from usage()

    # main logic continued ...

    pds = ''
    select = ''
    info = 0
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],
          'hd:is:v:',
          ['help','dataset=','select=','verbose='])

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                usage()
                sys.exit()
            elif opt in ('-d', '-- dataset'):
                pds = arg
            elif opt in ('-i', '--info'):
                info = 1
            elif opt in ('-s', '--select'):
                select = arg
            elif opt in ('-v', '--verbose'):
                verbose = int(arg)
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for i, mem in enumerate(
                    pdsdir(pds, mmatch=select, info=info, verbose=verbose),
                    start=1):
        print(i, mem)


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
