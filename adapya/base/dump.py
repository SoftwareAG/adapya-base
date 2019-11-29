"""
dump - Buffer hex display functions
===================================

This module contains buffer storage display functions

- most notably dump() used for logging buffers
- classes/methods for reversing readable SYSUDUMP data
  into virtual storage
- diffdump for printing differences in buffers using difflib

"""
from __future__ import print_function          # PY3

import binascii
from binascii import unhexlify
import struct
import string
import sys


benco = sys.getdefaultencoding()
if benco not in ('ascii', 'cp1252', 'latin_1'):
    benco = 'latin_1'

#
# set up printable ASCII table for translate()
#

# ASCII printables
ascpribles=\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b' ' b'!' b'"' b'#' b'$' b'%' b'&' b"'" b'(' b')' b'*' b'+' b','  b'-' b'.' b'/'\
      b'0' b'1' b'2' b'3' b'4' b'5' b'6' b'7' b'8' b'9' b':' b';' b'<'  b'=' b'>' b'?'\
      b'@' b'A' b'B' b'C' b'D' b'E' b'F' b'G' b'H' b'I' b'J' b'K' b'L'  b'M' b'N' b'O'\
      b'P' b'Q' b'R' b'S' b'T' b'U' b'V' b'W' b'X' b'Y' b'Z' b'[' b'\\' b']' b'^' b'_'\
      b'.' b'a' b'b' b'c' b'd' b'e' b'f' b'g' b'h' b'i' b'j' b'k' b'l'  b'm' b'n' b'o'\
      b'p' b'q' b'r' b's' b't' b'u' b'v' b'w' b'x' b'y' b'z' b'{' b'|'  b'}' b'~' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'\
      b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'  b'.' b'.' b'.'


# EBCDIC printables
ebcpribles=\
    b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'\
    b' ' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'<' b'(' b'+' b'.'\
    b'&' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'!' b'$' b'*' b')' b';' b'.'\
    b'-' b'/' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b',' b'%' b'_' b'>' b'?'\
    b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b':' b'#' b'@' b"'" b'=' b'"'\
    b'.' b'a' b'b' b'c' b'd' b'e' b'f' b'g' b'h' b'i' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'j' b'k' b'l' b'm' b'n' b'o' b'p' b'q' b'r' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'.' b's' b't' b'u' b'v' b'w' b'x' b'y' b'z' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'A' b'B' b'C' b'D' b'E' b'F' b'G' b'H' b'I' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'J' b'K' b'L' b'M' b'N' b'O' b'P' b'Q' b'R' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'.' b'.' b'S' b'T' b'U' b'V' b'W' b'X' b'Y' b'Z' b'.' b'.' b'.' b'.' b'.' b'.'\
    b'0' b'1' b'2' b'3' b'4' b'5' b'6' b'7' b'8' b'9' b'.' b'.' b'.' b'.' b'.' b'.'

priblesdict={
    # print tables for other ebcdict codepages may be added dynamically
    }

# If the system supports a full single byte character set (rather than
# 'ascii') make a translate table that contains special characters too.
# This is usualy enabled in lib/site.py where the encoding is gotten
# from locale.getdefaultlocale()
# 'cp037' is used as the corresponding Latin1 EBCDIC code page

def getprible(codec):
    if codec in priblesdict:
        return priblesdict[codec]
    else:
        if sys.getdefaultencoding() in ('cp1252', 'latin_1'):
            tbuf=adapya.base.Abuf(256)
            tbuf[0:32]=32*'.'
            for i in range(32,127):
                tbuf[i]=chr(i)
            tbuf[127]='.'           # 'DEL'
            if sys.getdefaultencoding() == 'cp1252':
                for i in range(128,160):
                    tbuf[i]=chr(i)
                # windows has defined additional codepoints in the control
                # character range 0x80-0x9f except the following:
                tbuf[0x81]=tbuf[0x8d]=tbuf[0x8f]=tbuf[0x90]=tbuf[0x9d]='.'
            else:
                tbuf[128:160]=32*'.'

            for i in range(160,256):
                tbuf[i]=chr(i)
            for i in range(32,128):
                tbuf[i]=chr(i)
            ascpribles=tbuf[:]   # repackage as string for string.translate()

            for i in range(64,255):
                tbuf[i]=chr(i)
            t2=tbuf[:]
            ustr = t2.decode(codec)

            tbuf[0:256] = ustr.encode(sys.getdefaultencoding(),'replace')
            tbuf[0:64]=64*'.'
            tbuf[255] = '.'
            ep = tbuf[:]
            priblesdict[codec] = ep # add new table to dict
            return ep
        else:
            return ebcpribles



