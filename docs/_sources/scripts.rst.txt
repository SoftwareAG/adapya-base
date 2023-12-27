*******
Scripts
*******

There are some scripts in adapya.base.scripts that can be run on the command line.
Usually they accept Unix style parameters. A help page is shown with the help option.

* ftpz.py - synchronize partitioned datasets with local folders
* getfilez.py - transfer single file and dump records
* jesjob.py - JES Spool Handler (list, read, etc.) via FTP(s)
* smfreaderz.py - read and interpret SMF30 records


ftpz.py - synchronize PDS with local files in folders
=====================================================

ftpz.py synchronizes remote partitioned datasets on z/OS with
local files in folders.

The syncronization depends on the modification time stamps
in the file system and the PDS directory

Usage: ftpz.py [options]::

    [-h] [-k] [-c certfile][-e [EXT]] [-n HOST] [-p PWD] [-s SITE] [-u USER]
    [-r] [-t] [-v VERBOSE] [-d PREFIX] [-x [EXCLUDE [EXCLUDE ...]]]
    [-i [INCLUDE [INCLUDE ...]]]
    {upsync,upload,download,downsync,config} [pds]

Positional arguments:

  {upsync,upload,download,downsync,config}:

  - upsync: upload changed members to partioned dataset (PDS) and
            delete members not existing in source

  - upload: upload changed files to partioned datasets (PDS)

  - download: download changed files from partioned datasets (PDS)

  - downsync: download changed members from partioned dataset (PDS)
            and delete members not existing in PDS
  - config: display or set configuration pds -
            Partitioned Dataset name w/o quotes. With ending
            period: parameter is used as high-level qualifier

Optional arguments::

  -h, --help            show this help message and exit
  -c, --certfile        Security certificate file (.pem for ftp server)
  -k, --keepsame        On download/sync do not overwrite old file if contents
                        same as new file
  -e [EXT], --ext [EXT]
                        extension to process (default is .s) e.g. -e .c -e
                        without argument: no extension
  -n HOST, --host HOST  ftp z/OS host name
  -p PWD, --pwd PWD     ftp z/OS user id
  -s SITE, --site SITE  Set ftp server options per quote site
  -u USER, --user USER  ftp z/OS user password
  -r, --ignerr          ignore ftp member access errors
  -t, --test            dry run - list actions only
  -v VERBOSE, --verbose VERBOSE
                        verbose output (1 to 3)
  -d PREFIX, --prefix PREFIX
                        dataset prefix
  -x [EXCLUDE [EXCLUDE ...]], --exclude [EXCLUDE [EXCLUDE ...]]
                        list of libraries/members to exlude from processing
  -i [INCLUDE [INCLUDE ...]], --include [INCLUDE [INCLUDE ...]]
                        list of libraries/members to include in processing

Examples:

1. sync-up PDS mm.test.adasrc from current directory and delete
   member that do not exist in source::

     > ftpz upsync --user xyz --pwd secret --host zmax MM.TEST.ADASRC

2. update all changed members PDS mm.test.adasrc from current directory::

     > ftpz upload --user xyz --pwd secret --host zmax MM.TEST.ADASRC

3. ftpz upsync -t mm.test.adasrc   # dry run without updating

4. set configuration default values::

      >  ftpz config --user xyz --host bfg1 --certfile CA.pem # set config
      >  ftpz config                                          # list config

      >  ftpz upload MM.TEST.ADASRC                           # use config

    When a configuration file is set up with the most common parameters in use -
    (user, host and password (pwd)) these do not have to be typed
    on each script execution. The password is stored in keyring
    if the keyring package is installed otherwise it is stored in the
    configuration file encrypted so that it is not plainly readable on the
    command line. See example 2.


5. download

   Download all missing or changed members of PDS mm.test.adasrc to
   current directory::

     > ftpz download MM.TEST.ADASRC

6. downsync

   Same as 'download' and in addition delete members in directory that
   are missing in PDS::

     > ftpz downsync MM.TEST.ADASRC

7. download all changed members for all PDS starting with high-level quailfier (HLQ).

   The current directory is used as the base matching its subdirectories name with
   partitioned datasets HLQ.name. Optionally exclude or include parameters can
   specifiy a list of libraries to exclude or include separated by space::

     > ftpz download mm.test. --exclude unwanted abandond

   will process pds mm.test.source and mm.test.macros but
   exclude mm.test.unwanted and mm.test.abandond

