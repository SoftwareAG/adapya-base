*****************
Using adapya-base
*****************

Read/Write Buffers with Abuf
============================

Implemented in `adapya.base.defs`

Read/write buffers are not directly available in Python only indirectly
with I/O routines.

The adapya.base.defs.Abuf class implements read/write buffers. They are used for the Adabas
control block and other buffers.::

 >>> from adapya.base.defs import Abuf # Access Abuf class
 >>> a=Abuf(8) # Allocate buffer of 8 bytes
 >>> a.value=b'Bell' # store 'Bell' into buffer a
 >>> a.raw # show contents of a
 b'bell\x00\x00\x00\x00'

 >>> a[0:8]   # same in slice notation
 b'bell\x00\x00\x00\x00'

 >>> a[0:4]  # extract part of buffer
 b'bell'

 >>> a[0]=b'W' # modify buffer at offset 0
 b'Well\x00\x00\x00\x00'

 >>> a.read(5) # read() 5 bytes of the buffer
 b'Well\x00'

 >>> a.read(5) # read() next bytes (only 3 left)
 b'\x00\x00\x00'

 >>> a.tell() # inquire position
 8

 >>> a.seek(0) # position to start of buffer
 >>> a.write('Sun') # write first 3 characters
 b'Sunl\x00\x00\x00\x00'


Working with Structures with Datamap
====================================

Implemented in `adapya.base.datamap`

The datamap module defines the Datamap class that allows to define
structure within a byte buffer. This is similar to a DSECT or C struct.
This is being used for setting up the Adabas control block and the other
buffers like record buffer or value buffer.

Datamap Data Types
------------------

The following data types require a name and a length:

String
  alpha numeric string

Unicode
  Unicode string (in UTF-16, each character takes 2 bytes)

Bytes
  similar to String but hexadecimal contents

Packed
  integer mapped to P format

Unpacked
  integer mapped to U format


The other data types take only the name:

Char
  1 byte character

Int1/2/4/8
  signed integer of 1, 2, 4 or 8 bytes

Uint1/2/4/8
  unsigned integer of 1, 2, 4 or 8 bytes

Float
  single precision float (IEEE format)

Double
  double precision float (IEEE format)


Basic Usage example
-------------------
::

 >>> from adapya.base.defs import Abuf
 >>> from adapya.base.datamap import Datamap, String, Int2
 >>> dm=Datamap('mymap',
         String('name',6),  # List of field definitions. Its order
         Int2('age')) # defines the position in the buffer
 >>> dm.getsize() # query the size of the datamap dm
 8
 >>> a=Abuf(8)
 >>> dm.buffer=a  # use buffer a with datamap dm
 >>> dm.name='Bell' # assign name
 >>> dm.age=64 # assign age
 >>> dm.dprint()  # print out all values of datamap dm
 mymap
 name = "Bell"
 age = 64

 >>> dm.age  # individual attribute access
 64
 >>> dm.name
 'Bell'
 >>> dm.name='12345678' # silent truncation (field size defined = 6)
 >>> dm.name
 '123456'
 >>> dm.name='1234 ' # silent blank truncation on return
 >>> dm.name
 '1234'


Example showing the different data types
----------------------------------------
::

 from adapya.base.datamap import Datamap, String, Unicode, Utf8, Bytes,
     Char, Int1, Uint1, Int2, Uint2, Int4, Uint4, Int8, Uint8,
     Float, Double, Unpacked

 p = Datamap( 'test_all_formats',
        String( 'str8', 8),
        Unicode('uni4', 4), # unicode 4 chars = 8 bytes
        Utf8( 'utf8', 8),
        Bytes( 'byt4', 4),
        Char( 'cha1'),
        Int1( 'int1'),
        Uint1( 'uin1'),
        Int2( 'int2'),
        Uint2( 'uin2'),
        Int4( 'int4'),
        Uint4( 'uin4', opt=T_STCK), # Uint4 STCK
        Int8( 'int8'),
        Uint8( 'uin8', opt=T_STCK), # Uint8 STCK
        Float( 'flo4'),
        Double( 'dou8'),
        Unpacked( 'dati', 14, dt='DATETIME'), # Python datetime object
        )

With Uint4 and Uint8 the additional option T\_STCK indicates that the
value is a timestamp value in mainframe STCK format. This is evaluated
with the dprint() function to print the timestamp in readable ISO
format.

An *Unpacked* field defined with the dt option (value 'DATETIME' or
'TIMESTAMP') work with Python datetime() objects::

 >>> from datetime import datetime
 >>> p.dati = datetime.now()
 >>> print p.dati
 2010-05-01 11:55:00

 >>> _,pos,ln,_,_ = p.keydict['dati']
 >>> p.buffer[pos:pos+ln]
 '20100501115500'

Note that a datetime value of zero corresponds to the Python **None**
type::

 >>> p.dati = None
 >>> print p.dati
 None
 >>> p.buffer[pos:pos+ln]
 '00000000000000'


Defining Multiple fields
------------------------

If the keyword **occurs** is added to the end of the field definition
it becomes a multiple value field.

.. note:: The field access does not return the field value but an iterator
   over the occurrences values - see m.languages as in the example below::

     >>> from adabas.datamap import Datamap, String
     >>> from adabas import Abuf
     >>> m = Datamap('mulitple_demo', String('languages', 3, occurs=5),
                 buffer=Abuf(100))
     >>> m.languages=('ENG','FRA','GER')
     >>> m.languages[2]
     'GER'
     >>> m.languages[2]='RUS'

     >>> for lang in m.languages:
           print lang
     ENG
     FRA
     RUS


Defining Periodic Group
-----------------------

If the field definition within a datamap contains a periodic ()
definition a datamap at the present location is defined.
::

 from adapya.base.datamap import Datamap, String, Packed
 p = Datamap( 'Periodics Demo',
              ...
              Periodic(
                Datamap('Income',
                  String( 'currency', 3),
                  Packed( 'annual', 5)
                  ),
                occurs=8),
              ...
              )

 >>> print len(p.income)
 8

 p.income[0].currency = 'EUR'
 p.income[0].annual = 99000


