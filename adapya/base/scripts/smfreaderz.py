""" Reader for  SMF records - selects SMF30 records

    Usage: smfreaderz [options]

    options:
        -d  --dsn      <smf dataset name>  remote SMF file
        -f  --file     <file> local SMF file
        -b  --bfile    <file> local SMF file VB blocked with BDW

        -k, --skiprec  <int>   number of records to skip
        -m, --maxrec   <int>  maximum number of records
        -p, --pwd      <password>  FTP server login password (*)
        -u, --user     <userid> FTP server login userid      (*)
        -h, --host     <host name> of IBM FTP server         (*)

        -s, --select   <record selection criteria> see below (**)

        -c, --config   Set/show configuration
        -v, --verbose  level of printed information (default 2)
        -?, --help

    (**) record selection criteria  kw1=val1[,kw2=val2]
         enclose hole string with " if it contains blanks
         valid keywords: job, id, user, group, prog
         Criteria must be all fulfilled to select a record
         Example: -s job=*MM*,group=RND,id=J*,prog=*ASM

    (***) verbose level, composable: 1 - stats SMF records
            2 - detailed print selected SMF records, 4 - dump records,
            8 - debug


    Defaults marked with (*) are taken from configuration.
    The configuration for user specific parameters can be stored
    with the --config option.

    The reader can transfer the file (--dsn) per FTP from a remote z/OS
    with the RDW option or can access the file locally if already
    transfered (--file). On z/OS the --bfile option may be used.

    Option -b/--bfile if file includes block descriptor word (BDW)
    e.g. when running on z/OS with DCB=(RECFM=U) override on DD stmt


    Examples:

    1. set configuration user, password
        smfreaderz --config --user hugo --pwd secret

    2. read remote SMF dataset and print
        smfreaderz -d cc.sysa.smf -h sysa

"""
from __future__ import print_function          # PY3
import sys,os
import getopt
from collections import Counter
from adapya.base.ftptoolz import Ftpzos
from adapya.base.jconfig import getparms,setparms,SHOWCONFIG
from adapya.base.dump import dump
from adapya.base.recordio import readrec
from adapya.base.smfrecordz import Smf, Smf30, Smf30pss, Smf30id,\
    Smf30prf, Smf30cas, SMFWOS, i2dt

__date__='$Date: 2018-05-07 15:13:26 +0200 (Mon, 07 May 2018) $'
__version__='$Rev: 818 $'

# default values
host=None
user=None
pwd=None

config = 0
dsn = ''         # Dataset name
fname = ''       # local file name
verbose = 2
block_rlen = 0   # block rest length
maxrec = 0       # maximum of records to read
recform = 'RDW+' # parameter for recordio: returns records including RDW
recno = 0        # record counter
skiprec = 0      # number of records to skip

#selection criteria
select=''
juser = ''
jobname = ''
jobid = ''
jprog = ''
jgroup = ''


if sys.hexversion < 0x03010100:
    PY3=False
    bbyte=lambda i: chr(i)
else:
    PY3=True
    bbyte=lambda i: chr(i).encode('ascii')

def selecting(x, sval):
    """ check if string sval is present in string x
        sval may beging and/or end with '*' for wild card search

        :returns: True if sval found in x or if sval empty
    """
    if not sval:
        return True
    if sval.startswith('*'):
        if sval.endswith('*'):
            return sval[1:-1] in x
        else:
            return x.endswith(sval[1:])
    elif sval.endswith('*'):
        return x.startswith(sval[:-1])
    else:
        return x == sval



def usage():
    print(__doc__)

try:
  opts, args = getopt.getopt(sys.argv[1:],
    '?b:d:f:h:k:m:p:s:u:cv:',
    ['help','bfile=','file=','host=','pwd=','maxrec=',
        'select=','skiprec=','user=','config','verbose='])
except getopt.GetoptError:
  print( sys.argv[1:])
  usage()
  sys.exit(2)
if len(sys.argv)==1:
    usage()
    sys.exit(2)
