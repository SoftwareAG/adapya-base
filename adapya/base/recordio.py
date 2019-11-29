"""
recordio - read and write records
=================================

The module recordio contains functions to read or write records with special
structures (variable, variable blocked):

    - RDW   records preceded by a record descriptor word

    - BDW   variable records blocked

    - EXCL4 records preceded by a 4 bytes exclusive record length
            in native byte-order)

"""
from __future__ import print_function          # PY3
from io import BytesIO
import os
import sys
from adapya.base.defs import Abuf
from adapya.base.dump import dump
from adapya.base.datamap import Datamap, Uint2, Uint1, Uint4, NETWORKBO


SEGALL = 0
SEGFIRST = 1
SEGLAST = 2
SEGMIDDLE = 3

def segmenttype(seg):
    if seg > 3:
        raise BaseException('invalid segment type %02X' % seg)
    return ['complete record','first segment',
            'last segment','middle segment'][seg]


rdw =  Datamap('RDW',
    # RDW Record descriptor word
    Uint2('rlen'), # Record length
    Uint1('seg'), # Segment control
    Uint1('seg2'), # Segment control 2 (unused)
    byteOrder=NETWORKBO,
    )

excl4 =  Datamap('EXCL4',
    # 4 Byte Excluded length Record
    Uint4('rlen'), # Record length
    )

# used for writing
wrdw =  Datamap('RDW',
    # RDW Record descriptor word
    Uint2('rlen'), # Record length
    Uint1('seg'), # Segment control
    Uint1('seg2'), # Segment control 2 (unused)
    byteOrder=NETWORKBO,
    buffer=Abuf(4),
    )

isnp =  Datamap('ISN_prefix',
    Uint4('isn'), # Segment descriptor
    byteOrder=NETWORKBO,
    buffer=Abuf(4)
    )


