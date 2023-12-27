# -*- coding: latin1 -*-
"""
datamap - Map Memory Structures to Class Attributes
===================================================

The datamap.py module defines the Datamap class which allows to
map record or memory structures to class attributes

"""
from __future__ import print_function          # PY3
import struct
import string
import sys
import types
import ctypes
from binascii import hexlify,unhexlify
from datetime import datetime,date
from datetime import time as dtime
from .defs import Abuf
from .conv import ebc2asc,asc2ebc,str2asc,str2ebc,swap
from .dtconv import str2dt,date2natdate, datetime2unixtime, utc2xts
from .dtconv import timestamp2nattime,xts2utc,unix2utc
from .dtconv import natdate2date, nattime2timestamp
from .dump import dump
from .stck import sstck,sstckd

__date__='$Date: 2023-12-01 00:54:33 +0100 (Fri, 01 Dec 2023) $'
__version__='$Rev: 1072 $'

if sys.hexversion >= 0x3010100: # PY3
    PY3 = True
    rawhex = lambda x: ('%s' % hexlify(x).upper())[2:-1]

else:
    PY3 = False
    rawhex = lambda x: '%s' % hexlify(x).upper()


debug = 0  # trace packing/unpacking into datamaps
INDENT = '' # indent of debug information

# field formats
# const           C                Python
T_STRING = 1
T_BYTE   = 2    # string type binary
T_UNPK   = 3    # ibm370 zoned     integer/long
T_PACK   = 4    # ibm370 packed    integer/long
T_DMAP   = 5    # substructure defined by Datamap
T_UTF16  = 'u'  # uint2 unicode swapping platform dependent
T_UTF8   = 't'  # utf-8 unicode
# --- struct format characters ---
T_CHAR   = 'c'  # char             string len=1
T_INT1   = 'b'  # signed char      integer
T_UINT1  = 'B'  # unsigned char    integer
T_INT2   = 'h'
T_UINT2  = 'H'
T_INT4   = 'l'
T_UINT4  = 'L'
T_PTR    = 'P'  # void *
T_INT8   = 'q'
T_UINT8  = 'Q'
T_FLOAT  = 'f'  # 4 byte IEEE float
T_DOUBLE = 'd'  # 8 byte IEEE double

# dict mapping datamap types to Adabas format
# Note: some types are not (yet) supported T_MAP
DM2ADAF = {T_STRING:'A', T_BYTE:'', T_UNPK:'U',
           T_PACK:'P', # T_DMAP
           T_CHAR:'A', T_INT1:'B', T_UINT1:'B',
           T_INT2:'F', T_UINT2:'B', T_INT4:'F',
           T_UINT4:'B', # T_PTR
           T_INT8:'F', T_UINT8:'B', T_FLOAT:'G', T_DOUBLE:'G',
           T_UTF16:'W', T_UTF8:'A'}

# dict mapping datamap types to Adabas format
# Predict knows also 'I', 'LA', 'LO', 'D', 'T'
# Note: some types are not (yet) supported T_MAP
PRD2DM = {  'A': T_STRING,
            'B': T_BYTE,
            'F': T_FLOAT,
            'I': T_INT1,
            'N': T_UNPK,
            'P': T_PACK,
            'W': T_UTF16, #??
            # 'LA': T_STRING, # long alpha   / also binary?
            # 'LO': T_STRING, # long LOB    / also binary?
            }

def prd2dm(prdformat,length=0):
    """get Datamap field code from Predict format
    """
    f = PRD2DM.get(prdformat,'')
    if f == T_INT1 and length > 1:
        if length == 2:
            return T_INT2
        elif length == 4:
            return T_INT4
        elif length == 8:
            return T_INT8
    elif f == T_FLOAT and length == 8:
        return T_DOUBLE
    return f


LEFT_ALIGNED = (T_STRING, T_UTF16, T_UTF8)

# additional field options (opt)
T_IN   = 1  # write access
T_OUT  = 2  # read access
T_INOUT= 3  # read/write
T_STCK = 4  # convert store clock - use with Uint4 or Uint8
T_HEX  = 8  # display hex (limited to 8 bytes)
T_NONE = 16 # dummy/filler field, do not display in dprint()
T_EBCDIC = 32 # data is EBCDIC
T_VAR0 = 64   # Variable
T_VAR1 = 128  # Variable 1 byte  incl.
T_VAR2 = 256  # Variable 2 bytes incl.
T_VAR4 = 512  # Variable 4 bytes incl.
T_DT = 1024   # convert to/from datetime() object
T_NWBO = 2048 # Net-work byte order alias big-endian
T_GMT = 4096  # use in conjunction with T_STCK if value is in GMT
              # and not local time
T_MUPE = 2**13 # MUPE indicator in getpossiz(), not used in field defn

NATIVEBO='='  # struct format character: native, standard size, no alignment
NETWORKBO='!' # struct format character: big-endian, standard size, no alignment
NATIVEBO_ALIGNED='@' # struct format character: big-endian, standard size, natvie alignment

if sys.byteorder =='little':
    UTF16_NATIVE = 'utf_16_le'
else:
    UTF16_NATIVE = 'utf_16_be'



def field( name, fmt, size, **options):
    """Defines a field element.

    A field element is used in the list of fields in a datamap class.
    It defines mainly name, format and size.

    Valid keywords for options i.e. keyword = value list:

    :param opt: define extra formatting e.g. (T_STCK, T_HEX) - see also below
        on variable length strings

        To define fields in other data architecture:

        - **T_EBCDIC**  field data is in EBCDIC (String, Packed, Unpacked, Char)
        - **T_NWBO**    field data is big-endian or high-order-byte-first
          rather than native byte-order

        To define this for all fields in a datamap use the setting on the
        datamap level:

            Datamap(..., ebcdic=1, byteorder=NETWORKBO)

        To define variable length strings:

            opt in (T_VAR0, T_VAR1, T_VAR2, T_VAR4)

        for AAL length reference, 1, 2, 4 byte length prefix

        To cumulate options join them with bitwise-or '|'

    :param fn: define Adabas field name. This is used in genfb() and
        getfndef() functions to generate the format buffer related
        to the datamap.

    :param pos: define **new offset** from start of datamap

    :param repos: reposition **relative** from current position

    :param caption: field text for dprint() or lprint()

    :param ppfunc: formatting function for dprint()

    :param colsize: column size for lprint()

    :param dt: 'DATETIME' (= Adabas datetime editmask) is used to map
        to/from Python datetime object (currently only DATETIME)

    :param sizefunc: reference to size function if T_VAR0 (AAL)
    """
    return (name, fmt, size, options)


def Periodic(dmap, occurs=0):
    """ Define periodic group with a datamap dmap on the fields of the group
    keywords for options:

    :param occurs: number of repetitions of group, parameter may be a function.

        If function returns -1 or -2: byte position(s) before
        the field contain the actual count. For example::

            occurs=lambda:-2

    """
    dmap.occurs=occurs
    if callable(occurs):
        plen = 0                 # length of periodic group dynamic
    else:
        plen = dmap.dmlen*occurs # length of periodic group fixed
    if debug: print( 'Periodic definition', dmap.dmname, 'T_DMAP', plen, dict(submap=dmap,occurs=occurs))
    return (dmap.dmname, T_DMAP, plen, dict(submap=dmap,occurs=occurs))
    # Multiple() instance will be created during init of enclosing Datamap
    # i.e. Multiple(self,dmap.dmname,occurs=occurs,submap=dmap)

def String( name, size, **options):
    return field(name, T_STRING, size, **options)

def Unicode( name, size, **options):
    """size in unicode characters * 2 = size in bytes """
    return field(name, T_UTF16, size, **options)

def Utf8( name, size, **options):
    return field(name, T_UTF8, size, **options)

def Packed( name, size, **options):
    return field( name, T_PACK, size, **options)

def Unpacked( name, size, **options):
    return field( name, T_UNPK, size, **options)

def Bytes( name, size, **options):
    "Byte string (binary)"
    return field(name, T_BYTE, size, **options)

def Filler( name, size):
    "Byte filler"
    return field(name, T_BYTE, size, opt=T_NONE)

def Char( name, **options):
    return field( name, T_CHAR, 1, **options)

def Int1( name, **options):
    return field( name, T_INT1, 1, **options)

def Uint1( name, **options):
    return field( name, T_UINT1, 1, **options)

def Int2( name, **options):
    return field( name, T_INT2, 2, **options)

def Uint2( name, **options):
    return field( name, T_UINT2, 2, **options)

def Int4( name, **options):
    return field( name, T_INT4, 4, **options)

def Uint4( name, **options):
    return field( name, T_UINT4, 4, **options)

def Int8( name, **options):
    return field( name, T_INT8, 8, **options)

def Uint8( name, **options):
    return field( name, T_UINT8, 8, **options)

def Float( name, **options):
    return field( name, T_FLOAT, 4, **options)

def Double( name, **options):
    return field( name, T_DOUBLE, 8, **options)

def Pointer( name, **options):
    return field( name, T_PTR, struct.calcsize('P'), **options)



class DatamapError(Exception):
    """Error Class for Datamap Exceptions

    :attr string: Adabas response string
    :attr dmap: Datamap instance where the error occurred

    Usage example:

    .. code-block:: python

       try:
           raise DatamapError('error text', dmap)
       except DatamapError as e:
           print( 'DatamapError', e.value, e.__class__)
           dump(e.dmap)
    """

    def __init__(self, value, dmap):
        self.value = value
        self.dmap = dmap
    def __str__(self):
        return repr(self.value)


sbuf=Abuf(256) # get work buffer

U0=b'0'*29             # nulls
P0=b'\x00'*14+b'\x0c'  # nulls e.g. for length = 3  P0[-3:]

# global for all datamap instances
# overrides any instance settings if 1 (=True)
dataIsEbcdic=0
byteOrder=NATIVEBO