for opt, arg in opts:
   # print opt, arg
  if opt in ('-?', '--help'):
    usage()
    sys.exit()
  elif opt in ('-c', '--config'):
    config=1
  elif opt in ('-d', '--dsn'):
    dsn = "'%s'" % arg
  elif opt in ('-f', '--file'):
    fname = arg
  elif opt in ('-b', '--bfile'):
    fname = arg
    recform = 'BDW+'    # file includes Block Descriptor Word (BDW)
  elif opt in ('-h', '--host'):
      host=arg
  elif opt in ('-k', '--skiprec'):
    skiprec = int(arg)
  elif opt in ('-m', '--maxrec'):
    maxrec = int(arg)
  elif opt in ('-p', '--pwd'):
      pwd=arg
  elif opt in ('-s', '--select'):
    select = arg.split(',')
    if len(select) > 0:
        for ss in select:
            k, v = ss.upper().split('=')
            if k == 'JOB': jobname = v
            elif k == 'ID': jobid = v
            elif k == 'USER': juser = v
            elif k == 'GROUP': jgroup = v
            elif k == 'PROG': jprog = v
            else:
                print('Invalid selection keyword: %s=%s' % (k,v))
                sys.exit(9)

  elif opt in ('-u', '--user'): # ftp user to transfer file
      user = arg
  elif opt in ('-v', '--verbose'):
      verbose = int(arg)

if config:
    """
    ftpcfg={}
    if host: ftpcfg['host'] = host
    if pwd:  ftpcfg['pwd']  = pwd
    if user: ftpcfg['user'] = user
    if ftpcfg:
        print( 'Updating configuration file .ztools')
        setparms('ftp',SHOWCONFIG,**ftpcfg) # only update parms if not default
    """
    if host or pwd or user:
        print( 'Updating configuration file .ztools')
        setparms('ftp',SHOWCONFIG,host=host,pwd=pwd,user=user) # only update parms if not default
    else:
        print( 'Reading configuration file .ztools')
        getparms('ftp',SHOWCONFIG,host='',user='',pwd='') # emtpy parms
    sys.exit()

oldest=None
latest=None

if dsn:
    # get ftp parameters (host,user,pwd) if not set by caller
    ftpcfg = getparms('ftp',verbose,host=host,user=user,pwd=pwd)
    host=ftpcfg.get('host','') # make sure that parms are not None
    pwd=ftpcfg.get('pwd','')
    user=ftpcfg.get('user','')

    if not fname:
        fname = dsn.strip("'") # remove quotes

    ftpz=Ftpzos(host,user,pwd,verbose=verbose,test=0)  # zos jes extensions
    ftp=ftpz.ftp # ftplib.FTP session for orinary ftp commands

    ftpz.getbinaryfile(dsn,fname,rdw=1) # read SMF file with variable records
    print( 'SMF dataset %s copied to local %s' % (dsn, fname))

    ftp.quit()     # do not reuse ftp.
    # now the file is locally accessible

smfcounter = Counter()
smf=Smf()
smfrec30 = Smf30()

s30id  = Smf30id()  # Job/sesion id
s30pss = Smf30pss() # product or subsystem
s30cas = Smf30cas() # processor / CPU accounting
s30prf = Smf30prf() # Performance

secttab=[  #o = no yet defined
    # section class, offset from ID section, 0/1 use line print rather than detail
    ( s30pss,     0x00, 0), # Subsystem section
    ( s30id,      0x08, 0), # ID section
#o  ( Smf30ura(), 0x10, 0), #- I/O activity
#o  ( Smf30cmp(), 0x18, 0), #- Completion
    ( s30cas,     0x20, 0), # Processor / CPU accounting
#o  ( Smf30acs(), 0x28, 0), # Accounting
#o  ( Smf30sap(), 0x30, 0), # Storage
    ( s30prf,     0x38, 0), # Performance
#o  ( Smf30ops(), 0x40, 0), # Operator
#o  ( Smf30xxx(), 0x48, 0), # EXCP
#o  ( Smf30dr(),  0x58, 0), # APPC/MVS
#o  ( Smf30ar(),  0x60, 0), # APPC/MVS cumulative
#o  ( Smf30dr(),  0x68, 0), # openMVS
#o  ( Smf30op(),  0x74, 0), # Usage
#o  ( Smf30rm(),  0x80, 0), # First ARM section
#o  ( Smf30mse(), 0x8c, 0), # Multi-System enclave Remote System Data
#o  ( Smf30cds(), 0x98, 0), # Counter data
#o  ( Smf30uss(), 0xa0, 0), # zEDC usage
    ]

