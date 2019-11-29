#! /usr/bin/env python
# -*- coding: latin1 -*-
"""
defs - Basic definitions for adapya
===================================

The module defs.py in the adapya.base package defines basic functionality
for the adapya packages

- Abuf class (read/write buffer) provides byte buffers with read and write
  access funtions

- Logging

- dummymutex for synchronizing printing and logging


"""
from __future__ import print_function          # PY3

__version__ = '1.0.4'
if __version__ == '1.0.4':
    _svndate='$Date: 2019-11-21 15:21:10 +0100 (Thu, 21 Nov 2019) $'
    _svnrev='$Rev: 949 $'
    __version__ = 'Dev ' +  _svnrev.strip('$') + \
                  ' '.join(_svndate.strip('$').split()[0:3])

import ast, ctypes, logging, sys

if sys.hexversion < 0x03010100 and sys.platform == 'zos':
    # Get helpers for string conversion between Latin1 and EBCDIC (cp037)
    # for read() and write() with Abuf instances -
    # for Rocket Python port: source is in Latin1 and system runs EBCDIC.
    # No need for this in PY3 where strings are in unicode and
    # decode() / encode() will do the job.
    # todo: for other EBCDIC flavours these functions would need to be
    #       properly parameterized
    from .conv import str2ebc, ebc2str


class ProgrammingError(Exception): pass

class DummyContext(object):
    def __enter__(self):
        pass
    def __exit__(self,excty,excva,tt):
        pass

"""adapya.base.defs.dummymutex is a dummy lock for
printing and logging in the Adabas api modules
override with a real lock object e.g. passed
as pmutex parameter to the Adabas class

E. g. with multi-processing
    >>> pmutex = multiprocessing.Lock()
    >>> with pmutex:
    ...     print 'synchronized printing'

"""
dummymutex = DummyContext()

if sys.hexversion > 0x03010100:
    # Python 3
    def Abuf(init, encoding='utf-8', errors='strict'):
        ''' Create a read/write buffer similar to a bytearray.
        This factory function returns a Cbuf object.

            :param init: a buffer size > 0 or an initial nonempty
                string or unicode string which determines the size
                of the buffer.
            :param encoding: standard encoding encode string to binary
                string, default is 'utf-8'

        Some Abuf use examples (Python2):

        >>> a=Abuf(10)
        >>> a.write('abc')
        >>> a.write('DEFG')
        >>> a.value
        b'abcDEFG'
        >>> a.raw
        b'abcDEFG\\x00\\x00\\x00'
        >>> a.tell()
        7
        >>> a.seek(0)
        >>> a.read(3)
        b'abc'
        >>> a.read_text(4)
        'DEFG'
        >>> a[0]
        b'a'
        >>> a[0:3]
        b'abc'
        >>> a[3:]=b'1234567'
        >>> a.value
        b'abc1234567'


        Some examples (Python3):

        >>> e=Abuf(10,encoding='cp037')
        >>> e.write('ABC')
        >>> e.write(b'123')
        >>> e.value
        b'\\xc1\\xc2\\xc3123'
        >>> e.raw
        b'\\xc1\\xc2\\xc3123\\x00\\x00\\x00\\x00'
        >>> e.seek(0)
        >>> e.read_text(3)
        'ABC'
        >>> e.read(3)
        b'123'
        >>> e[0]
        b'\xc1'
        >>> e[0:3]
        b'\xc1\xc2\xc3'

        '''

        size = 0
        binit = b''
        if isinstance(init, str):
            binit = init.encode(encoding=encoding,errors=errors)
            size = len(binit)
        elif isinstance(init, (bytes,bytearray)):
            size = len(init)
        elif isinstance(init, int):
            size=init
        else:
            raise TypeError(init)

        Cchar = ctypes.c_char * size

        class Cbuf(Cchar):
            _type_   = ctypes.c_char
            _length_ = size

            def __init__(self,size,encoding=encoding,errors=errors):
                self.encoding = encoding
                self.pos = 0
                if size>0:
                    Cchar.__init__(self, b'\x00')
                else:
                    raise ProgrammingError('Cbuf: Unable to allocate zero size buffer')

            # add file methods to the object
            def write(self, wstr):
                p1  = self.pos

                if isinstance(wstr, str):
                    bstr = wstr.encode(encoding=encoding,errors=errors)
                else:
                    bstr = wstr

                length = len(bstr)
                if p1 + length > self._length_:
                    # c_char_Array size exceeded
                    length = self._length_ - p1
                p2 = p1 + length
                self[p1:p2] = bstr[0:length]
                self.pos = p2

            write_text = write  # write_text same method as write PY3

            def read(self, size):
                " return bytes string from buffer from current position "
                if size < 1:
                    return ''
                p1 = self.pos
                p2 = p1 + size
                if p2 <= len(self):
                    self.pos=p2
                    return self[p1:p2]
                else:
                    self.pos=len(self)
                    return self[p1:p2]

            def read_text(self, size, encoding=encoding, errors=errors):
                """ return string from buffer from current position """
                if size < 1:
                    return ''
                # determine size of one blank
                ss = len(' '.encode(encoding=encoding,errors=errors))
                p1 = self.pos
                p2 = p1 + size*ss
                if p2 <= len(self):
                    self.pos=p2
                else:
                    self.pos=len(self)
                return self[p1:p2].decode(encoding=encoding,errors=errors)

            def seek(self, offset, where=0):
                if where < 1: # from buffer start
                    np=offset
                elif where == 1: # from current pos
                    np=self.pos+offset
                else:   # where=2 from the end
                    np=len(size)+offset
                if np < 0:
                    self.pos=0
                elif np < len(self):
                    self.pos=np
                else:
                    self.pos=len(self)

            def tell(self):
                return self.pos

            def buf2str(self):
                "convert byte string in buffer to string and strip blanks and nul"
                s = self[:].decode(encoding=encoding,errors=errors)
                return s.strip(' \x00')

        cc = Cbuf(size)
        if isinstance(init, str):
            cc.value=binit
        if isinstance(init, (bytes,bytearray)):
            cc.value=init
        return cc