def setEbcdic(yesno):
    """set EBCDIC data in map
    :param yesno: True or False
    """
    global dataIsEbcdic
    dataIsEbcdic = yesno
    if debug:
        print( 'setEbcdic()' , yesno)

def setNativeByteOrder():
    global byteOrder
    byteOrder = NATIVEBO
    if debug:
        print( 'setNativeByteOrder()' , byteOrder)

def setNetworkByteOrder():
    global byteOrder
    byteOrder = NETWORKBO
    if debug:
        print( 'setNetworkByteOrder()', byteOrder)


def bit_str(b, istrList):
    """
    Produce readable print of integer or single byte input

    :param b: byte or integer
    :param istrList: list of tuples containing the bits
        and the corresponding string.

        Optionally a third element of a tuple may be a
        string that is taken as default when the bits are
        all not set.

    Examples::

      >>> from adapya.base.datamap import bit_str
      >>> print( bit_str(b'\\x03',[(1,'one'),(2,'two')]))
      one,two

      >>> print( bit_str(b'\\x03',[(3,'three'),(1,'one'),(2,'two')]))
      three

      >>> print( bit_str(b'\\x06',[(3,'three'),(1,'one'),(2,'two')]))
      two,X'04'

      >>> bit_str(b'\\x86',[(2,'two'),(0x80,'negative','positive')])
      "two,negative,X'04'"

      >>> bit_str(b'\\x00',[(2,'two'),(0x80,'negative','positive')])
      'positive'

    """
    r = []

    if isinstance(b, int):
        x=b
    else: # string or b'' type
        x, = struct.unpack('=B', b)

    if istrList == None:
        istrList=()

    for item in istrList:
        if len(item) == 3:      # check if string given if i bits not set
            i, s, defs = item
        else:
            defs = ''
            i, s = item

        if (x&i)==i:            # all i bits set in x
            x^=i                # reset used bits
            r.append(s)
        elif (x&i) == 0 and defs: # no bit is set and a default string is given
            r.append(defs)

    if x:
        r.append("X'%02X'" % x) # add hex values w/o symbols

    return ','.join(r)          # return '' or symbols separated by '+'


def flag_str(flag,flist):
    """ This is similar to bit_str but only lists the elements
    for which a definition exists.

    :param flag: integer
    :param flist: list of (integer, string) tuples

    Example::

        >>> flag_str(3, ((1,'one'),(2,'two'),(4,'four')))
        'one,two'
    """
    ss=[]
    for (x,s) in flist:
        if flag & x:
            ss.append(s)
    return ','.join(ss)

def flag_strc(flag,flist):
    """Similar to flag_str but compressed i.e. without commas
    each flag bit is represented by a string or a '.'

    :param flag: integer
    :param flist: list of (integer, string) tuples

    Example::

        >>> flag_strc(5, ((1,'O'),(2,'T'),(4,'F')))
        'O.F'
    """
    ss=[]
    for (x,s) in flist:
        if flag & x:
            ss.append(s)
        else:
            ss.append('.')
    return ''.join(ss)

def str_str(s, strdict):
    """ Return a readable string from the value
    if it exists otherwise the hex value for integers or blank

    :param s: value (could be string or int: key for dict)
    :param strdict: dict containing the interpretation

    Examples::

        >>> str_str('quark', {'quark':'one',2:'two',4:'four'})
        'one'
        >>> str_str(3, {1:'one',2:'two',4:'four'})
        "X'03'"
    """
    if s in strdict:
        return strdict[s]
    else:
        if type(s) == type(1):  # integer
            return  "X'%02X'" % s
        else:
            return ''

def list_str(i, istrList):
    """Produce readable print from list

    :param i:  position in list
    :param istrList: List of strings
    """
    if 0<= i < len(istrList):
        return istrList[i]
    else:
        return ''

def list_stri(i, istrList):
    """Produce readable print from list

    :param i:  position in list
    :param istrList: List of strings
    """
    if 0<= i < len(istrList):
        return istrList[i]
    else:
        return '%d' % i

