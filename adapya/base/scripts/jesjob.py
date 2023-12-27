#! /usr/bin/env python
# -*- coding: latin1 -*-
"""
    ---- jesjob.py -- Z/OS JES Spool Reader via ftp ----

    Read Jobs in Spool

    Usage: python jesjob.py [options]

    function:
        read    jobnr
        del     jobnr
        list

    options:
        -h, --host        * <host name> of FTP host (IBM FTP server)
        -u, --user        * <userid>
        -p, --pwd         * <password>  password for login to FTP server
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

    1. read Job Spool files to local file JOB1234.X.txt
        python jesjob.py --read --jobid JOB1234 --user hugo --pwd secret

    2. set configuration user, password and default editor
        python jesjob.py --config --user hugo --pwd secret --xedit c:/prog/xedit.exe

    3. list jobs in spool
        python jesjob.py --list --jobid MM*

    4. submit job and get result
         parmameter to
        python jesjob.py --subget uid.jobs(adarep)

    A configuration file can be set up with the most common parameters in use -
    e.g. user, host and password (pwd). Then these do not have to be typed
    on each jesjob execution. The password is encrypted so that it is not
    plainly readable on the command line. See example 2.

"""
from __future__ import print_function          # PY3

__date__='$Date$'

def usage():
    print(__doc__)


def getlines(ftp, filename, outfile=None):
    # fetch a text file
    if outfile is None:
        f = sys.stdout
    else:
        # avoid encoding error as some codepoints do not exist in win CP1252
        f = open(outfile, 'w', encoding='latin1')
    # use a lambda to add newlines to the lines read from the server
    ftp.retrlines("RETR " + filename, lambda s, w=f.write: w(s+"\n"))
    if outfile is not None:
        f.close()