else:
    # Python 2
    def Abuf(init, encoding='utf-8', errors='strict'):
        ''' Create a read/write buffer similar to a bytearray.
        This factory function returns a Cbuf object.

            :param init: a buffer size > 0 or an initial nonempty
                string or unicode string which determines the size
                of the buffer.

        Some Abuf use examples:

        >>> a=Abuf(10)
        >>> a.write('abc')
        >>> a.write('DEFG')
        >>> a.value
        'abcDEFG'
        >>> a.raw
        'abcDEFG\\x00\\x00\\x00'
        >>> a.tell()
        7
        >>> a.seek(0)
        >>> a.read(3)
        'abc'
        >>> a.read_text(4)
        u'DEFG'
        >>> a[0]
        'a'
        >>> a[0:3]
        'abc'
        >>> a[3:]='1234567'
        >>> a.value
        'abc1234567'
        '''

        size = 0
        istr=''
        if isinstance(init, str):
            istr=init
            size = len(init)
        elif isinstance(init, unicode):
            istr=init.encode(encoding,errors)
            size = len(init)
        elif isinstance(init, (int, long)):
            size=init
        else:
            raise TypeError(init)

        Cchar = ctypes.c_char * size

        class Cbuf(Cchar):
            _type_   = ctypes.c_char
            _length_ = size

            def __init__(self,size):
                self.encoding = encoding

                self.pos = 0
                if size > 0:
                    Cchar.__init__(self, '\x00')
                else:
                    raise ProgrammingError('Cbuf: Unable to allocate zero size buffer')

                if u' '.encode(encoding) == '\x40': # and sys.platform=='zos':
                    self.ebcdic = 1     # target is ebcdic encoding
                else:
                    self.ebcdic = 0

            # add file methods to the object
            def write(self, wstr):
                p1  = self.pos
                if isinstance(wstr, unicode):
                    bstr = wstr.encode(encoding,errors)
                    # elif isinstance(wstr, str) and self.ebcdic:
                    # bstr = unicode(wstr).encode(encoding,errors)
                    ##    bstr = str2ebc(wstr)
                else:
                    bstr = wstr
                length = len(bstr)
                if p1 + length > self._length_:
                    # c_char_Array size exceeded
                    length = self._length_ - p1
                p2 = p1 + length
                self[p1:p2] = bstr[0:length]
                self.pos = p2

            def write_text(self, wstr):
                p1  = self.pos
                if isinstance(wstr, unicode):
                    bstr = wstr.encode(encoding,errors)
                elif isinstance(wstr, str) and self.ebcdic:
                    bstr = unicode(wstr).encode(encoding,errors)
                    ##    bstr = str2ebc(wstr)
                else:
                    bstr = wstr
                length = len(bstr)
                if p1 + length > self._length_:
                    # c_char_Array size exceeded
                    length = self._length_ - p1
                p2 = p1 + length
                self[p1:p2] = bstr[0:length]
                self.pos = p2

            def read(self, size):
                if size < 1:
                    return ''
                p1 = self.pos
                p2 = p1 + size
                if p2 <= len(self):
                    self.pos=p2
                else:
                    self.pos=len(self)
                rs = self[p1:p2]
                if self.ebcdic:
                    return ebc2str(rs)
                else:
                    return rs

            def read_text(self, size, encoding=encoding, errors=errors):
                """ return unicode string from buffer from current position """
                if size < 1:
                    return u''
                # determine size of one blank
                ss = len(u' '.encode(encoding,errors))
                p1 = self.pos
                p2 = p1 + size*ss
                if p2 <= len(self):
                    self.pos=p2
                else:
                    self.pos=len(self)
                return self[p1:p2].decode(encoding,errors)

            def seek(self, offset, where=0):
                if where < 1: # from buffer start
                    np=offset
                elif where == 1: # from current pos
                    np=self.pos+offset
                else:   # where=2 from the end
                    np=len(size)+offset
                if np < 0:
                    self.pos=0
                elif np < len(self):
                    self.pos=np
                else:
                    self.pos=len(self)

            def tell(self):
                return self.pos

            def buf2str(self):
                "Convert byte string in buffer to string and strip blanks and nul"
                if self.ebcdic:
                    s = ebc2str(self[:])
                else:
                    s = self[:]
                return s.strip(' \x00') # remove blanks NUL at end

        cc = Cbuf(size)
        if isinstance(init, (str, unicode)):
            cc.value=istr

        return cc