def readrec(f,recform='',dumphdr='',numrec=0,skiprec=0, ecodec='cp037',debug=0):
    """ readrec - Generator function to read records
    with special record format specified in recform

        :param f: filehandle of open file
        :param recform: record format to process

            - 'RDW' variable record format (2 bytes length, Network byte order)
                    return record without RDW header (exclusive)

            - 'RDW+' variable record format (2 bytes length, Network byte order)
                    return record including RDW header

                    Note: for segmented records rlen in RDW header is length
                          of first segment and not the whole record

            - 'BDW' variable record blocked: input includes Block Descriptor Word
                    which is skipped
                    return record without RDW header (exclusive)

            - 'BDW+' same as BDW but return record including RDW header

            - 'EXCL4' exclusive 4 bytes length, native byte order

        :param dumphdr: header text of record; if not empty: prints record
        :param ecodec: Ebcdic codec for character interpretation when dumping records
        :param debug: 1 - print RDW information

    Example usage::

    >> for rec in readrec(f,recform='RDW',dumphdr='my_records'):
    >>    process(rec)

    """
    V = 1        # variable records
    VB = 2       # variable blocked includes variable
    WITH_RDW = 4 # return record with RDW header

    bu = None    # BytesIO object
    recfm=0
    block_rlen = 0
    if recform.startswith('RDW'):
        recfm = V
    elif recform.startswith('BDW'):
        recfm = VB
    if recform.endswith('+'):
        recfm |= WITH_RDW

    if recfm & (V|VB):
        i = 0  # counting complete/logical records
        while  i < skiprec:     # skipping records loop
            rdws = f.read(4)
            if len(rdws)<4:
                return
            rdw.buffer=rdws     # use rdws as underlying buffer
            rlen = rdw.rlen

            if rlen > 0x7fff:
                dwtype='record'
                if recfm & VB and block_rlen==0:
                    dwtype='block'
                raise BaseException('Invalid %s length %s exceeds 32k-1 in record %d' %
                         (dwtype, rlen, i+1))

            if recfm & VB:
                if block_rlen > 4: # reduce remaining block length by record len
                    block_rlen -= rlen
                else: # need to consume BDW block header 4 bytes
                    block_rlen = rlen
                    if debug & 1:
                        dump(rdws[0:4],header='Block Descriptor Word')
                    continue  # need to read RDW

            if rdw.rlen > 4:    # it's a record
                record = f.seek(rdw.rlen-4, os.SEEK_CUR) # skip record
            if rdw.seg in (SEGFIRST, SEGMIDDLE):
                if debug&1: print('Skipping %s len(%04x) in logical record %d'%(
                    segmenttype(rdw.seg), rdw.rlen, i))
                continue # only count last or unsegmented records

            i += 1
            if debug & 1: print('Skipping %s len(%04x) in logical record %d'%(
                segmenttype(rdw.seg), rdw.rlen, i))

        maxrec = skiprec + numrec
        while 1:
            rdws = f.read(4)
            if len(rdws)<4:
                return
            rdw.buffer=rdws # use rdws as underlying buffer
            rlen = rdw.rlen

            if rlen > 0x7fff:
                dwtype='record'
                if recfm & VB and block_rlen==0:
                    dwtype='block'
                raise BaseException('Invalid %s length %s exceeds 32k-1 in record %d' %
                         (dwtype, rlen, i+1))

            if recfm & VB:
                if block_rlen > 4:  # still records in block
                    block_rlen -= rlen
                else: # need to consume BDW block header 4 bytes
                    block_rlen = rlen

                    if debug & 1:
                        dump(rdws[0:4],header='Block Descriptor Word')
                    continue  # need to read RDW

            if rlen < 5:    # empty record
                yield b''

            if debug&1: print('Reading %s len(%04x) in logical record %d'%(
                segmenttype(rdw.seg), rdw.rlen, i+1))

            if rdw.seg : # copy any segmented record to buffer
                if rdw.seg == SEGFIRST: # first segment
                    bu=BytesIO()
                    if recform.endswith('+'): # record to include RDW
                        bu.write(rdws)

                bu.write(f.read(rlen-4))

                if rdw.seg == SEGLAST: # last segment
                    record = bu.getvalue() # return collected segments
                    if dumphdr:
                        dump( record, header='\n%s: %d, total length %04X'%(
                            dumphdr,i+1,len(record)),ecodec=ecodec )
                    yield record
                else:
                    continue    # do not count numrec for first/middle segment

            else:  # record is not segmented i.e. complete
                if recform.endswith('+'): # record to include RDW
                    f.seek(-4, os.SEEK_CUR) # rewind to record start
                else:
                    rlen -= 4

                record = f.read(rlen)
                if dumphdr:
                    rdwx = ' (%04X,%04X)' %(rdw.rlen, rdw.seg)
                    dump( record, header='\n%s: %d%s'%(dumphdr,i+1,rdwx),ecodec=ecodec )
                yield record
            i += 1
            if numrec and i > maxrec:
                return
            # while loop

    elif recform == 'EXCL4':
        for i in range(skiprec):
            e4s = f.read(4)
            if len(e4s)<4:
                return
            excl4.buffer=e4s # use rdws as underlying buffer
            if excl4.rlen > 4:    # record
                record = f.seek(excl4.rlen, os.SEEK_CUR) # skip record
        i = skiprec   # i is total record count starting from 1
        maxrec = skiprec+numrec
        while 1:
            i += 1
            if numrec and i > maxrec:
                return
            e4s = f.read(4)
            if len(e4s)<4:
                return
            excl4.buffer=e4s # use rdws as underlying buffer
            rlen = excl4.rlen
            if rlen < 1:    # empty record
                yield b''
            else:
                record = f.read(rlen)
                if dumphdr:
                    dump( record, header='\n%s: %d'%(dumphdr,i),ecodec=ecodec )
                yield record
            # while loop



    elif recform=='':   # textfile, read data is str
        for i in range(skiprec):
            record = f.readline()
            if record == '':  # end of file
                return
        i = skiprec   # i is total record count starting from 1
        maxrec = skiprec+numrec
        while 1:
            i += 1
            if numrec and i > maxrec:
                return  # all processed
            else:
                record = f.readline()
                if record == '':  # not b''
                    return  # end of file
                record = record.rstrip() # remove trailing whitespace and newline
                if dumphdr:
                    dump( record, header='\n%s: %d'%(dumphdr,i),ecodec=ecodec )
                yield record
            # while loop
    else:
        raise BaseException('Invalid recform %r specified' % recform)

def writerec(f, record, isn=None, recform=''):
    """ writerec - function to write records with special record format

        :param f: filehandle of open file
        :param record: record string/bytearray to be written
        :param isn: prefix record with an 4 byte integer in Network byte order
        :param recform: record format to process::

            - 'RDW' variable record format:

              2 bytes length, 2 bytes emtpy in Network byte order

    """

    if recform == 'RDW':
            if isn is None:
                wrdw.rlen = len(record)+4
            else:                   # include ISN as 4 bytes prefix
                wrdw.rlen = len(record)+8

            f.write(wrdw.buffer)

            if isn is not None:
                isnp.isn=isn
                f.write(isnp.buffer)

            f.write(record)

    else:
        raise BaseException('Invalid recform %r specified' % recform)


if __name__ == "__main__":
    import sys
    # import doctest
    # doctest.testmod()
    print(__doc__)
    print('\n===> %s has no main section - do not execute it directly! <===\n' % __file__)
    sys.exit(99)


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