# Hexadecimal table
ishex=\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '0' '1' '2' '3' '4' '5' '6' '7' '8' '9' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00'\
      '\x00' 'A' 'B' 'C' 'D' 'E' 'F' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' 'a' 'b' 'c' 'd' 'e' 'f' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'\
      '\x00' '\x00' '\x00' '\x00' '\x00' '\x00' '\x00'

def diffdump(buf1, buf2, header1='Buffer 1', header2='Buffer 2',
        startaddr=None, fd=None):
    """Print the difference of 2 buffers"""
    from difflib import Differ
    from StringIO import StringIO

    f1=StringIO()
    f2=StringIO()

    dump(buf1, header=header1, startaddr=startaddr, fd=f1)
    dump(buf2, header=header2, startaddr=startaddr, fd=f2)

    f1.seek(0)  # reposition to file start
    f2.seek(0)

    d = Differ()
    result = list(d.compare(f1.readlines(), f2.readlines()))

    """
    print('results of dump()')
    print(f1.readlines())
    print(f2.readlines())
    print(result)
    """

    if fd==None:
        sys.stdout.writelines(result)
    else:
        fd.writelines(result)

def diffbin( a, b, header1='Buffer1', header2='Buffer2',
        startaddr=0, fd=None):
    """Binary difference printer for buffer objects a and b
    """
    from difflib import SequenceMatcher

    s=SequenceMatcher(None, a, b)

    print("\nComparing\n    A = %s\n    B = %s " % (header1, header2),
          file=fd)


    for tag, i1, i2, j1, j2 in s.get_opcodes():
        print( "\n%s A+%04X(%04X) vs. B+%04X(%04X)" % (
            tag[0:3].upper(), i1,i2-i1, j1, j2-j1), file=fd)
        if tag == 'delete':
            dump(a[i1:i2],prefix='A',header=None,startaddr=startaddr+i1,fd=fd)
        elif tag == 'equal':
            dump(a[i1:i2],prefix='A',header=None,startaddr=startaddr+i1,fd=fd)
        elif tag == 'replace':
            dump(a[i1:i2],prefix='A',header=None,startaddr=startaddr+i1,fd=fd)
            dump(b[j1:j2],prefix='B',header=None,startaddr=startaddr+j1,fd=fd)
        else: # tag == 'insert':
            dump(b[j1:j2],prefix='B',header=None,startaddr=startaddr+j1,fd=fd)

    print('\nSimliarity between objects is %3.1f%%\n' % (s.ratio()*100,),file=fd)