def dpack(dmap, key, data, indx=0):
    global dataIsEbcdic
    global byteOrder

    ftype, start, size, inout, fdic  = dmap.keydict[key]

    start += dmap.offset + indx*size
    stop = start+size
    ebcdic =  inout&T_EBCDIC or dmap.__dict__['ebcdic'] or dataIsEbcdic

    bo = NETWORKBO if (inout&T_NWBO) else \
           dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder is None take global

    if debug:
        print( INDENT, '%s.dpack(%s,indx=%r) size=%d start=%d stop=%d, inout=%d, fdic=%r, bo=%s' % (
                dmap.dmname, key, indx, size, start, stop, inout, fdic, bo))

    if not (inout & T_IN):
        raise DatamapError("Field %s must not be modified" % key, dmap)

    if ftype == T_STRING:
        fieldlen = stop-start
        # print( 'datamap setattr: key=%s, data=%s' % (key,repr(data)), type(data))
        espace = dmap.__dict__['espace']
        enc    = dmap.__dict__['encoding']
        if sys.hexversion >= 0x3010100: # PY3
            if isinstance(data, str):
                data = data.encode(enc)
            elif isinstance(data, (bytes,bytearray)):
                if ebcdic:
                    data = str2ebc(data)
            else:
                data = repr(data)
        else:   # PY2
            if isinstance(data, str):
                if ebcdic:
                    data = str2ebc(data)
            elif isinstance(data, unicode):
                data = data.encode(enc)
            else:
                data = repr(data)

        mlen = min(len(data),fieldlen)
        dmap.buffer[start:start+mlen] = data[0:mlen]

        if fieldlen > mlen: # fill rest of field with space character
          try:
            dmap.buffer[start+mlen:stop] = (fieldlen-mlen)* espace
          except:
            print('espace=%r, start=%d, stop=%d, mlen=%d, fieldlen=%d' % (
                espace,start,stop,mlen,fieldlen))
            print(dir(dmap.buffer))
            # raise

    elif ftype == T_UTF16:
        fieldlen = stop - start
        if not isinstance(data,type(u'')): # need to first convert to unicode
            data=data.decode(dmap.encoding)
        datalen=len(data)*2  # length in bytes
        minlen=min(datalen,fieldlen)
        padlen=(fieldlen-minlen)//2
        if bo==NETWORKBO:
            dmap.buffer[start:stop]=(data[0:minlen//2]+u' '*padlen
                 ).encode('utf_16_be')
        else:
            #print( 'start=%d, stop=%d, minlen=%d, padlen=%d' % (
            #    start, stop, minlen, padlen)
            #dump( (data[0:minlen]+u' '*padlen).encode(UTF16_NATIVE))

            dmap.buffer[start:stop]=(data[0:minlen//2]+u' '*padlen
                ).encode(UTF16_NATIVE)

    elif ftype == T_UTF8:
        fieldlen = stop - start
        # print( 'datamap setattr: key=%s, data=%s' % (key,repr(data)), type(data))
        sutf8 = str(data).encode('utf8') if sys.hexversion >= 0x3010100 \
            else unicode(data).encode('utf8')
        datalen=len(sutf8)
        minlen=min(datalen,fieldlen)
        padlen=(fieldlen-minlen)
        dmap.buffer[start:stop]=sutf8[0:minlen]+b' '*padlen

    elif ftype == T_PACK:   # packed decimal
        fieldlen = stop - start

        if ebcdic:
            sign = b'f'
        else:
            sign = b'c'

        if inout & T_DT:    # converting from datetime object
            if data == None:
                bdata = U0[:fieldlen]                 # None value is stored as zero

            elif fdic.get('dt', None) == 'DATETIME' and isinstance(data, datetime):
                bdata = b'%04d%02d%02d%02d%02d%02d' % (data.year, data.month, data.day,
                    data.hour, data.minute, data.second )
            elif fdic.get('dt', None) == 'TIMESTAMP' and isinstance(data, datetime):
                bdata = b'%04d%02d%02d%02d%02d%02d%06d' % (data.year, data.month, data.day,
                    data.hour, data.minute, data.second, data.microsecond )
            elif fdic.get('dt', None) == 'DATE' and isinstance(data, (date, datetime)):
                bdata = b'%04d%02d%02d' % (data.year, data.month, data.day)
            elif fdic.get('dt', None) == 'TIME' and isinstance(data, time):
                bdata = b'%02d%02d%02d' % (data.hour, data.minute, data.second)
            elif fdic.get('dt', None) == 'NATDATE' and isinstance(data, (date, datetime)):
                if sys.hexversion >= 0x3010100: # PY3
                    bdata = bytes(str(date2natdate(data.year, data.month, data.day)),'ascii')
                else:
                    bdata = bytes(date2natdate(data.year, data.month, data.day))
            elif fdic.get('dt', None) == 'NATTIME' and isinstance(data, datetime):
                if sys.hexversion >= 0x3010100: # PY3
                    bdata = bytes(str(timestamp2nattime(data.year, data.month, data.day,
                            data.hour, data.minute, data.second, data.microsecond)),'ascii')
                else:
                    bdata = bytes(timestamp2nattime(data.year, data.month, data.day,
                            data.hour, data.minute, data.second, data.microsecond))
        else:
            if data < 0:
               idata = - int(data)
               sign = b'd'
            else:
               idata = int(data)

            if sys.hexversion >= 0x3010100: # PY3
                bdata = bytes(str(idata),'ascii')         # bytes() does not append L on long integer
            else:
                bdata = bytes(idata)

        datalen = len(bdata)//2 + 1

        if debug:
            print(datalen,len(bdata),bdata[:16], fieldlen)

        if not len(bdata) % 2:  # 22 -> 022F
            nibble =b'0'
        else:                 # 1  -> 1F
            nibble = b''
        if datalen > fieldlen:
            raise DatamapError('datamap setattr Packed: data size %d exceeds field size %d, key=%s, data=%s' \
                % (datalen,fieldlen,key,bdata[:16]+b'...'), dmap)
        elif datalen < fieldlen:
            zeros = (fieldlen - datalen) * b'00'
        else:
            zeros = b''
        if debug:
            print( 'start=%d, stop=%d, len=%d, zeros=%r, nibble=%r, bdata=%r, sign=%r, %r' %(
                    start, stop, stop-start, zeros, nibble, bdata, sign, unhexlify(zeros+nibble+bdata+sign)) )
            dump(dmap.buffer[start:stop])
        dmap.buffer[start:stop]=unhexlify(zeros+nibble+bdata+sign)


    elif ftype == T_UNPK:   # unpacked decimal
        fieldlen=stop-start
        if debug and ftype==T_UNPK: print('dpack UNPK: fieldlen=%d' % fieldlen)
        sign=1

        if inout & T_DT:    # converting from datetime object
            if data == None:
                bdata = U0[:fieldlen]                 # None value is stored as zero
            elif fdic.get('dt', None) == 'DATETIME' and isinstance(data, datetime):
                bdata = b'%04d%02d%02d%02d%02d%02d' % (data.year, data.month, data.day,
                    data.hour, data.minute, data.second )
            elif fdic.get('dt', None) == 'TIMESTAMP' and isinstance(data, datetime):
                bdata = b'%04d%02d%02d%02d%02d%02d%06d' % (data.year, data.month, data.day,
                    data.hour, data.minute, data.second, data.microsecond )
            elif fdic.get('dt', None) == 'DATE' and isinstance(data, (date, datetime)):
                bdata = b'%04d%02d%02d' % (data.year, data.month, data.day)
            elif fdic.get('dt', None) == 'TIME' and isinstance(data, dtime):
                bdata = b'%02d%02d%02d' % (data.hour, data.minute, data.second)
            elif fdic.get('dt', None) == 'NATDATE' and isinstance(data, (date, datetime)):
                bdata = str(date2nattime(data.year, data.month, data.day))
            elif fdic.get('dt', None) == 'NATTIME' and isinstance(data, datetime):
                bdata = str(timestamp2nattime(data.year, data.month, data.day,
                            data.hour, data.minute, data.second, data.microsecond))
        else:
            if data < 0:
                sign = -1
                idata = - int(data)
                bdata = str(idata).encode() # long integers don't have L appended (but with repr())
                if not ebcdic:
                    last = struct.pack('=B', 0x70 + idata%10) # last digit is a digit '0'-'9'
                    bdata = bdata[:-1] + last             # modify last byte
            else:
                idata = int(data)
                bdata = str(idata).encode() # long integers don't have L appended (but with repr())

        datalen=len(bdata)

        if debug and ftype==T_UNPK: print('dpack UNPK: data=%s datalen=%d' % (bdata,datalen))

        if ebcdic:
            zero=b'\xf0'
            sbuf[0:datalen] = bdata
            asc2ebc(sbuf,0,datalen)

            if sign < 0:  # fix last position if negative
                sbuf[datalen-1] = chr(ord( sbuf[datalen-1] )& 0xdf)  # negative is 0xD-

            bdata=sbuf[:datalen]
        else:
            zero=b'0'

        if datalen > fieldlen:
            raise DatamapError('datamap setattr Unpacked: data size %d exceeds field size %d, key=%s, data=%s, odata=%s' \
                % (datalen,fieldlen,key,bdata,repr(data)), dmap)
        elif datalen < fieldlen:
            zeros = (fieldlen - datalen) * zero
        else:
            zeros = b''
        if debug and ftype==T_UNPK:
            print(type(zeros), zeros, type(bdata), bdata, start, stop)
        dmap.buffer[start:stop]=zeros+bdata

    elif ftype== T_BYTE:
        fieldlen=stop-start
        # print( type(data))
        if not data:    # zero or empty bytes
            dmap.buffer[start:stop]=fieldlen*b'\x00'

        elif isinstance(data, (int, type(2**32))):  # PY2/3
            if data < 0:
                raise DatamapError('datamap setattr BYTE: data is negative key=%s, data=%s, length=%d' \
                    % (key,repr(data),stop-start), dmap)
            if fieldlen == 1:
                if data & ~0xff:
                    raise DatamapError('datamap setattr BYTE: data exceeds field size %d, key=%s, data=%s' \
                        % (stop-start,key,repr(data)), dmap)
                dmap.buffer[start:stop]=struct.pack('=B', data)
            elif fieldlen == 2:
                if data & ~0xffff:
                    raise DatamapError('datamap setattr BYTE: data exceeds field size %d, key=%s, data=%s' \
                        % (stop-start,key,repr(data)), dmap)
                dmap.buffer[start:stop]=struct.pack(bo+'H', data)
                if 0:
                    print('datamap dpack() BYTE', bo, data)
                    dump(dmap.buffer[start:stop])
            elif fieldlen == 4:
                if data & ~0xffffffff:
                    raise DatamapError('datamap setattr BYTE: data exceeds field size %d, key=%s, data=%s' \
                        % (stop-start,key,repr(data)), dmap)
                dmap.buffer[start:stop]=struct.pack(bo+'L', data)
            elif fieldlen==8:
                if data & ~0xffffffffffffffff:
                    raise DatamapError('datamap setattr BYTE: data exceeds field size %d, key=%s, data=%s' \
                        % (stop-start,key,repr(data)), dmap)
                dmap.buffer[start:stop]=struct.pack(bo+'Q', data)
            else:
                xdata=hex(data)[2:]  # remove 0x prefix
                if xdata[-1]=='L':
                    xdata=xdata[:-1] # remove Long int indicator
                if len(xdata)%2==1: # hexstring uneven
                    xdata='0'+xdata
                bdata=unhexlify(xdata)
                if len(bdata) > fieldlen:
                    raise DatamapError('datamap setattr BYTE: data exceeds field size %d, key=%s, data=%s' \
                        % (stop-start,key,repr(data)), dmap)
                if len(bdata) < fieldlen:
                    bdata = b'\x00' * (fieldlen-len(bdata)) + bdata   # prepend binary zeros
                if bo == NATIVEBO and sys.byteorder =='little':
                    dmap.buffer[start:stop]=swap(bdata)
                else:
                    dmap.buffer[start:stop]=bdata

        else:
            datalen=len(data)
            if fieldlen == datalen:
                dmap.buffer[start:stop]=data
            elif fieldlen > datalen:
                dmap.buffer[start:start+datalen]=data
                dmap.buffer[start+datalen:stop]=(fieldlen-datalen)*b'\x00'
            else: #  fieldlen < datalen
                dmap.buffer[start:stop]=data[0:fieldlen]

    elif ftype == T_UINT1:
        if 0 <= data <= 0xff:
            dmap.buffer[start:stop]=struct.pack('B', data) # UINT1
        else:
            raise DatamapError('datamap setattr Uint1: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
    elif ftype == T_INT1:
        if debug:
            dump(dmap.buffer[start:stop])
            print(dir(dmap.buffer))
        if -0x80 <= data <= 0x7f:
            dmap.buffer[start:stop]=struct.pack('b', data) # INT1
        else:
            raise DatamapError('datamap setattr Int1: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
        # dmap.buffer[start:stop]=struct.pack('=B', data) # '=B' or '=b'
    elif ftype in T_UINT2:
        if 0 <= data <= 0xffff:
            if inout & T_NWBO:
                bo = NETWORKBO
            else:
                bo = dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder in None take global
            dmap.buffer[start:stop]=struct.pack(bo+'H', data) # UINT2
        else:
            raise DatamapError('datamap setattr Uint2: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
    elif ftype == T_INT2:
        if -0x8000 <= data <= 0x7fff:
            if inout & T_NWBO:
                bo = NETWORKBO
            else:
                bo = dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder in None take global
            dmap.buffer[start:stop]=struct.pack(bo+'h', data) # INT2
        else:
            raise DatamapError('datamap setattr Int2: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
    elif ftype == T_UINT4:
        if inout & T_DT:    # converting from datetime object
            if data == None:
                data = 0                 # None value is stored as zero
            elif fdic.get('dt', None) == 'UNIXTIME' and isinstance(data, datetime):
                data = datetime2unixtime(data.year, data.month, data.day,
                                         data.hour, data.minute, data.second )

        if 0 <= data <= 0xffffffff:
            if inout & T_NWBO:
                bo = NETWORKBO
            else:
                bo = dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder in None take global
            dmap.buffer[start:stop]=struct.pack(bo+'L', data) # UINT4
        else:
            raise DatamapError('datamap setattr Uint4: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
    elif ftype == T_INT4:
        if -0x80000000 <= data <= 0x7fffffff:
            if inout & T_NWBO:
                bo = NETWORKBO
            else:
                bo = dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder in None take global
            dmap.buffer[start:stop]=struct.pack(bo+'l', data) # INT4
        else:
            raise DatamapError('datamap setattr Int4: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
    elif ftype == T_UINT8:
        if 0 <= data <= 0xffffffffffffffff:
            dmap.buffer[start:stop]=struct.pack(bo+'Q', data) # UINT8
        else:
            raise DatamapError('datamap setattr Uint8: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
    elif ftype == T_INT8:
        if inout & T_DT:    # converting from datetime object
            if data == None:
                data = 0                 # None value is stored as zero
            elif fdic.get('dt', None) == 'XTIMESTAMP' and isinstance(data, datetime):
                data = utc2xts(data.year, data.month, data.day,
                    data.hour, data.minute, data.second, data.microsecond )

        if -0x8000000000000000 <= data <= 0x7fffffffffffffff:
            if inout & T_NWBO:
                bo = NETWORKBO
            else:
                bo = dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder in None take global
            dmap.buffer[start:stop]=struct.pack(bo+'q', data) # INT8
        else:
            raise DatamapError('datamap setattr Int8: data exceeds field size %d, key=%s, data=%s' \
                % (stop-start,key,repr(data)), dmap)
    elif ftype == T_CHAR:
        enc    = dmap.__dict__['encoding']
        if sys.hexversion >= 0x3010100: # PY3
            if not isinstance(data, (bytes,bytearray,str)):
                data = repr(data)
            if isinstance(data, str):
                data = data.encode(enc)
        else:   # PY2
            if not isinstance(data, (str,unicode)):
                data = repr(data)
            elif isinstance(data, unicode):
                data = data.encode(enc)         # already converted to EBCDIC
            elif ebcdic:
                data = str2ebc(data)
        if len(data) > 1:
            raise DatamapError('datamap setattr Char: data exceeds 1 byte, key=%s, data=%s' \
                % (key,repr(data)), dmap)
        dmap.buffer[start:start+1] = data
    else:
        bo = dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder in None take global
        # print( bo, ftype, data, start, stop)
        dmap.buffer[start:stop]=struct.pack(bo+ftype, data)
        if ftype == T_CHAR and ebcdic:
            asc2ebc(dmap.buffer,start,stop)


def dunpack(dmap, key, indx=0, possiz=None):
    """ datamap unpack

    :param index: if index is > 0: indexed access with constant field size>0
        if possiz not given
    :param possiz: list of (pos, size) tuple indexed by index

    """

    global dataIsEbcdic, sbuf

    if not dmap.buffer:
        raise DatamapError('dunpack(): no buffer assigned to datamap %r, key=%s, index=%d, possiz=%r' \
                % (dmap, key, indx, possiz))

    ftype, start, size, inout, fdic = dmap.keydict[key]

    if possiz:
        pos, size = possiz[indx]
        start+=dmap.offset + pos
        stop=start+size
    else:
        start+=dmap.offset + indx*size
        stop=start+size

    if debug and indx <2:
        print( '%s.dunpack(%s,indx=%r) size=%d start=%d stop=%d offset=%d' % (
            dmap.dmname, key, indx, size, start, stop, dmap.offset))
        print( dmap.keydict[key])
        print( '\tpossiz=%r' % possiz)

    if ftype == T_STRING:
        enc = dmap.__dict__['encoding']
        if sys.hexversion >= 0x3010100:
            if not inout&T_EBCDIC:
                return dmap.buffer[start:stop].decode(encoding=enc,errors='replace').rstrip(' ')
            else:
                return dmap.buffer[start:stop].decode(encoding='cp037').rstrip(' ')
        else:
            espace = dmap.__dict__['espace']

            if dmap.__dict__['ebcdic'] or dataIsEbcdic or inout&T_EBCDIC:
                try:
                    sbuf[0:size]=dmap.buffer[start:stop]
                except: # ValueError:
                    print('ValueError: size=%d start=%d stop=%d len(sbuf)=%d len(buffer)=%d key=%s indx=%d' %
                        (size, start, stop, len(sbuf), len(dmap.buffer), key, indx))
                    dump(dmap.buffer)

                    if len(sbuf) < size:  # temp buffer too small?
                        _t = sbuf
                        sbuf = Abuf(size) # reallocate in size needed
                        del _t
                        sbuf[0:size]=dmap.buffer[start:stop]
                    else:
                        raise
                ebc2asc(sbuf,0,size)
                return sbuf[0:size].rstrip(' ') # no other whitespace
            else:
                if debug:
                    print('value=%r' % dmap.buffer[start:stop].rstrip(' '))
                return dmap.buffer[start:stop].rstrip(' ')

    elif ftype == T_UTF16:  # Unicode
        global byteOrder
        if dmap.__dict__['byteOrder']==NETWORKBO or \
                            byteOrder==NETWORKBO:
            return dmap.buffer[start:stop].decode('utf_16_be').rstrip(' ')
        return dmap.buffer[start:stop].decode(UTF16_NATIVE).rstrip(' ')

    elif ftype == T_UTF8:   # returns unicode string
        _ret=u' '
        try:
            _ret =  dmap.buffer[start:stop].decode('utf_8', 'ignore')
        except: # UnicodeDecodeError:
            _ret = b'Invalid UTF8 string '+hexlify(dmap.buffer[start:stop]).decode('utf_8')
        return _ret.rstrip(' ')

    elif ftype == T_BYTE:
        return dmap.buffer[start:stop]

    elif ftype == T_PACK:   # packed decimal
        sbuf[0:size]=dmap.buffer[start:stop]
        # supports also ebcdic packed
        sign=1
        hexbytes = hexlify(sbuf[0:size]) # bytes type in PY3
        #if sys.hexversion >= 0x3010100:
        #    hexstr = hexbytes.decode()
        #else:
        #    hexstr = hexbytes
        #if hexstr[-1:].upper() in 'BD':
        if hexbytes[-1:].upper() in b'BD':
            sign=-1
        if not (inout & T_DT):    # datetime output
            return sign * int(hexbytes[:-1])
        else:
            #size = len(hexstr)-1
            size = len(hexbytes)-1
            sbuf[0:size] = hexbytes[:-1]

            if sbuf[0:size] == U0[:size]:               # Any datetime 0 value is returned as None
                return None
            if fdic.get('dt', None) in ('DATETIME','TIMESTAMP'):
                return datetime(*str2dt(sbuf[1:size]))
            elif fdic.get('dt', None) == 'DATE':
                return date(int(sbuf[1:5]), int(sbuf[5:7]), int(sbuf[7:9]))
            elif fdic.get('dt', None) == 'TIME':
                return dtime(int(sbuf[1:3]), int(sbuf[3:5]), int(sbuf[5:7]))
            elif fdic.get('dt', None) == 'NATDATE':
                return date(*natdate2date(int(sbuf[0:size])))
            elif fdic.get('dt', None) == 'NATTIME':
                return datetime(*nattime2timestamp(int(sbuf[0:size])))

    elif ftype == T_UNPK:   # unpacked decimal
        if 0:
            print('sbuf',sbuf[:size],'size',size)
            print('buffer',dmap.buffer[start:stop],'start',start,'stop', stop)
            print(dmap.keydict[key], possiz)
        sbuf[0:size]=dmap.buffer[start:stop]

        if dmap.__dict__['ebcdic'] or dataIsEbcdic  or inout & T_EBCDIC:
            if size>1:
                ebc2asc(sbuf,0,size-1)
            hx = hexlify( sbuf[size-1:size] ).upper()   # b'F',b'9'
            zone,lastdig = hx[0:1],hx[-1:]
            # print('hx=%r, lastdig=%r, zone=%r' % (hx,lastdig,zone,))
            if zone in b'BD':
                sbuf[size-1:size]=unhexlify(b'7'+lastdig)
            else:
                sbuf[size-1:size]=unhexlify(b'3'+lastdig)

        if inout & T_DT:    # datetime output
            if sbuf[0:size] == U0[:size]:               # Any datetime 0 value is returned as None
                return None
            if fdic.get('dt', None) in ('DATETIME','TIMESTAMP'):
                return datetime(*str2dt(sbuf[0:size]))
            elif fdic.get('dt', None) == 'DATE':
                return date(int(sbuf[0:4]), int(sbuf[4:6]), int(sbuf[6:8]))
            elif fdic.get('dt', None) == 'TIME':
                return dtime(int(sbuf[0:2]), int(sbuf[2:4]), int(sbuf[4:6]))
            elif fdic.get('dt', None) == 'NATDATE':
                return date(*natdate2date(int(sbuf[0:size])))
            elif fdic.get('dt', None) == 'NATTIME':
                return datetime(*nattime2timestamp(int(sbuf[0:size])))

        sign=1
        if sys.hexversion >= 0x3010100:
            lastdig = sbuf[size-1:size]
            if lastdig > b'9':               # '9' or  'y' (negative) = b'\x39' or b'\x79' (negative)
                sign=-1
            lastdig = hexlify(lastdig)[-1:]   # b'9'
            return sign * int( (sbuf[:size-1]+lastdig).decode('ascii'))
        else:
            lastdig = sbuf[size-1:]
            if lastdig > b'9':
                sign=-1
            lastdig = hexlify(lastdig)[-1:]

            return sign * int(sbuf[:size-1]+lastdig)

    else: # elif ftype == T_INT4:
        if inout & T_NWBO:
            bo = NETWORKBO
        else:
            bo = dmap.__dict__['byteOrder'] or byteOrder  # if instance byteOrder in None take global
        try:
            ii, = struct.unpack(bo+ftype, dmap.buffer[start:stop]) # '=l'
        except: # struct.unpack error:
            print( 'Invalid data for struct.unpack() type=%s, offset=%4X, length=%d' % (
                        ftype, start-dmap.offset, stop-start))
            dump(dmap.buffer[start:stop])
            raise
        # print( 'getattr byteOrder+ftype', byteOrder+ftype, key, ii, type(ii))
        if ftype == T_CHAR and \
               ( dmap.__dict__['ebcdic'] or dataIsEbcdic or inout&T_EBCDIC):
            return str2asc(ii)
        elif inout & T_DT:
            if fdic.get('dt', None)=='UNIXTIME' and ftype in (T_INT4, T_INT8) :
                return datetime(*unix2utc(ii))
            elif fdic.get('dt', None)=='XTIMESTAMP' and ftype==T_INT8 :
                return datetime(*xts2utc(ii))
        else:
            return ii


class Multiple(object):
    """ Initialize with Multiple(supermap, key, occurs [, submap])
    if 'occurs' is a function it will be called in prepare()
    to determine the actual occurrences before field access

    This class is used internally when defining fields with occurs>0
    """
    def __init__(self, supermap, superkey, occurs=1, submap=None):
            object.__setattr__(self,'supermap',supermap)    # datamap which defines element
            object.__setattr__(self,'superkey',superkey)    # key of element in supermap
            object.__setattr__(self,'submap',submap)        # optional datamap (e.g. Periodic)
            # object.__setattr__(self,'startpos',datamap.keydict[superkey][1])
            if callable(occurs):
                object.__setattr__(self,'occfunc',occurs)
                object.__setattr__(self,'occurs',0)
            else:
                object.__setattr__(self,'occurs',occurs)
            object.__setattr__(self,'possiz',None)


    def __getitem__(self,indx):
        " currently only integers as index, no slice parameter!!!"

        if debug and indx<2:  # debug
            if isinstance(self, Multiple):
                print( INDENT, '%s.%s.__getitem__(%d) ' % (self.supermap.dmname, self.superkey, indx))
            else:
                print( INDENT, '%s.__getitem__(%d)'  % (self.dmname, indx))

        if 0 <= indx < self.occurs:
            if self.submap:
                sm = self.submap
                dm = self.supermap
                startpos=dm.keydict[self.superkey][1]  # current position
                sm.buffer=dm.buffer # copy buffer from enclosing datamap
                if self.possiz:                   # possiz list created in prepare()
                    pos, siz = self.possiz[indx]
                    sm.offset=dm.offset+startpos+pos
                else:
                    sm.offset=dm.offset+startpos+indx*sm.dmlen
                return sm
            else:
                return dunpack(self.supermap, self.superkey, indx=indx, possiz=self.possiz)

        raise StopIteration('Field %s.%s index %d is out of range 0 - %d' % (
             self.supermap.dmname, self.superkey, indx, self.occurs-1))

    def __setitem__(self,indx, value):
        " currently only integers as index, no slice parameter!!!"
        # print( 'set one value indexed %s(%d)' % (self.superkey, indx))
        if self.submap:
            raise DatamapError('Value assignment to datamap %s field %s[%d] invalid' % (
                self.supermap.dmname, self.superkey, indx), self.supermap )

        if 0 <= indx < self.occurs:
            dpack(self.supermap, self.superkey, value, indx=indx)
        else:
            raise StopIteration('Field %s.%s[%d] index out of range 0 : %d' % (
                self.supermap.dmname, self.superkey, indx, self.occurs))

        return self.occurs


class Datamap(object):
    """
    Datamap maps attributes to fields located in buffer+offset.

    This is similar to a struct in C and involves un-/packing to/from
    Python objects.

    It is used to handle data structures external to Python.

    Internally, attributes are defined as tuples per field list parameter
    and stored as keys in the dict 'keydict' that contains tuples of

        - data_type,
        - slice_start,
        - slice_length,
        - read/write ability
        - function or method to convert to readable string

    The sequence of fields is maintained in the the list 'keylist'

    Attribute tuples are generated with a list of data type specific
    functions. Each defines the attribute name and other field options

    Examples::

    >>> from adapya.base.defs import Abuf
    >>> from adapya.base.datamap import Datamap, String, Int2
    >>> g = Datamap( 'mymap',String('foo', 6),Int2('bar') )
    >>> g.buffer=Abuf(8)

    >>> g.bar=255
    >>> g.foo='abcdef'

    >>> print( g.foo)         # attribute access
    abcdef

    >>> dump(g.buffer)      # contents of buffer
    Buffer
     0000 61626364 6566FF00                   abcdef..         /ÂÄÀÁÃ..
    <BLANKLINE>
    <BLANKLINE>

    >>> print( '%(foo)s and %(bar)d' % g)        # dictionary access
    abcdef and 255

    The following keywords are supported:

    - **buffer**  sets the buffer on which the datamap is mapped
    - **offset**  defines the offset in the buffer where the datamap starts
    - **encoding** sets the encoding to convert to/from Unicode (default 'Latin1')
    - **ebcdic**  if True: Alpha strings are in EBCDIC (encoding will be set to 'cp037'
      if not encoding is not specified)

    - **byteOrder** define byte order for whole datamap (NETWORKBO or NATIVEBO)
    - **occurs**    multiple occurrence of datamap, e.g. PE group
      is a fixed number or an occurrence function, for example

          occurs=lambda:m1.occ - is a reference the occurrence count

    - **dmlen**
    - **varies**   indicates variable field positions and lengths
    - **supermap** enclosing datamap which provides defaults for buffer, offset etc.

    """

    def __init__(self, dmname, *fieldlist, **kw):

        self.__dict__['espace']    = None       # encoded space character in buffer (depends on encoding)
        self.__dict__['buffer']    = None
        self.__dict__['byteOrder'] = None
        self.__dict__['ebcdic']    = 0
        self.__dict__['encoding']  = ''         # encoding to convert to/from unicode
        self.__dict__['dmlen']     = 0
        self.__dict__['dmname']    = dmname
        self.__dict__['initix']    = -1         # last field intitialized (index in keylist)
        self.__dict__['initdmlen']  = 0
        self.__dict__['occurs']    = 0
        self.__dict__['offset']    = 0
        self.__dict__['varies']    = 0
        self.__dict__['supermap']  = None

        for k,v in kw.items():
            if k in ('byteOrder','buffer','ebcdic','encoding',
                     'occurs','offset','supermap','varies'):
                self.__dict__[k] = v
            elif k == 'dmlen':
                self.__dict__['dmlen'] = v
                self.__dict__['initdmlen'] = v
            elif k == 'byteorder':
                self.__dict__['byteOrder'] = v
            else:
                raise DatamapError('Undefined keyword %s'%k, self)

        enc = self.__dict__['encoding']
        ebc = self.__dict__['ebcdic']

        if not enc:   # no encoding set
            if self.__dict__['ebcdic']:
                enc = 'cp037'               # standard US EBCDIC
            else:
                enc = 'latin_1'             # standard ISO-8859-1
            self.__dict__['encoding'] = enc
        else:
            if not ebc and enc in ('cp037',):  # asc2ebc and ebc2asc with std cp037/Latin1
                self.__dict__['ebcdic'] = 1

        self.__dict__['espace'] = ' '.encode(enc)    # py2/3

        newdic = {}
        fieldpos = 0
        keylist = []
        self.__dict__['keydict']=newdic

        keysize=0       # max. size of field name
        capsize = 0     # caption size

        for v in fieldlist:
            # key - field name, fty - field type, odict - field options
            key, fty, size, odict = v

            assert key,'field must have a name in field definition %s' % v
            assert not key in newdic, 'field name %r already defined in datamap' % (key,)

            fieldopt=0
            fdict={}                            # field options

            if isinstance(odict, dict):
                fdict = odict.copy()            # shallow copy

                # evaluate special keywords and delete from fdict
                if 'repos' in fdict:
                    ipos = fdict['repos']
                    assert ipos, 'Datamap Field definition: repos must not be zero'

                    if self.__dict__['dmlen'] < fieldpos:     # update dmlen with last max. position used
                        self.__dict__['dmlen'] = fieldpos     # total size of all fields
                        self.__dict__['initdmlen'] = fieldpos # total size of all fields
                    fieldpos+=ipos
                    # del fdict['repos']  # need repos for prepare when updating positions
                if 'pos' in fdict:
                    if self.__dict__['dmlen'] < fieldpos:     # update dmlen with last max. position used
                        self.__dict__['dmlen'] = fieldpos     # total size of all fields
                        self.__dict__['initdmlen'] = fieldpos # total size of all fields
                    fieldpos=fdict['pos']
                    del fdict['pos']
                if 'opt' in fdict:
                    fieldopt|=fdict['opt']
                    del fdict['opt']
                if 'dt' in fdict:
                    dtv = fdict['dt']
                    if dtv in ('DATETIME','TIMESTAMP','DATE','TIME',
                               'NATDATE','NATTIME','UNIXTIME','XTIMESTAMP'):
                        fieldopt|=T_DT          # convert to/from datetime() object

            caption = fdict.get('caption','')   # display title with dprint()
            capsize = max(capsize,len(caption)) # size of biggest caption

            # Use display column size if set otherwise the bigger of field size or field name
            # This is relevant for colum-wise print in lprint()

            if 'colsize' not in fdict:
                sz = size
                if fty == T_BYTE or fieldopt & T_HEX:
                    sz*=2
                elif fieldopt & T_STCK:
                    sz = max(sz, 19)
                elif fty in (T_UINT1,):
                    sz=3
                elif fty in (T_INT1,):
                    sz=4
                elif fty in (T_UINT2,):
                    sz=5
                elif fty in (T_INT2,):
                    sz=6
                elif fty in (T_INT4, T_UINT4, T_UINT8, T_INT8):
                    sz=10
                elif fty == T_PACK:
                    sz = size * 2 - 1
                elif fieldopt & T_DT:
                    sz = 19           # datetime() str() 9999-12-31 23:59:59
                    # sz = 26         # with microsecond

                fdict['colsize'] = max(sz,len(key))

            if callable(size):
                fdict['initsize'] = size
                size=0  #  current size == 0
            else:
                if fty == T_UTF16:
                    size*=2                   # each unicode char is 2 bytes
                fdict['initsize'] = size

            if not fieldopt&T_INOUT:
                fieldopt|=T_INOUT             # if neither IN/OUT set default to INOUT

            newdic[key] = [fty, fieldpos, size, fieldopt, fdict]

            keylist.append(key)

            occurs = fdict.get('occurs',0)

            if occurs:
                fds = fdict.get('submap', None)   # sub datamap i.e. Periodic
                fdict['submap'] = Multiple(self, key, occurs, submap=fds)

                if fds:
                    fds.supermap=self
                    fieldpos += size          # Periodic: size is already dmlen*occurs or 0 if variable
                    if fds.varies:
                        self.varies=1
                elif not callable(occurs):
                    fieldpos += size * occurs # Multiple field
                else:  #
                    self.varies=1
            else:
                fieldpos+=size

            if keysize < len(key): # width of attribute name for printing
                keysize=len(key)

            if size == 0:
                self.__dict__['varies']=1 # mark datamap varies in size

        if self.__dict__['dmlen'] < fieldpos:
            self.__dict__['dmlen'] = fieldpos     # total size of all fields
            self.__dict__['initdmlen'] = fieldpos # total size of all fields

        self.__dict__['keylist'] = keylist
        self.__dict__['keysize'] = keysize  # max size of attribute name
        self.__dict__['capsize'] = capsize  # max size of caption

        # print( self.__dict__['keydict'])

    def getsize(self):
        """:returns: size of datamap"""
        return self.__dict__['dmlen']

    def prepare(self):
        """ Prepare datamap for field access.

        This function must be called if datamap contains
        variable fields or variable number of occurences.

        It sets the exact field position [1] and size [2] in the field
        definition list so that field access can use it.

        For variable length fields position/size excludes the length part
        initsize - stores the initial size (=0 for variable fields).
        """
        if debug:
            global INDENT
            print( INDENT, '%s.prepare() with dmlen=%d varies=%d buffer=%r offset=%d' % (
                           self.dmname, self.dmlen, self.varies, self.buffer, self.offset))
            INDENT+=4*' '

        if not self.varies:     # nothing to do if no variable components
            return

        fieldpos = 0
        start = fieldpos + self.offset

        keylist = self.__dict__['keylist']

        for i, k in enumerate(keylist):
            fdef = self.__dict__['keydict'][k]

            ftype,pos,sz,opt,fdic = fdef

            fieldpos += fdic.get('repos',0)

            if fieldpos != pos:     # update current field position
                if debug: print( 'updating %s.%s pos from %d to %d' % (self.dmname, k, pos, fieldpos))

                fdef[1] = fieldpos

            size = fdic.get('initsize')   # could be number or function
            mu = fdic.get('submap',None)

            if mu is not None:   # Multiple field or PE group
                                 # Note: Multiple has length function!
                if debug: print( INDENT, 'prepare:', self.dmname, k, fdef)
                if ftype == T_DMAP:
                    sm = mu.submap
                    if debug: print( INDENT, 'prepare: if submap %s varies=%d, dmlen=%d: call prepare()' %(
                                        sm.dmname,sm.varies,sm.dmlen))

                    if not sm.varies:
                        size=sm.dmlen
                    else:
                        sm.prepare()
                        if debug: print( INDENT, 'prepare: after calling prepare for', sm.dmname, sm.dmlen, sm.varies)

                occfunc = mu.__dict__.get('occfunc',None)
                if occfunc:

                    occurs = occfunc()  # current number of occurrences
                    if debug: print( INDENT, 'prepare: mupex=%d' % abs(occurs))

                    if occurs < 0:      # occurrence counter before field, abs(occurs) is size of counter
                        assert -2 <= occurs,'Invalid MUPE size %d, only 1 or 2 defined' % (abs(occurs),)

                        fieldpos += occurs  # byte position before MU field or PE group
                        copt = T_MUPE|T_VAR1 if occurs == -1 else T_MUPE|T_VAR2

                        fieldpos,occurs = self.getpossiz(i, copt, fieldpos)  # i = field element in datamap

                    mu.occurs=occurs
                else:
                    occurs = mu.__dict__.get('occurs',0)    # fixed number

                if debug: print( INDENT, 'prepare: key=%s, fieldpos=%d, occurs=%d' % (
                                            k, fieldpos, mu.__dict__.get('occurs',0)))

                if opt & (T_VAR0 | T_VAR1 | T_VAR2 | T_VAR4): # this is a variable field
                    possiz = []
                    for ix in range(occurs):
                        fieldpos,size = self.getpossiz(i, opt, fieldpos) # i = field element index in datamap
                        possiz.append((fieldpos,size))

                    fdic['possiz'] = possiz
                else:
                    if debug: print( INDENT, 'prepare: key=%s, fieldpos=%d, size=%d, occurs=%d, totalsize=%d' % (
                                                 k, fieldpos, size, occurs, size*occurs))
                    fieldpos += size * occurs

            else: # single field
                if opt & (T_VAR0 | T_VAR1 | T_VAR2 | T_VAR4): # this is a variable field
                    fieldpos,size = self.getpossiz(i, opt, fieldpos) # i = field element index in datamap

                    if size != sz:
                        fdef[2] = size
                    if fieldpos != pos:     # update current field position to data portion
                        fdef[1] = fieldpos
                    if debug: print( k, fieldpos, size, pos, sz)
                fieldpos += size

        if fieldpos > self.dmlen:     # update current dmlen
            if debug: print( 'updating %s.dmlen from %d to %d' % (self.dmname, self.dmlen, fieldpos))
            self.dmlen = fieldpos

        if debug:
            INDENT = INDENT[:-4]


    def getpossiz(self, index, opt, fieldpos):
        """ Determine position and size in variable field or
            occ. count before MU/PE field ( opt & T_MUPE)

            called from prepare()
        """
        # debug = 1

        bo = self.__dict__['byteOrder']

        pm = self
        while pm:               # find outmost datamap for buffer and offsets
            ppm = pm.supermap
            if ppm is None:
                break
            pm = ppm

        if bo is None:
            bo = pm.__dict__['byteOrder'] or byteOrder

        start = fieldpos + pm.offset


        keylist = self.__dict__['keylist']
        k = keylist[index]
        fdef = self.__dict__['keydict'][k]
        ftype,pos,sz,opt,fdic = fdef

        if debug:
            global INDENT
            INDENT += 4*' '
            print( INDENT, '%s.getpossiz() for %s start %d = fieldpos %d + offset %d bo=%s in buffer %r' % (
                            self.dmname, k, start, fieldpos, self.offset, bo, self.buffer))

        if opt & T_VAR1:
            size, = struct.unpack(bo+T_UINT1, pm.buffer[start:start+1])
            if size > 0 and not opt & T_MUPE:
                size -= 1   # minus 1
            fieldpos += 1
        elif opt & T_VAR2:
            size, = struct.unpack(bo+T_UINT2, pm.buffer[start:start+2])
            if not opt & T_MUPE:
                if size <= 2:
                    size = 0
                else:
                    size -= 2
            fieldpos += 2
        elif opt & T_VAR4:
            size, = struct.unpack(bo+T_UINT4, self.buffer[start:start+4])
            if size <= 4:
                size = 0
            else:
                size -= 4
            fieldpos += 4
        elif opt & T_VAR0:

            fun = fdic.get('sizefunc', None)

            if isinstance(fun, (types.FunctionType,types.MethodType)):
                size = fun() # call interpretation
                if debug: print('fun(): %d' % size)
            elif isinstance(fun, types.IntType): # variable/const
                size = fun # get the value
                if debug: print('fun(): %d' % size)
            else:
                size = 0
        else:
            size=0
            if debug: print('non var? size=0')
            pass

        if debug:
            INDENT = INDENT[:-4]

        return fieldpos, size


    def rippledown(self, fun, parm):
        """ apply function to lower datamaps
            no data is returned
        """

        keylist = self.__dict__['keylist']

        for i, k in enumerate(keylist):
            fdef = self.__dict__['keydict'][k]

            ftype,pos,sz,opt,fdic = fdef

            mu = fdic.get('submap',None)
            if mu is not None:   # Multiple field or PE group
                                 # Note: Multiple has length function!
                # print( INDENT, 'rippledown:', self.dmname, k, fdef)
                if ftype == T_DMAP:
                    sm = mu.submap
                    # print( INDENT, 'rippledown(): %s calling %s' %(sm.dmname, fun))
                    smfun =  getattr(sm,fun)
                    smfun(parm)


    def setByteOrder(self, byteorder):
        if byteorder == NETWORKBO:
            bo = byteorder
        else:
            bo = NATIVEBO

        if self.__dict__['byteOrder'] != bo:
            self.__dict__['byteOrder'] = bo

            # print('calling rippledown in setByetOrder(%s, %r)' %(self.dmname,bo))
            self.rippledown('setByteOrder', bo) # set it in submaps

        # print( 'setByteOrder()' , self.byteOrder)

    def setEbcdic(self, yesno):
        """set String/Char data to EBDIC in datamap

        This method also overrides any encoding with 'cp037' for EBCDIC or
        'Latin_1' for not EBCDIC.

        :param yesno: 0 to switch to EBCDIC or 1 to switch to ASCII
        """
        ebc = self.__dict__['ebcdic']
        if ebc:
            if yesno:
                return  # already set to ebcdic
            else:
                # switch off ebcdic
                self.__dict__['encoding'] = 'latin_1'
                self.__dict__['ebcdic'] = 0
        else:
            if yesno:
                self.__dict__['encoding'] = 'cp037'
                self.__dict__['ebcdic'] = 1

        # print('calling rippledown in setEbcdic(%s, %r)' %(self.dmname,yesno))
        self.rippledown('setEbcdic', yesno)

    def setNativeByteOrder(self):
        self.__dict__['byteOrder']=NATIVEBO
        # print( 'setNativeByteOrder()' , self.byteOrder)

    def setNetworkByteOrder(self):
        self.__dict__['byteOrder']=NETWORKBO
        # print( 'setNetworkByteOrder()', self.byteOrder)

    def setfsize(self, key, newsize):
        """ set new fieldsize
            Note: offsets of the following fields are not adjusted!
        """
        ftype, start, size, inout, fdic  = self.keydict[key]
        size = newsize
        self.keydict[key] = (ftype, start, size, inout, fdic)

    def dprint(self, indent=0, proff=0, selectfields=(), skipnull=0, title='' ):
        """Print detail lines with all attributes

        :param proff:  1 = print offset when walking through buffers
        :parm selectfields: display only fields listed (optional)
        :parm skipnull: 1 = do not display empty fields
        :parm title: title to display else datamap name
        """

        indstr=' '*indent

        if title:
            name = title
        else:
            name = self.__dict__['dmname']

        #o replication buffer specifics: move to urb/reptor code:
        #o  override function dprint()
        """ change the following
        eye = self.buffer[self.offset:self.offset+4]
        global dataIsEbcdic
        if self.__dict__['ebcdic'] or dataIsEbcdic:
          eye = str2asc(eye)
        """
        if proff:
            offstr = " at offset X'%04X'" %  self.offset
        else:
            offstr = ''
        print( "%s%s%s" %  (indstr, name, offstr))

        ks = self.capsize or self.keysize
        # use keysize if capsize==0 i.e. no caption was defined

        for k in self.__dict__['keylist']:
            (t,x,y,opt,fdic) = self.__dict__['keydict'][k]
            if opt & T_NONE:    # do not display filler fields
                continue
            if selectfields and k not in selectfields:
                continue
            dstr=''

            ostr = self.__getattr__(k) # data value or Multiple()

            if isinstance(ostr, Multiple):  # this can be MU field or a PE group
                if t == T_DMAP:             # PE Group
                    print()  # separating empty line
                    ostr.submap.lprint(header=1, indent=indent+4)
                    for i in ostr: # iterate on PE occurrences returns PE group datamap instance i
                        i.lprint(indent=indent+4,proff=1)
                    print()  # separating empty line
                    continue                # finished with this element

                else: #  iterate the MU field
                    mustrings = []
                    for oi in range(ostr.occurs):
                        mustrings.append('%r' % ostr[oi])
                    print( '[%s]' % (', '.join(mustrings),) ) # print MU values
                    continue

            if skipnull:
                if not ostr:
                    continue
                elif isinstance(ostr, str) and ostr == len(ostr)*'\x00':
                    continue
                elif PY3 and isinstance(ostr, bytes) and ostr == len(ostr)*b'\x00':
                    continue
                #else:
                #    print( 'skip?:', ostr, type(ostr))

            fun = fdic.get('ppfunc', None)

            if isinstance(fun, types.FunctionType):
                dstr = fun(ostr) # call interpretation
            elif isinstance(fun, types.MethodType): # method
                dstr = fun(ostr) # call interpretation ???no self

            kk = fdic.get('caption', k) # use caption as title or key

            if t in (T_STRING, T_BYTE, T_CHAR, T_UTF8, T_UTF16):
                if t == T_BYTE:
                    ostr = "X'%s'" % rawhex(ostr)
                    if len(ostr) == 0:
                        ostr='00'*y
                    print( '%s%-*s = %s %s' % (indstr, ks, kk, ostr, dstr))
                else:
                    if len(ostr) == 0:
                        ostr=' '*y
                    else:
                        # ostr=repr(ostr)[1:-1]  # omit double quotes
                        pass
                    print( '%s%-*s = %r %s' % (indstr, ks, kk, ostr, dstr))  # remove single quotes from repr()
                    # print( "%s%-*s = '%s' %s" % (indstr, ks, kk, ostr, dstr))
            else:
                if opt&T_STCK:
                    if t==T_UINT4:
                        ostr = sstck(ostr,gmt=opt&T_GMT) # local time if T_GMT not set
                    else: # should be T_UINT8
                        ostr = sstckd(ostr,gmt=opt&T_GMT) # local time if T_GMT not set
                if opt&T_HEX:
                    ostr = "X'%0*X'" % (2*y,ostr)
                if dstr:                                                  # result of function call
                    print( '%s%-*s = %s' % (indstr, ks, kk, dstr))
                else:                                                     # not string/byte/function
                    print( '%s%-*s = %s' % (indstr, ks, kk, ostr))
        print()

    def items(self, selectfields=()):
        """Return list of name value pairs on the fields in datamap

           Restriction: no composite fields

           :todo: check if byte arrays/fields can be used when handling bytes

        >>> from adapya.base.datamap import Datamap, String, Int2
        >>> g = Datamap( 'mymap',String('foo', 6),Int2('bar') )
        >>> from adapya.base.defs import Abuf
        >>> g.buffer=Abuf(8)
        >>> g.bar=255
        >>> g.foo='abcdef'
        >>> g.items()
        [('foo', 'abcdef'), ('bar', 255)]

        """

        myitems=[]

        for k in self.__dict__['keylist']:
            (t,x,y,opt,fdic) = self.__dict__['keydict'][k]
            if opt & T_NONE:    # do not display filler fields
                continue
            if selectfields and k not in selectfields:
                continue

            ostr = self.__getattr__(k)

            if isinstance(ostr, Multiple):  # this can be MU field or a PE group
                continue

            fun = fdic.get('ppfunc', None)

            if fun:
                if isinstance(fun, types.FunctionType):
                    ostr = fun(ostr) # call interpretation
                elif isinstance(fun, types.MethodType): # method
                    ostr = fun(ostr) # call interpretation ???no self
            elif t == T_BYTE:
                # ostr = '%s' % hexlify(ostr).upper()
                #if len(ostr) == 0:
                #    ostr='00'*y
                ostr = bytes(ostr)
            elif opt&T_STCK:
                if t==T_UINT4:
                    ostr = stck.sstck(ostr,gmt=opt&T_GMT) # local time if T_GMT not set
                    cs = max(cs,19)         # adapt column size if blank
                elif t==T_UINT8: # should be T_UINT8
                    ostr = stck.sstckd(ostr,gmt=opt&T_GMT) # local time if T_GMT not set
                    cs = max(cs,cs if 'colsize' in fdic else 30) # adapt column size if blank
            elif opt&T_HEX and t not in (T_STRING, T_CHAR, T_UTF8, T_UTF16):
                ostr = "%0*X" % (2*y,ostr)

            myitems.append( (k,ostr) )
        return myitems



    def lprint(self, header=0, indent=0, proff=0, selectfields=(), col1=''):
        """
        Print line with all attributes in one line with

        :param header: 1: print only header
        :param indent: Columns to indent (default = 0)
        :param proff:  1: print offset when walking through buffers
        :param selectfields: display only fields listed (optional)
        :param col1: prefix text as first column (use to add index numbers to line)
            Header and detail line should pass same string length

        """

        indstr=' '*indent

        name = self.__dict__['dmname']
        if header:
            if proff:
                offstr = " at offset X'%04X'" %  self.offset
            else:
                offstr = ''
            print( "%s%s%s" %  (indstr, name, offstr))

            # print('header indstr = %r col1 = %r' % (indstr,col1))
            print(indstr+col1,end='')

            # column size determined by max. caption and field length
            for k in self.__dict__['keylist']:
                (t,x,y,opt,fdic) = self.__dict__['keydict'][k]
                if opt & T_NONE:    # do not display filler fields
                    continue
                if selectfields and k not in selectfields:
                    continue

                kk = fdic.get('caption', k) # use field caption or key

                if 'colsize' in fdic:
                    cs=fdic['colsize']
                elif opt & T_STCK:
                    if t==T_UINT4:
                        stcksz = 19
                    else:
                        stcksz = 30
                    cs=max(fdic.get('colsize', len(kk)), stcksz)
                else:
                    cs=len(kk)

                if t  in (T_STRING, T_UTF8, T_UTF16):   # strings left aligned
                    print( '%-*s' % (cs, kk), end=' ')
                else:                                   # numeric values right aligned
                    print( '%*s' % (cs, kk), end=' ')

            print()
            return  # --- end of header print ---

        print( indstr+col1, end='')

        # print line with all fields
        for k in self.__dict__['keylist']:
            (t,x,y,opt,fdic) = self.__dict__['keydict'][k]
            #if k == 'cmdt':
            #    print( 'k =',k, t, x, y, opt, fdic, self.__getattr__(k))

            if opt & T_NONE:    # do not display filler fields
                continue
            if selectfields and k not in selectfields:
                continue

            ostr = self.__getattr__(k)

            if isinstance(ostr, Multiple):  # this can be MU field or a PE group
                if t == T_DMAP:             # PE Group
                    ostr.supermap.lprint(header=1, indent=indent+4)
                    for i in ostr:
                        i.lprint(indent=indent+4)
                    continue                # finished with this element

                else:   # iterate the MU field
                    mustrings = []
                    for os in ostr:
                        mustrings.append('%r' % os)
                    print( ', '.join(mustrings))
                    #o integrate code below to each value
                    #o continue

            kk=fdic.get('caption',k)        # use column header if defined
            cs=fdic.get('colsize', len(kk)) # column size
            fun = fdic.get('ppfunc', None)

            if fun:
                if isinstance(fun, types.FunctionType):
                    ostr = fun(ostr) # call interpretation
                elif isinstance(fun, types.MethodType): # method
                    ostr = fun(ostr) # call interpretation ???no self
                cs=max(cs,len(ostr))
            elif t == T_BYTE:
                ostr = '%s' % hexlify(ostr).upper()
                if len(ostr) == 0:
                    ostr='00'*y
            elif opt&T_STCK:
                if t==T_UINT4:
                    ostr = sstck(ostr,gmt=opt&T_GMT) # local time if T_GMT not set
                    cs = max(cs,19)         # adapt column size if blank
                elif t==T_UINT8: # should be T_UINT8
                    ostr = sstckd(ostr,gmt=opt&T_GMT) # local time if T_GMT not set
                    cs = max(cs,cs if 'colsize' in fdic else 30) # adapt column size if blank
            elif opt&T_HEX and t not in (T_STRING, T_CHAR, T_UTF8, T_UTF16):
                ostr = "%0*X" % (2*y,ostr)

            if t in LEFT_ALIGNED:
                print( '%-*s' % (cs, ostr), end=' ')
            else:
                print( '%*s' % (cs, ostr), end=' ')      # left align
        print()


    def __getattr__(self,key):
        # function will only be called if normal instance attribute lookup fails
        # e.g. self.buffer would not come here because it is initalized (to None) in
        # self.__dict__

        if not isinstance(self, Datamap):
            print('Expected Datamap instance is of %r' % type(self))
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__, key))
        if 0:
            print( INDENT, '%s.%s.__getattr__()\n\t%r' % (self.dmname,key,self.keydict))

        if key in self.keydict:
            ftype, start, size, inout, fdic = self.keydict[key]
            if 0:
                print( INDENT, '%s.%s.__getattr__()\n\t%r' % (self.dmname,key,self.keydict))
            if 'submap' in fdic:
                return fdic['submap']     # return Multiple/Datamap object
            else:
                return dunpack(self, key)
        else:
            if 0 and key in ('buffer', 'offset') and self.supermap:
                # locate buffer and offset in outmost datamap that encloses datamap self
                pmfirst = pm = self.supermap
                while pm :
                    pm, pmfirst = pm.supermap, pm
                return dunpack(pmfirst, key)

            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__, key))


    def __getitem__(self,key):
        "Dictionary type of usage: b['str']"
        return self.__getattr__(key)

    def __setitem__(self,key,data):
        "Dictionary type of usage: b['str']='abcde'"
        return self.__setattr__(key,data)

    def __setattr__(self,key,data):
        global dataIsEbcdic

        if key in self.keydict:
            ftype, start, size, inout, fdic  = self.keydict[key]

            if not (inout & T_IN):
                raise DatamapError("Field %s must not be modified" % key, self)

            if 'submap' in fdic:
                # Only come here if d.mufield = (val1,val2)
                # d.mufield[1] = value is resolved as
                #    d.__getitem__() returning submap object (e.g. Multiple) followed by
                #    submap.__setitem__()
                occurs = fdic.get('occurs',0)

                if callable(occurs):
                    occurs=occurs()
                # elif isinstance(occurs, (list,tuple)): # todo
                #   get and set occ functions given: set occurrences function
                #   to update occurrence count or Format with index range

                if occurs > 0 and isinstance(data, (list,tuple)) and len(data) <= occurs:
                    for i, val in enumerate(data):
                        dpack(self, key, val, indx=i)
                else:
                    if isinstance(data, (list,tuple)):
                        raise DatamapError('Assignment to submap/multiple %s only for tuples/list with size %d < max occurrence %d' % (
                            key,len(data),occurs), self)
                    else:
                        raise DatamapError('Assignment to submap/multiple %s only for tuples/list, given %r' % (
                            key,data), self)
            else:
                dpack(self, key, data)

        else:
            if key in self.__dict__:  # key must be defined at class init
                self.__dict__[key]=data
            else:
                raise DatamapError('Attribute %s not defined in Datamap'%key, self)

    def genfb(self):
        """ Generate Format buffer from datamap with fields defining Adabas
        field name with options fn

        datamap instance must have field name *fn* added to the options
        dict of each field

        :returns: string with format buffer contents

        Note: currently limited to normal fields - no PE/MU support

        >>> from adapya.base.datamap import Datamap,Int2,String
        >>> g = Datamap('mymap',String('foo',6,fn='AA'),Int2('bar',fn='AB',occurs=3))
        >>> g.genfb()
        'AA,6,A,AB,2,F.'
        """
        import os
        if PY3:
            from _io import StringIO
        else:
            from cStringIO import StringIO
        fbuf = StringIO()

        for k in self.__dict__['keylist']:
            (ftype, start, size, inout, fdic) = self.__dict__['keydict'][k]
            if fbuf.tell() > 0:
                fbuf.write(',') # separate from previous field
            if 'fn' in fdic:
                fn = fdic['fn']
                occ = fdic.get('occurs',0) # (fixed) occurrences or zero
                if occ > 1:
                    occ = '1-%d' % occ
                else:
                    occ=''
                ffrm = DM2ADAF.get(ftype,'')
                if ffrm:
                    fbuf.write('%s%s,%d,%s' % (fn,occ,size,ffrm) )
                else:
                    fbuf.write('%s,%d' % (fn,size) )
            else:
                fbuf.write('%dX' % size ) # field name not found: leave empty

        fbuf.write('.') # close format buffer field list
        fbs=fbuf.getvalue()
        return fbs # return prepared format buffer string

    def getfndef(self,name):
        """Get Adabas field definition from datamap

        :returns: tuple Adabas (field name, length, format)
               or None if name does not exist or field name not found

        >>> g = Datamap( 'mymap',String('foo',6,fn='AA'),Int2('bar',fn='AB') )
        >>> g.getfndef('foo')
        ('AA', 6, 'A')
        """
        fdef = self.__dict__['keydict'].get(name,None)
        if fdef:
            (ftype, start, size, inout, fdic) = fdef
            if 'fn' in fdic:
                fn = fdic['fn']
                ffrm = DM2ADAF.get(ftype,'')
                return (fn, size, ffrm)
        return None

    def reset(self):
        """
        Reset attributes/key values of a datamap to default values
        if buffer variable is set::

            >> adac.cb.reset()
        """
        if self.buffer: # can only reset values if buffer is underlying
            for key in self.keylist:    # go from left to right
                ftype, start, size, inout, fdic  = self.keydict[key]

                if not (inout & T_IN):
                    continue    # do not reset input only fields

                if ftype == T_STRING:
                    value = ''
                elif ftype in (T_UTF16, T_UTF8):
                    value = u''
                elif ftype == T_BYTE:
                        value = b''
                elif ftype == T_CHAR: # one character
                        value = ' '
                else:   # numeric type
                    if inout & T_DT:
                        value = None
                    else:
                        value = 0

                if 'submap' in fdic:
                    # Only come here if d.mufield = (val1,val2)
                    # d.mufield[1] = value is resolved as
                    #    d.__getitem__() returning submap object (e.g. Multiple) followed by
                    #    submap.__setitem__()
                    occurs = fdic.get('occurs',0)

                    if callable(occurs):
                        occurs=occurs()
                    # elif isinstance(occurs, (list,tuple)): # todo
                    #   get and set occ functions given: set occurrences function
                    #   to update occurrence count or Format with index range

                    if occurs > 0:
                        for i in range(occurs):
                            dpack(self, key, value, indx=i)
                else:
                    dpack(self, key, value)



    def update(self, *kviter, **kw):
        """
        Update or set the attributes/keys of a datamap to the values
        in the list given as list or iterable of (key, value) pairs
        or as list of keyword=value itmes

        :param kviter: list or iterable of 'key',value pairs
        :param kw:     list of key=value

        Example::

            >> empl.update(name='Bell',first_name='John')
        """
        for k,v in kviter:
            self.__setattr__(k,v)
        for k,v in kw.items():
            self.__setattr__(k,v)

def fndef2datamap(name,fndef):
    """ Return a Fieldmap class from a fndef list
    :param fndef: list of fndef tuples
    :param name: class name to be returned
    """

    class Fieldmap(Datamap):
        def __init__(self,**kw):
            Datamap.__init__(self, name, *flist, **kw)
    Fieldmap.__name__ = name.capitalize()

    return Fieldmap

#
# define pack and unpack for numerical types
#

d = Datamap( 'formats',
        Unpacked( 'u', 29, pos=0),
        Packed(   'p', 15, pos=0),
        Bytes(    'b', 126, pos=0),
        Int1(     'f1', pos=0),
        Int2(     'f2', pos=0),
        Int4(     'f4', pos=0),
        Int8(     'f8', pos=0),
        Uint1(    'u1', pos=0),  # unsigned integer
        Uint2(    'u2', pos=0),
        Uint4(    'u4', pos=0),
        Uint8(    'u8', pos=0),
        )
d.buffer = Abuf(126)
d.setNativeByteOrder()

def fpack(value, format, length, byteorder=None, ebcdic=0):
    """ Pack number to byte string in one of the following
    number representations/formats supported by Adabas:

        Unpacked, Packed, Binary, Fixpoint, unsigned integer 'u'

    :param value:  number (int/long)
    :param format: 'U', 'P', 'B', 'F', 'u'
    :param length: allowed are for U:1-30, P:1-15, B:1-126, F:1,2,4,8
                   u:1,2,4,8

    :returns: string in PY2 and bytes in PY3

    Example::

        >>> from adapya.base.datamap import fpack
        >>> fpack(234,'P',2) == b'\x23\x4c'
        True

    """
    d.setEbcdic(ebcdic)
    if byteorder:
        d.setByteOrder(byteorder)
    else:
        d.setNativeByteOrder() # reset
    if format=='U':
        d.setfsize('u',length)   # set length for converting U with u mapped to buffer
        d.u=value
    elif format=='P':
        d.setfsize('p',length)
        d.p=value
    elif format=='B':
        d.setfsize('b',length)
        d.b=value
    elif format=='F':
        if length == 2:
            d.f2=value
        elif length == 4:
            d.f4=value
        else:   # length == 8
            d.f8=value
    elif format=='u':   # unsigned integer
        if length == 1:
            d.u1=value
        elif length == 2:
            d.u2=value
        elif length == 4:
            d.u4=value
        else:   # length == 8
            d.u8=value
    return d.buffer[:length]

def funpack(bstring, format, byteorder=None,ebcdic=0):
    """Unpacks number from byte string in one of the following
    number representations/formats supported by Adabas:

        Unpacked, Packed, Binary, Fixpoint

    :param value: Byte string
    :param format: 'U', 'P', 'B', and 'F' plus 'u' unsigned
    :param byteorder: NETWORKBO or NATIVEBO (defined in datamap)
    :returns: number (int/long) for 'U', 'P', 'F' and 'u'
            or byte string for 'B'

    Example::

        >>> from adapya.base.datamap import funpack
        >>> funpack(b'\x23\x4d','P')
        -234
    """
    d.setEbcdic(ebcdic)
    if byteorder:
        d.setByteOrder(byteorder)
    else:
        d.setNativeByteOrder() # reset
    length = len(bstring)
    d.buffer[0:length] = bstring
    if format=='U':
        d.setfsize('u',length)   # set length for converting U with u mapped to buffer
        return d.u
    elif format=='P':
        d.setfsize('p',length)
        return d.p
    elif format=='B':
        d.setfsize('b',length)
        return d.b
    elif format=='F':
        if length == 1:
            return d.f1
        elif length == 2:
            return d.f2
        elif length == 4:
            return d.f4
        else:   # length == 8
            return d.f8
    elif format=='u':
        if length == 1:
            return d.u1
        elif length == 2:
            return d.u2
        elif length == 4:
            return d.u4
        else:   # length == 8
            return d.u8

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