def evalb(s):
    """ Evaluates string for single byte escape sequences

    :returns: byte string

    >>> evalb('ABC\xe4\xff')
    b'ABCäÿ'

    .. note:: In PY3 no unicode escapes can be used,
        use evals() for that purpose.

    """
    b2="b'%s'" % s
    return ast.literal_eval(b2)


def evals(s):
    """ Evaluates string for unicode escape sequences

    :returns: string

    >>> evals('ABC\u00e4\u00ff')
    'ABCäÿ'

    .. note::

        In PY3 no escaped single bytes can be defined,
        use evalb() for that purpose.

    """
    s2="'%s'" % s
    return ast.literal_eval(s2)


LOGCMD=1        #0x01
LOGBEFORE=1<<1  #0x02
LOGCB=1<<2      #0x04
LOGFB=1<<3      #0x08
LOGRB=1<<4      #0x10
LOGSB=1<<5      #0x20
LOGVB=1<<6      #0x40
LOGIB=1<<7      #0x80
LOGMB=1<<8      #0x0100
LOGPB=1<<9      #0x0200
LOGUB=1<<10     #0x0400
LOGAOS=1<<16    #0x10000
LOGRSP=1<<17    #0x20000
LOGBUF=1<<18    #0x40000 LOG all buffers
LOGSP=1<<19     #0x80000 LOG depending on command option (command table option)

logopt = LOGRSP|LOGCB  # global log parameter for current log setting
logstr = ''            # log options printable last set

# define a Handler which writes DEBUG messages or higher to the sys.stderr

# changed to stdout so that nosetests can capture the logged data
#  and output it only on error (2011_1102)
#  leaving it on sys.stderr would write the full log even for successful tests
console = logging.StreamHandler(sys.stdout)   #default is sys.stderr
#console.setLevel(logging.DEBUG)

# format for simple console use
#formatter = logging.Formatter('adalog: %(message)s')
## tell the handler to use this format
#console.setFormatter(formatter)

# add the handler to the root logger
logging.getLogger('').addHandler(console)
adalog = logging.getLogger('adalog')
adalog.setLevel(logging.DEBUG)


def log(logparm=None):
    """ set adapya.base interface log options
    """
    global logopt,adalog,logstr
    from .datamap import flag_str

    if logparm == None:
        pass
    elif logparm != logopt:
        logopt=logparm

    if logopt == 0:
        logstr='off'
    else:
        logstr = flag_str(logopt, ((LOGCMD,'LOGCMD'),
            (LOGBEFORE,'LOGBEFORE'),(LOGCB,'LOGCB'),(LOGFB,'LOGFB'),
            (LOGRB,'LOGRB'),(LOGSB,'LOGSB'),(LOGVB,'LOGVB'),
            (LOGIB,'LOGIB'),(LOGAOS,'LOGAOS'),(LOGRSP,'LOGRSP'),
            (LOGMB,'LOGMB'),(LOGPB,'LOGPB'),(LOGBUF,'LOGBUF'),
            ))
    # adalog.info('Adabas call logging: %s\n' % logstr)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

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