def dump(buf, header='Buffer', prefix='', startaddr=None, fd=None, log=None, ecodec='cp037'):
    """ print or log buffer

    :param buf: string, bytestring or bytearray
    :param ecodec: ebcdic codec name for ebcdic printable characters
    :param startaddr: dump lines will be prefixed with given start address plus offset
        as absolute address rather than relative offset from buffer start

    Example to write warning to logger adalog::

        dump(a,log=adalog.warning)

    """
    ep = getprible(ecodec) # get ebcdic printables table
    lines=[]
    if header:
        lines.append(header)

    if isinstance(buf, str) and sys.hexversion > 0x03010100:
        buf = buf.encode('unicode_internal')    # convert to byte string
        # buf is now local variable

    i = 0
    j = len(buf) if buf else 0
    p = 0     # unique line offset
    pline = '' # previous unique line
    for i in range(j//16):
        k = i*16
        cline = buf[k:k+16]
        if pline != cline:
            if p+1 < i:  # some line(s) were suppressed
                lines.append('%s      %d identical line(s) suppressed' % (prefix, i-(p+1)))
            p = i
            pline = cline

            if sys.hexversion > 0x03010100:
                # Python 3
                transd1=buf[k:k+16].translate(ascpribles).decode(benco)
                transd2=buf[k:k+16].translate(ep).decode(benco)
            else:
                transd1=buf[k:k+16].translate(ascpribles)
                transd2=buf[k:k+16].translate(ep)

            i1,i2,i3,i4=struct.unpack('!IIII', buf[k:k+16])
            if startaddr:
                lines.append('%s %08X %08X %08X %08X %08X %s %s'\
                  % (prefix, startaddr+k,i1,i2,i3,i4, transd1, transd2)
                  )
            else:
                lines.append('%s %04X %08X %08X %08X %08X %s %s'\
                  % (prefix, k,i1,i2,i3,i4, transd1, transd2))

    if p < i:  # lines including last line suppressed?
        lines.append('%s      %d identical line(s) suppressed' % (prefix, i-p))

    k=j//16*16
    rest=j%16
    # print('rest=',rest)
    if (rest) > 0:
        rline = '%02X'*rest % struct.unpack('B'*rest, buf[k:k+rest])\
                + (32-rest*2)*' ' # fill up with blanks
        if startaddr:
            r1 = '%s %08X %s %s %s %s '\
              % (prefix, startaddr+k, rline[0:8],rline[8:16],
                 rline[16:24],rline[24:32])
        else:
            r1 = '%s %04X %s %s %s %s '\
              % (prefix, k, rline[0:8],rline[8:16],
                 rline[16:24],rline[24:32])

        r2 = buf[k:k+rest].translate(ascpribles)+\
              (16-rest+1)*b' '+\
              buf[k:k+rest].translate(ep)

        # print(r1,r2, type(r1), type(r2))

        if sys.hexversion > 0x03010100:
            # Python 3
            lines.append( r1 + r2.decode(benco) )
        else:
            lines.append( r1+r2 )

    if header:
        lines.append('\n')

    if log:
        log('\n'.join(lines))
    else:
        print('\n'.join(lines), file=fd)


hex2buf=lambda hexbuf: \
    binascii.unhexlify(
        string.replace(
            string.replace(hexbuf, ' ',''),
            '\n','')
        )
"""
convert hexadecimal input 'hexbuf' to buffer string
blanks and CR LF are suppressed
"""

txt2buf=lambda txt: txt.replace(' ','').replace('\n','')
"""
convert text input 'txt' that may be split over se1.0.4 lines to string
blanks and CR LF are suppressed
"""


def ishexstr(str):
    """
    test string str for being all hexadecimal characters
    """
    if len(str) == 0:
        return 0
    for c in str:
        if not ord(ishex[ord(c)]):
            return 0
    return 1



def hex3buf(hexbuf):
    """
    convert TSO interpreted hex screen to buffer
    input must contain triple of interpreted and 2 hex lines
    where each column is one character
    """
    x=string.replace(hexbuf,' ','')
    lines=string.split(x,'\n')
    i=0
    s=''
    x=''
    while i+2<len(lines):
        line1 = lines[i+1]
        line2 = lines[i+2]
        if len(line1)==len(line2) and \
            ishexstr(line1) and ishexstr(line2):
            for a,b in zip(line1, line2):
                x=x+a+b
            s=s+binascii.unhexlify(x)
            i+=3
            x=''
        else:
            i+=1
    return s


def hexRbuf(hexbuf):
    """ interpret printed hex printed buffers in various formats
        formats: TSO print
    """
    x=string.replace(hexbuf,' ','')
    lines=string.split(x,'\n')
    bbuf=[]
    newbuf=''
    offset=0
    i=0
    ii=len(lines)
    while i < ii:
        line=lines[i]
        # print('i=%d, ii=%d, line=%s' % (i,ii,line))
        if line.startswith('URBH') or  \
           (ii > (i+1) and lines[i+1].startswith('5544')):
            # try TSO hex display
            if newbuf != '':
                bbuf.append(newbuf)
                # dump(newbuf)
                newbuf=''
            x=''
            while i+2<ii:
                line1 = lines[i+1]
                line2 = lines[i+2]
                if len(line1)==len(line2) and \
                    ishexstr(line1) and ishexstr(line2):
                    for a,b in zip(line1, line2):
                        x=x+a+b
                    newbuf=newbuf+binascii.unhexlify(x)
                    i+=3
                    x=''
                else:
                    i+=1
                # print('TSO line %d: %s' % (i, lines[i]))
                # dump(newbuf)
                if lines[i].startswith('x'):
                    i-=1
                    break
        elif line.startswith('x'):
            if line.startswith('x000000!') and newbuf != '':
                bbuf.append(newbuf)
                # dump(newbuf)
                newbuf=''
                offset=0
            t = string.split(line,'!')
            s1=t[0]
            s2=t[1]
            if not s1.startswith('x0'):
                break
            s1x = 'x%06x' % offset
            # print(s1)
            # print(s2)
            # print(offset, s1x)
            if s1 == s1x: # expected offset?
                newbuf+=binascii.unhexlify(s2)
                offset+=32
                # print(offset)
        i+=1
    if newbuf != '':
        bbuf.append(newbuf)
        # dump(newbuf)
        newbuf=''
    return bbuf

if __name__=='__main__':

    import getopt
    from os.path import abspath

    filename=''
    filename2=''
    maxsize=0x02000000  # 32 meg
    skip = 0
    verbose=0

    def usage():
        print(
"""dump.py - File hex dumper script

 Usage: python dump.py [--file]  <filename>
                                 <filename1>,<filename2>

 Options:

    -h, --help              display this help
    -f, --file <filename>   <filename> is file to dump or
                            file1,file2 for file difference
    -m, --maxsize <n>       limit size (bytes) of dump
    -s, --skip <s>          skip bytes from start of file
    -v, --verbose           with file difference (detailed binary)

 Example (short parameter form):
    python dump.py -f hex.bin       - prints hexdump of hex.bin
    python dump.py -f t1.bin,t2.bin - prints hexdump of t1.bin
                                      with differences from t2.bin
    python dump.py -v -f t1.bin,t2.bin  print detailed binary
                                        difference using diffbin()
                                          i.e. difflib.SequenceMatcher

""")
        return  # from usage()

    # main logic
    try:
        opts, args = getopt.getopt(sys.argv[1:],
          'hf:m:s:v',
          ['help','file=','maxsize=','skip=','verbose'])

        for opt, arg in opts:
            if opt in ('-h', '--help', '--verbose'):
                usage()
                sys.exit()
            elif opt in ('-v', '--verbose'):
                verbose=1
            elif opt in ('-f', '--file'):
                # Ensure that 2 splits occur by appending ',,'
                filename,filename2,_ = (arg+',,').split(',',2)
            elif opt in ('-m', '--maxsize'):
                maxsize = int(arg)
            elif opt in ('-m', '--maxsize'):
                skip = int(arg)
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    finally:
        if not filename and len(args) == 1:
            filename=args[0]
        elif not filename and len(args) == 2:
            filename=args[0]
            filename2=args[1]

    if filename2:
        fd = open(filename,'rb')
        fc = fd.read()
        fd.close()
        fd = open(filename2,'rb')
        fc2 = fd.read()
        fd.close()
        if verbose:
            diffbin(fc,fc2,
                     header1=abspath(filename),
                     header2=abspath(filename2))
        else:
            diffdump(fc,fc2,
                     header1=abspath(filename),
                     header2=abspath(filename2))
    else:
        fd = open(filename,'rb')
        saddr = skip
        if skip:
            fd.seek(skip, os.SEEK_CUR)

        while 1:
            fc = fd.read(maxsize)
            ll = len(fc)
            if ll:
                dump(fc,startaddr=saddr,header=abspath(filename))
                saddr+=ll
            #if ll < maxsize:
            #    break
            break
        fd.close()

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
#  $Date: 2018-04-17 13:44:55 +0200 (Tue, 17 Apr 2018) $
#  $Rev: 811 $

