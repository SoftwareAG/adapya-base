#! /usr/bin/env python
""" FTP-get specific file or PDS member from z/OS
    converted to ASCII or
    binary variable blocked sequential dataset as binary with
    RDW record prefix

    Usage: getfilez [options]

    The records of the local file can be dumped setting the --verbose switch 4
    and a selected with --numrec and --skiprec parameters (example 3 below).

    Options:
        -a  --ascii         transfer with EBCDIC to ASCII conversion
        -b  --binary        binary transfer (variable blocked) with RDW prefix
        -d  --dsn           remote sequential dataset name
        -e  --ext           extension (default .s) for member names if no fname specified
        -f  --fname         local file name (optional)
        -c, --config        set/show configuration
        -C, --certfile      certificate file (.pem)
        -n  --numrec        with verbose & 4: number of records to print
        -p, --pwd           <password>  FTP ser1.3.0ogin password (*)
        -u, --user          <userid>                              (*)

        -r, --recform       specifies the record structure:
                            'RDW' variable records include Record
                                  Descriptor Word which is skipped
                            'RDW+' same as RDW but also return RDW
                            'BDW' data includes Block Descriptor Word
                                  which is skipped (RECFM=U)
                            'BDW+' same as BDW, bu also return record with RDW
                            'EXCL4' 4 byte excl. length prefix
        -s  --skiprec       with verbose & 4: number of records to skip
        -v, --verbose       0: (default), 1: log ftp, 2: detailed ftp,
                            4: dump records
        -x, --xlate         full dataset name of the hlq.name.TCPXLBIN translate table
                            on mainframe for EBCDIC to ASCII conversion
                            using the "site SBDATACON=<xlate>
        -h, --host          <host name> of IBM FTP server         (*)
        -?, --help

    defaults marked with (*) are taken from configuration (-c)
    The configuration values are stored ciphered in file ~/.toolz

    Examples:

    1. set configuration user, password

       >> getfilez --config --user hugo --pwd secret

    2. read remote dataset with verbose FTP operations, user and password
       are taken from configuration. File is processed binary and RDW record
       headers are preserved

       >> getfilez -bd mm.db8.uld1 -r RDW -h da3f -v2

    3. dump VB records in local file limited by skiprec and numrec

       >> getfilez -f mm.db8.uld1 -r RDW -v4 -n 1000 -s 1222000

    4. copy member EPILOG from PDS to local file epilog.s and convert to ASCII

       >> getfilez -ad mm.pds(epilog)


"""
from __future__ import print_function          # PY3

__date__='$Date: 2023-12-07 14:28:09 +0100 (Thu, 07 Dec 2023) $'


import sys,os
import getopt
from adapya.base.ftptoolz import Ftpzos
from adapya.base.jconfig import getparms,setparms,SHOWCONFIG
from adapya.base.recordio import readrec
from adapya.base.defs import evalb
from adapya.base.dump import dump

if sys.hexversion < 0x03010100:
    PY3=False
else:
    PY3=True



# default values
host=None
user=None
pwd=None
certfile = None
ext='.s'

binary=None
config=0
dsn=''      # Dataset name
fname=''    # local file name
numrec=0
recform=''
skiprec=0
verbose=0
xlate=''    # hql.<xlate>.TCPXLBIN translation table on mainframe

def usage():
    print(__doc__)

try:
  opts, args = getopt.getopt(sys.argv[1:],
    '?abd:e:f:h:n:p:r:s:u:cC:v:x:',
    ['help','ascii','binary','dsn=','ext=','file=','host=','pwd=',
        'recform=','user=','config','certfile=','verbose:','xlate='])
except getopt.GetoptError:
  print(sys.argv[1:])
  usage()
  sys.exit(2)
if len(sys.argv)==1:
    usage()
    sys.exit(2)