with open(fname,'rb') as f:
    for record in readrec( f, recform=recform, numrec=maxrec, skiprec=skiprec,
                          debug=1 if verbose&8 else 0):
        rlen = len(record)
        recno += 1

        if rlen < SMFWOS: # smallest SMF record is without subtypes (0x12)
            print( 'SMF Record %d has invalid record length %d (shorter than SMF record header %d)' % (
                recno, rlen, SMFWOS))
            continue

        smf.buffer=record # map data of underlying buffer

        smfcounter[ smf.rty ] += 1  # count each smf record type

        if not oldest:
            oldest = i2dt( smf.dte, smf.tme)  # datetime() of first record after skipping
        latest = (smf.dte,smf.tme)

        if smf.rty != 30:
            if verbose & 8:
                print( '--- skipping other SMF record %d ---' % recno)
                smf.dprint(skipnull=1)
            continue

        smfrec30.buffer = record

        if verbose & 8:
            dump(record[0:rlen],header='SMF30 record %d' % recno)

        if rlen < smfrec30.dmlen :
            print( 'SMF Record %d has invalid record length %d (shorter than %d)' % (
                recno, rlen, smfrec30.dmlen))
            break
        smfrec30.buffer=record # update underlying buffer

        if verbose & 8:
            print( '--- Record %d: SMF30 ---' % recno)
            smfrec30.dprint(skipnull=1)

        if select and smfrec30.ion:   # selection and id section exists
            s30id.buffer = record
            s30id.offset = smfrec30.iof  # offset from start of record with RDW

            # print('rud=%s, user=%s, selecting=%r' % (s30id.rud, juser, selecting(s30id.rud,juser)))

            if not selecting(s30id.rud, juser):
                continue
            if not selecting(s30id.jbn, jobname):
                continue
            if not selecting(s30id.jnm, jobid):
                continue
            if not selecting(s30id.pgm, jprog):
                continue
            if not selecting(s30id.grp, jgroup):
                continue
            if verbose & 2:
                print('Record selected by condition %s'% select)

        if verbose & 4 and not verbose & 8:
            dump(record[0:rlen],header='SMF30 record %d' % recno)

        if verbose & 2:
            print( '--- Record %d: SMF30 ---' % recno)

        for section, sectoff, sectline in secttab: # loop through all
            smfrec30.offset=sectoff
            sectoff = smfrec30.sof
            sectlen = smfrec30.sln
            sectnum = smfrec30.son

            if sectlen < section.dmlen:
                if sectlen:
                    print( 'WARNING: Record %d section length %d is shorter than defined %d for %s; skipping' % (
                        recno, sectlen, section.dmlen, section.dmname))
                continue
            elif sectlen > section.dmlen:
                print( 'WARNING: Record %d has larger section length %d than defined %d for %s)' % (
                    recno, sectlen, section.dmlen, section.dmname))

            section.buffer=record
            section.offset=sectoff

            if sectnum > 1:
                # do not repeat printing dmname on line print
                sectname, sectend = ('','') if sectline else (section.dmname,'\n')

                print( '\n Record %d has %d sections for %s' % (
                    recno, sectnum, sectname),end=sectend)
            else:
                print()

            col1 = ''
            if sectline:    # use lprint() to print values in columns
                section.lprint(header=1,col1=col1,indent=1)   # print column header

            # print(section.dmname, sectnum)

            for j in range(1,sectnum+1):
                if sectline:
                    section.lprint(col1=col1,indent=1)
                else:
                    section.dprint(skipnull=1)

                section.offset+=sectlen

        smfrec30.offset=0 # reset offse

skips = ' - skipped %d' % skiprec if skiprec > 0 else ''
print('\nSMF file %s processed %d records%s' % (fname, recno, skips))
if oldest:
    print('\n    oldest record %s' % oldest)
if latest:
    print('\n    latest record %s' % i2dt(*latest))


if verbose & 1:
    print('\nRecord counts per SMF type:')
    for smftyp, smfcnt in sorted( smfcounter.items() ):
        print('SMF%-3d %6d' % (smftyp, smfcnt))


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