if __name__=='__main__':

    from adapya.base.ftptoolz import Ftpzos
    from adapya.base import jconfig

    from ftplib import error_perm
    import sys,os
    import getopt

    if sys.hexversion >= 0x3010100: # PY3
        PY3 = True
        getinput = input
    else:
        PY3 = False
        getinput = raw_input

    # default values
    certfile=None #''
    host=None #''
    user=None #''
    pwd=None #''
    xedit=None #''    # editor executable path read from config
    # xedit=r"C:\Program Files (x86)\KEDITW\KEDITW32.EXE"   # Win7
    # xedit="C:\PROGRA~1\ULTRAE~1\UEDIT32.EXE"

    config=0
    jlist=0
    jread=0
    jdelete=0
    jedit=0

    #   JES Job selection parameters per command
    #   SITE JESJOBNAME=%s JESOWNER=%s JESSTATUS=%s
    jobname =None #''
    jobowner=None #''
    jobstatus=None #''  # ALL, OUTPUT, ACTIVE
    jobid = ''
    job=None    #''  # filename of job
    jdsnmem=''  # dsn and member  e.g. mm.jobs(rep8)
    mem=''      # extracted member name
    STOP=0      # continue if zero
    verbose=0
    test=0      # dry run

    try:
      opts, args = getopt.getopt(sys.argv[1:],
        '?Cdlg:h:p:j:ru:n:o:s:cex:v:',
        ['help','certfile=','delete','list','subget','host=','pwd=','read','user=',
         'jobid=','jobname=','jobowner=','jobstatus=','config','edit','xedit=','verbose='])
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
      elif opt in ('-c', '--config'):
        config=1
      elif opt in ('-C', '--certfile'):
        config=1
      elif opt in ('-d', '--delete'):
        jdelete=1
      elif opt in ('-e', '--edit'):
        jedit=1
      elif opt in ('-x', '--xedit'):   # editor program name
        xedit=arg
      elif opt in ('-g', '--subget'):   # submit and get result
        jdsnmem=arg
        x = jdsnmem[0:-1].split('(')  # split dsn and member
        mem = x[1]
      elif opt in ('-h', '--host'):
          host=arg
      elif opt in ('-j', '--jobid'):
          jobid=arg.upper()
      elif opt in ('-n', '--jobname'):
          jobname=arg
          print('-->jobname', arg)
      elif opt in ('-o', '--jobowner'):
          jobowner=arg
      elif opt in ('-l', '--list'):
        jlist=1
      elif opt in ('-p', '--pwd'):
          pwd=arg
      elif opt in ('-r', '--read'):
          jread=1
      elif opt in ('-u', '--user'):
          user=arg
      elif opt in ('-s', '--jobstatus'):
          jobstatus=arg
      elif opt in ('-v', '--verbose'):
          verbose=int(arg)

    parms = dict(host=host,user=user,pwd=pwd,certfile=certfile,
                 jobname=jobname,jobowner=jobowner,jobstatus=jobstatus,xedit=xedit)

    cfg = jconfig.getparms('ftp', 0,  **parms)

    if config:
        if len(sys.argv)<3:
            print(".ztools jesjob configuration defaults are set as follows:")
            for k, t in cfg.items():
                if k not in ('host', 'user', 'pwd', 'certfile',
                        'jobname', 'jobowner','jobstatus','xedit'):
                    continue # skip any other parameters
                if k == 'pwd':
                    t = '*password*'
                print('%15s: %s' % (k,t))
        else:
            # reset parm in config if set to '' otherwise set or ignore (=None)
            # second parm = 1: print
            jconfig.setparms('ftp', 1, **parms)
            #    host = '' if host=="''" else host if host else None,
        sys.exit()

    host = host or cfg.get('host')
    if not host:
            print("No host name given. Host name needed for ftp connection; terminating!")
            sys.exit(1)
    certfile = certfile or cfg.get('certfile')
    user    = user   or cfg.get('user')
    pwd     = pwd    or cfg.get('pwd')

    jobname   = jobname   or cfg.get('jobname') or ''
    jobowner  = jobowner  or cfg.get('jobowner') or '*'
    jobstatus = jobstatus or cfg.get('jobstatus') or 'OUTPUT'

    xedit   = xedit  or cfg.get('xedit')

    if jobname=='':
        if (jread or jlist) and not jobid:
            jobname=user+'*'
    if jobname:
        jobnamepar = 'JESJOBNAME=%s* ' % jobname
    else:
        jobnamepar = 'JESJOBNAME=* '


    ftpz = Ftpzos(host,user,pwd,verbose=verbose,test=test,certfile=certfile)
    ftp = ftpz.ftp

    print('SITE FILE=JES')
    print(ftp.sendcmd('SITE file=jes'),'\n') # switch to Spool mode

    site='SITE %sJESOWNER=%s JESSTATUS=%s'\
         % (jobnamepar, jobowner, jobstatus)

    if jdsnmem != '':
        print('get %s %s' % (repr(jdsnmem), mem+'.txt'))
        print(ftp.sendcmd('SITE JESJOBNAME=*'),'\n')
        getlines(ftp, repr(jdsnmem), mem+'.txt')

    elif jlist:
        if jobid:
            site='SITE %sJESOWNER=%s JESSTATUS=%s'\
                % (jobnamepar, '*', jobstatus)
            print(site)
            print(ftp.sendcmd(site),'\n')
            print(ftp.retrlines('LIST '+jobid))  # list spool files of 1 job
        else:
            print(site)
            print(ftp.sendcmd(site),'\n')
            print(ftp.retrlines('LIST'))    # list directory contents

    elif jread:
        print(site)
        print(ftp.sendcmd(site),'\n')

        jobx=jobid.split('.')  # in case jobid has spool file number jobid.1
        if len(jobx)==1:       # no jobid number appended
            job=jobid+'.X'
            print('Reading full spool', job)
        else:
            job=jobid

        try:
            jobx0 = jobx[0]
            int(jobx0)          # check if plain job/started task number

            if len(jobx0) > 5:
                job = 'J'+job   # 7 digit id
            else:
                job = 'JOB'+job # 5 digit id

        except ValueError as e:
            pass    # use the given string as job name

        jobfile='%s.txt' % job

        print('Trying spool', job)

        try:
            getlines(ftp, job, jobfile)
        except error_perm as e:
            for msg in e.args:
                print(' '*3,msg)
                if str(msg).find('550 Jobid') >= 0:
                    if job.startswith('JOB'):
                        job = job.replace('JOB','STC')
                    elif job.startswith('STC'):
                        job = job.replace('STC','JOB')
                    elif job.startswith('J'):
                        job = job.replace('J','S')
                    elif job.startswith('S'):
                        job = job.replace('S','J')
                    else:
                        STOP=1
                        raise
                    jobfile='%s.txt' % job
                    print('Retrying with', job)
                    try:
                        getlines(ftp, job, jobfile)
                    except error_perm as e:
                        for msg in e.args:
                            print(' '*3,msg)
                        STOP=1
                        pass
                    break

    elif jdelete:
        print(site)
        print(ftp.sendcmd(site),'\n')

        jobdir = []
        jobs   = []

        try:
            print(ftp.dir(jobdir.append)) # list directory contents
        except error_perm as e:
            print('\n', e.message)
            ftp.quit()     # do not reuse ftp.
            sys.exit()

        """
        with 5 digits job numbers
        JOBNAME  JOBID    OWNER    STATUS CLASS
        MMXSCR   JOB44711 MM       OUTPUT D        RC=0008 13 spool files
        MM8      JOB44683 MM       OUTPUT D        ABEND=000 9 spool files
        MMXSCR   JOB44685 MM       OUTPUT D        ABEND=000 6 spool files

        with 7 digits job numbers
        MMANC8   J0205860 MM       OUTPUT G        RC=0000 8 spool files
        MM8      S0408321 MM       OUTPUT STC      ABEND=000 3 spool files
        """

        for z in jobdir[1:]:            # skip header
            print(z)
            zz = z.split()
            jobs.append(zz[1])

        answer=getinput('Do you want to delete all jobs listed?')
        if answer.upper()=='Y':
            for jj in jobs:
                try:
                    print('Deleting job', jj)
                    print(ftp.delete(jj))        # delete Job
                except error_perm as e:
                    print('\n', e.message)
                    print('\nCould not delete job - skipping command\n')
                    pass

    #ok ftp.retrlines('LIST JOB54008')     # list directory contents
    #ok ftp.retrlines('LIST',jobdir.append) # list directory contents
    #ok getlines(ftp,'JOB54008.1') # sys.stdout
    #ok print(ftp.sendcmd('delete JOB13035')) # delete Job
    #ok print(ftp.sendcmd('SITE file=seq')) # switch to File mode
    #ok ftp.retrlines('LIST')     # list directory contents
    #ftp.close()   # unilateral close

    ftp.quit()     # do not reuse ftp.

    if STOP:
        sys.exit(99)

    if jedit:
        if jread:
            fn=os.getcwd()+'\\'+jobfile
        elif jdsnmem:
            fn=os.getcwd()+'\\'+mem+'.txt'
        else:
            sys.exit()
        print('Editing:', fn)
        s=getinput('Calling editor %s; Press ENTER to continue' % xedit)
        os.execl(xedit,'arg0',fn)
        # passed control to editor