for opt, arg in opts:
   # print(opt, arg)
  if opt in ('-?', '--help'):
    usage()
    sys.exit()
  elif opt in ('-C', '--certfile'):
    certfile = arg
  elif opt in ('-c', '--config'):
    config=1
  elif opt in ('-a', '--ascii'):
    if binary==None:
        binary=0
    else:
        print("--ascii or --binary (-a/-b) may only be specified once")
        usage()
        sys.exit()
  elif opt in ('-b', '--binary'):
    if binary==None:
        binary=1
    else:
        print("--ascii or --binary (-a/-b) may only be specified once")
        usage()
        sys.exit()
  elif opt in ('-d', '--dsn'):
    # z/OS ftp distinguishes datasets from files if dataset name is
    # enclosed with quotes (')
    dsn = "'%s'" % arg
  elif opt in ('-e', '--ext'):
    if arg.upper() == 'NONE':
        ext = ''
    else:
        ext = arg
  elif opt in ('-f', '--file'):
    fname = arg
  elif opt in ('-h', '--host'):
      host=arg
  elif opt in ('-n', '--numrec'):
      numrec=int(arg)
  elif opt in ('-p', '--pwd'):
      pwd=arg
  elif opt in ('-r', '--recform'):
      recform=arg.upper()
  elif opt in ('-s', '--skiprec'):
      skiprec=int(arg)
  elif opt in ('-u', '--user'):
      user=arg
  elif opt in ('-v', '--verbose'):
      verbose=int(arg)
  elif opt in ('-x', '--xlate'):
      xlate=arg

if config:
    """
    ftpcfg={}
    if host: ftpcfg['host'] = host
    if pwd:  ftpcfg['pwd']  = pwd
    if user: ftpcfg['user'] = user
    if ftpcfg:
        print('Updating configuration file .ztools')
        setparms('ftp',SHOWCONFIG,**ftpcfg) # only update parms if not default
    """
    if host or pwd or user or certfile:
        print('Updating configuration file .ztools')
        setparms('ftp',SHOWCONFIG,host=host,pwd=pwd,user=user,certfile=certfile) # only update parms if not default
    else:
        print('Reading configuration file .ztools')
        getparms('ftp',SHOWCONFIG,host='',user='',pwd='',certfile='') # emtpy parms
    sys.exit()

if dsn and binary==None:
    print("--ascii or --binary (-a/-b) must be specified")
    usage()
    sys.exit(1)


if dsn:
    # get ftp parameters (host,user,pwd) if not set by caller
    ftpcfg = getparms('ftp',verbose,host=host,user=user,pwd=pwd,certfile=certfile)
    host=ftpcfg.get('host','') # make sure that parms are not None
    pwd=ftpcfg.get('pwd','')
    user=ftpcfg.get('user','')
    certfile=ftpcfg.get('certfile','')

    if not fname:
        import re
        fname = dsn.strip("'") # remove quotes
        # check if pds(member) specified, valid special chars $,#,@
        #                                <- member name->
        m=re.match('[A-Za-z0-9@#\.\$]+\(([A-Za-z0-9@#\$]+)\)',fname)
        if m:
            fname = m.group(1)+ext  # extract member name and add extension

    ftpz=Ftpzos(host,user,pwd,certfile=certfile,verbose=verbose,test=0)  # zos jes extensions
    ftp=ftpz.ftp # ftplib.FTP session for orinary ftp commands

    if binary:
        ftpz.getbinaryfile(dsn,fname,rdw=1 if recform else 0) # read file with variable records if recform specified
    else:
        ftpz.getfile(dsn,fname,xlate=xlate) # read file with variable records


    print('Sequential dataset %s%s copied to local %s' % (dsn, ' binary' if binary else '' ,fname))

    ftp.quit()     # do not reuse ftp.
    # now the file is locally accessible

if verbose&4:
    # dump records
    with open(fname,'rb') as f:
        if binary and not recform:
            MAXSIZE = 0x10000 # 32k
            saddr = 0
            while 1:
                fc = f.read(MAXSIZE)
                rlen = len(fc)
                if rlen:
                    dump(fc,startaddr=saddr,header=fname)
                    saddr+=rlen

                if rlen < MAXSIZE:
                    break
            if saddr == 0:
                print('File %s is empty' % fname)
        else:
            for record in readrec( f, recform=recform, numrec=numrec, skiprec=skiprec,
                              dumphdr='Record'):
                pass

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