8. download specific missing or changed members 'FOO' and 'BAR' of a PDS as
   foo.s and bar.s in current directory::

     > ftpz download mm.test.source --include foo bar

9. download to use extension .c and special translation table for
   ibm-1047 to ibm-819 with EBCDIC LF = 0x15

     > ftpz download mm.c.source -e .c -s sbdataconn=MM.OEMVS31.TCPXLBIN




getfilez.py - transfer single file and optionally dump records
==============================================================

Read specific dataset or PDS member from z/OS per FTP
converted to ASCII or binary.

Datasets may be variable blocked sequential dataset as binary with
RDW record prefix.

Usage: getfilez [options]

The records of the local file can be dumped setting the --verbose switch 4
and a selected with --numrec and --skiprec parameters (example 3 below).

Options::

    -a  --ascii         transfer with EBCDIC to ASCII conversion
    -b  --binary        binary transfer (variable blocked) with RDW prefix
    -d  --dsn           remote sequential dataset name
    -e  --ext           extension (default .s) for member names if no
                        fname specified
    -f  --fname         local file name (optional)
    -c, --config        set/show configuration
    -C, --certfile      certificate file (.pem)

    -n  --numrec        with verbose & 4: number of records to print
    -p, --pwd           <password>  FTP ser1.3.0ogin password (*)
    -u, --user          <userid>                              (*)

    -r, --recform       specifies the record structure:
                        'RDW' variable records inlcude Record
                              Descriptor Word which is skipped
                        'RDW+' same as RDW but also return RDW
                        'BDW' data includes Block Descriptor Word
                              which is skipped (RECFM=U)
                        'BDW+' same as BDW, bu also return record with RDW
                        'EXCL4' 4 byte excl. length prefix
    -s  --skiprec       with verbose & 4: number of records to skip
    -v, --verbose       0: (default), 1: log ftp, 2: detailed ftp,
                        4: dump records
    -x, --xlate         full dataset name of the hlq.name.TCPXLBIN translate
                        table on mainframe for EBCDIC to ASCII conversion
                        using the "site SBDATACON=<xlate>
    -h, --host          <host name> of IBM FTP server         (*)
    -?, --help

Defaults marked with (*) are taken from configuration (-c)
The configuration values are stored ciphered in file ~/.toolz

Examples:

1. set configuration user, password::

     > getfilez --config --user hugo --pwd secret

2. read remote dataset with verbose FTP operations, user and password
   are taken from configuration. File is processed binary and RDW record
   headers are preserved::

     > getfilez -bd mm.db8.uld1 -r RDW -h da3f -v2

3. dump VB records in local file limited by skiprec and numrec::

     > getfilez -f mm.db8.uld1 -r RDW -v4 -n 1000 -s 1222000

4. copy member EPILOG from PDS to local file epilog.s and convert to ASCII::

     > getfilez -ad mm.pds(epilog)


jesjob.py - Z/OS JES Spool Reader via FTP
=========================================

Usage: python jesjob.py [options]

The following functions are available:

    -  read    jobnr
    -  del     jobnr
    -  list
    -  subget  member


Options::

        -h, --host        * <host name> of FTP host (IBM FTP server)
        -u, --user        * <userid>
        -p, --pwd           <password>  password for login to FTP server
        -C, --certfile    * <file>      .pem file with server certificates

        -c, --config                    set/show configuration
        -d  --delete                    delete jobs in SPOOL
        -l  --list                      list jobs
        -g  --subget                    submit and get result
        -r, --read                      read job number
        -?, --help

        -e, --edit                      call editor with spool file read
        -x, --xedit       * <editor>    full path name of editor executable
        -j, --jobid         <jobid>     job id, eg. JOB12345/STC54321
                                           or just 12345
        -o, --jobowner    * <jobowner>  JESOWNER (default *)
        -n, --jobname     * <jobname>   JESJOBNAME
        -s, --jobstatus   * <jobstatus> JESTATUS in [ALL,ACTIVE,OUTPUT(default)]

                          * marked parameters may be stored in config file

Examples:

1. read Job Spool files to local file JOB1234.X.txt::

   > python jesjob.py --read --jobid JOB1234 --user hugo --pwd secret

2. set configuration user, password and default editor::

   > python jesjob.py --config --user hugo --pwd secret --xedit c:/prog/xedit.exe

3. list jobs in spool::

   > python jesjob.py --list --jobid MM*

4. submit job and get result::

   > python jesjob.py --subget uid.jobs(adarep)

A configuration file can be set up with the most common parameters in use -
e.g. user, host and password (pwd). Then these do not have to be typed
on each jesjob execution. The password is encrypted so that it is not
plainly readable on the command line. See example 2.



smfreaderz.py - read and print SMF30 records
============================================

Usage: smfreaderz [options]::

   options:

       -d  --dsn      <smf dataset name>  remote SMF file
       -f  --file     <file> local SMF file
       -b  --bfile    <file> local SMF file VB blocked with BDW

       -k, --skiprec  <int>   number of records to skip
       -m, --maxrec   <int>  maximum number of records
       -p, --pwd      <password>  FTP ser1.3.0ogin password (*)
       -u, --user     <userid> FTP ser1.3.0ogin userid      (*)
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


The following command (on Windows cmd) will select SMF30 records
with program name ADARUN from a SMF system dataset::

 >>> smfreaderz -v3 -s JOB=MM10026 -d ZMAX.SMFDAY.G3037V00

Record selected by condition [' JOB=MM10026']::

  --- Record 181197: SMF30 ---

  Product or Subsystem Section
  SMF30 sub type         = Step total
  Record version number  = '05'
  Subsystem product name = 'SMF'
  MVS product level      = 'SP7.2.1'
  System name            = 'ZMAX'
  Sysplex name           = 'MAXPLEX'


  Job/Session Id Section
  Job/session name             = 'MM10026'
  Program name                 = 'ADARUN'
  Step name                    = 'ADANUC'
  JES job id                   = 'S0207297'
  Step number                  = 1
  Device allocation start time = 14:35:54.95
  Problem program start time   = 14:35:55.23
  Time initiator selected step = 14:35:54.95
  Date initiator selected step = 2018.079
  Time reader found job card   = 14:35:54.79
  Date reader found job card   = 2018.079
  Time reader found end of job = 14:35:54.82
  Date reader found end of job = 2018.079
  RACF group id                = 'MFRAME'
  RACF user id                 = 'RACFSTC'
  Step name invoking procedure = 'STARTING'
  Job class                    = 'STC'
  Interval start time          = 2018-03-20 14:35:54.955237.078
  Interval end time            = 2018-03-20 14:56:26.669574.079
  Address space id             = X'012E'


  CPU accounting section
  Timer Flag1                                  = X'80'
  Step CPU time under TCB                      = 00:00:45.18
  Step CPU time under SRB                      = 00:00:12.24
  Initiator CPU time under TCB                 = 00:00:00.30
  CPU time I/O Interrupts                      = 00:00:06.26
  Step dependent enclave CPU time              = 00:00:44.62
  Time on zIIP                                 = 00:00:42.66
  Dependent enclave time on zIIP               = 00:00:42.66
  zIIP time on CP                              = 00:00:03.06
  Dependent enclave zIIP time on CP            = 00:00:03.06
  Dependent enclave zIIP time on CP normalized = 00:07:51.38
  CPU TCB time for step init                   = 00:00:00.24
  Highest Task Program name                    = 'IEESB605'

  Performance section
  zIIP normalization factor = 1.98


To run this in z/OS batch the dataset must be referenced via DD name 'SMF'::

  //MMSMF30  JOB MM,CLASS=G,MSGCLASS=X,LINES=100
  //*
  //* smfreaderz.py reads SMF files from DD:SMF
  //* -h option will print usage / description
  //*
  //BPX      EXEC PGM=BPXBATSL
  //SMF DD DISP=SHR,DSN=OPS.ZMAX.SMFDAY.G3037V00,DCB=(RECFM=U)
  //STDPARM  DD *
  PGM /usr/mm/py27/bin/python
     /usr/mm/apy/smfreaderz.py -b dd:SMF -v3
     -s JOB=MM10026
  /*
  //STDOUT   DD SYSOUT=*
  //STDERR   DD SYSOUT=*
  //STDENV   DD PATH='/usr/mm/apy/batsl.env',PATHOPTS=ORDONLY
  //



