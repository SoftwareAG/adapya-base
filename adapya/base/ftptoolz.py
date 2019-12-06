"""
ftptoolz module
===============

The Ftpzos class in ftptoolz contains z/OS specific methods for accessing the SPOOL and
datasets.

Jobs
----

* submit()
* listjobs()
* listjob()
* deletejob()
* getjoblines()

PDS dataset
-----------

* memberinfo()
* memberlines()
* members()
* getbinaryfile()
* getfile()
* getlines()
* storemember()
* touchmembers()

ftptoolz modules requires Python V2.7 or higher
"""

from __future__ import print_function          # PY3

import binascii
import datetime, time
import filecmp   # cmp() to compare file contents
import ftplib    # from   ftplib   import error_perm
import json
import sys
import os
from collections import namedtuple
from fnmatch import fnmatchcase
if sys.hexversion > 0x03010100:
    PY3=True
    from _io import StringIO # _io implemented in C code
    from io import BytesIO
else:
    PY3=False
    #from cStringIO import StringIO
    from StringIO import StringIO

from adapya.base import xtea

iv = 'ABCDEFGH'
ckey = '0123456789012345'

lnr=0

def crypt(string):
    global iv, ckey
    return xtea.crypt(ckey,string,iv)

def invalid_name(n):
    for i in '-_%':
        if i in n:
            print("\  Ftp cannot handle name %s with characters '-', '%%' or '_': skipping member" % n)
            return True
    return False

Member = namedtuple('Member','name changed size userid')
""" The namedtuple Member describes the member information in a directory listing
    of a partitioned dataset (PDS).
"""

Jobstatus = namedtuple('Jobstatus','jobname jobid owner status cl cc numspool cputime elapsed stepname procname')
""" The namedtuple Jobstatus describes the jobstatus in z/OS as returned from ftp

    >>> Jobstatus('MMP8','JOB23114','ACF2STC','OUTPUT','K','0000',5)
    >>>                                                 or 'A000' if abend
"""

Spoolfile = namedtuple('Spoolfile','id stepname procstep cl ddname numbytes')
""" The namedtuple Spoolfile describes the a JES spool file in z/OS as returned from ftp

    >>> Spoolfile(1,'JES2','STEP1','X','JESJCL',7362)
"""

Dataset = namedtuple('Dataset','volume unit referred extents used recfm lrecl blksize dsorg dsname')
""" The namedtuple Dataset describes the information obtained from the z/OS ftp directory listing

    >>> Dataset('VSM033','3390','20120215',1,10,'U',6447,6447,'PO','ABC.LOAD')

Example directories::

    ARCIVE Not Direct Access Device                         VLOG.G0001V00
    Dataset('ARCIVE','','',1,10,'',0,0,'','VLOG.G0001V00')
                                                       GDG  NEW.VLOG
    VSM002 3390   2012/09/12  1   15  VB   27994 27998  PS  NEW.VLOG.G0115V00
    VSM123 3390   **NONE**    1   45  ?        0     0 NONE NEW.VLOG.G0120V00
                                                       VSAM MOON.DDIR
    VSM007 3390                                        VSAM MOON.DDIR.D

"""

touchtemplate_sample="""
When writing text files to members of a partitioned dataset
z/OS FTP usually setting the member creation date to the
time of the FTP.

If the modification time of the original text file is to
be set in the member, it is possible to configure a TOUCH job
that is submitted to the mainframe that corrects the
dates for the processed members in the PDS.

Note: the template has one variable for DSN that is replaced

The template for such a job looks like the folling - adaptions
for job card and steplib library are required:

//MMTOUCH  JOB  MM,CLASS=K,MSGCLASS=X
//*
//         EXEC  PGM=TOUCH,REGION=0M
//STEPLIB  DD DISP=SHR,DSN=MM.UTIL.LOAD
//SYSPRINT DD SYSOUT=X
//PDS      DD DISP=SHR,DSN=%s
//SYSIN    DD *
"""

class DatasetsPDSspecifiedError(Exception):
    pass

# class Ftpzos(ftplib.FTP):
class Ftpzos():
    """wraps ftplib.FTP with specific z/OS functions like
    submitting jobs and reading JES spool

    >>> from tools.ftptoolz import Ftpzos
    >>> ftp = Ftpzos('host','user','password',verbose=2)

    """
    def __init__(self,host,user,passwd,verbose=0,test=0):
        self.verbose=verbose
        self.test=test                         # do not perform change actions
        self.ftp = ftplib.FTP('')
        if verbose>1:
            self.ftp.set_debuglevel(1)         # shows commands and responses
        if verbose:
            print(self.ftp.connect(host))      # connect to host, default port
            print(self.ftp.login(user, passwd))
            print(self.ftp.getwelcome())
        else:
            self.ftp.connect(host)             # connect to host, default port
            self.ftp.login(user, passwd)
            self.ftp.getwelcome()


    def deletejob(self, jobid):
        """Delete Job identified by jobid

        :param jobid: e.g. 'JOB12345'
        """
        self.ftp.sendcmd('SITE file=jes') # switch to Spool mode
        delresp = self.ftp.delete(jobid)
        self.ftp.sendcmd('SITE file=seq') # switch to File mode
        print('deletejob(%s) returned', delresp)


    def getjob(self, jobid, outfile=None):
        """Copies job output to outfile

          :param jobid: JOBID.X for complete spool output or
                           JOBID.n for individual spool files
                           e.g. JOB12345.X or JOB12345.1

          :param outfile: optional output file to receive contents

          :returns filename: file name of output file

        """
        self.ftp.sendcmd('SITE file=jes') # switch to Spool mode

        jobid=jobid.upper()

        jobx=jobid.split('.')  # in case jobid has spool file number jobid.1
        if len(jobx)==1:               # no jobid number appended
            job=jobid+'.X'
            print('Reading full spool', job)
        else:
            job=jobid

        if not (job.startswith('JOB') or job.startswith('STC')):
            job = 'JOB'+job     # append JOB to try

        if not outfile:
            jobfile='%s.txt' % job
        else:
            jobfile=outfile

        print('Trying spool', job)

        try:
            self.getfile(job, jobfile)
        except ftplib.error_perm as e:
            for msg in e.args:
                print(' '*3,msg)
                if str(msg).find('550 Jobid') >= 0:
                    if job.startswith('JOB'):
                        job = job.replace('JOB','STC')
                    elif job.startswith('STC'):
                        job = job.replace('STC','JOB')
                    else:
                        raise
                    if not outfile:
                        jobfile='%s.txt' % job
                    print('Retrying with', job)
                    try:
                        self.getfile(job, jobfile)
                    except ftplib.error_perm as e:
                        for msg in e.args:
                            print(' '*3, msg)
                        raise

        self.ftp.sendcmd('SITE file=seq') # switch to File mode

        return jobfile # file name of retrieved spool output


    def getjoblines(self, filename, outfile=None):
        """Generator function if no outfile specified
           yields a line

          :param filename: JOBID.X for complete spool output or
                           JOBID.n for individual spool files
                           e.g. JOB12345.X or JOB12345.1

          :param outfile: optional output file to receive contents
        """
        self.ftp.sendcmd('SITE file=jes') # switch to Spool mode

        # fetch a text file
        if outfile is None:
            lines=[]
            self.ftp.retrlines("RETR " + filename, lines.append)
            for line in lines:
                yield line
        else:
            f = open(outfile, 'w')
            # use a lambda to add newlines to the lines read from the server
            self.ftp.retrlines("RETR " + filename, lambda s, w=f.write: w(s+"\n"))
            f.close()

        self.ftp.sendcmd('SITE file=seq') # switch to File mode


    def datasets(self, dsnprefix):
        """generator function yields catalog information for each dataset
        found under prefix returning a Dataset() tuple

        :param dsnprefix: read file or pds member
        """
        listing=[]
        try:
            self.ftp.cwd(dsnprefix)
        except ftplib.error_perm as e:
            print("Can't chdir to", repr(dsnprefix), ":", repr(e.args))
            raise
        except EOFError:
            raise StopIteration
        try:
            self.ftp.retrlines('LIST', listing.append)
        except ftplib.error_perm as e:
            print("Can't list catalog ", repr(dsnprefix), ":", repr(e.args))
            raise StopIteration
        else:
            if len(listing)==0:
                raise Exception('Empty catalog listing for %s' % dsnprefix)
            if listing[0].startswith(' Name     VV.MM'):
                raise DatasetsPDSspecifiedError('No catalog listing for %s' % dsnprefix)
            if not listing[0].startswith('Volume Unit'):
                # raise Exception('No catalog listing for %s' % dsnprefix)
                raise StopIteration
            del(listing[0])

            for line in listing:
                volume=unit=referred=recfm=dsorg=dsname=''  # default values
                sextents=sused=slrecl=sblksize='0'

                if self.verbose > 2: print('ftp LIST:', line)

                words = line.split()
                if len(words) == 2:
                    dsorg, dsname = words
                elif len(words) == 4: # VSAM with volser
                    volume, unit, dsorg, dsname = words
                elif len(words) == 6 and words[0]=='ARCIVE': # Dataset archived
                   volume = 'ARCIVE'
                   dsname = words[-1]
                elif len(words) == 10:
                        volume,unit,referred,sextents,sused,recfm,slrecl,sblksize,dsorg,dsname=words

                d=Dataset(volume,unit,referred,int(sextents),int(sused),recfm,
                          int(slrecl),int(sblksize),dsorg,dsname)
                yield d

    def pdsnames(self, dsnprefix, recfm='FB'):
        """Iterate over datasets starting with prefix and return only PDS or PDSE datasets

        :param dsnprefix: Dataset prefix - single quoted
        :param recfm:  filter special datasets  (e.g. '?B' selects 'FB' or VB'

        """
        for d in self.datasets(dsnprefix):
            if d.dsorg in ('PO','PO-E'):
                if self.verbose > 2:
                    print('pdsnames:', d)

                if recfm and not fnmatchcase(d.recfm,recfm): # sift out undesired recfm
                    continue
                yield d.dsname

    def getbinaryfile(self, filename, outfile, rdw=0):
        """Copy binary file from ftp to file

           :param filename: read file or pds member

           :param outfile: output file to receive contents

           :param rdw: if true transfers file with variable records being prefixed
                with the RDW word (Int2 record length inclusive, 2 bytes dummy)

        """
        # fetch a text file
        f = open(outfile, 'wb')
        if self.verbose>2:
            print('File %s opened for source file %s'%(outfile,filename))
        # use a lambda to add newlines to the lines read from the server
        if rdw:
            self.ftp.sendcmd('SITE rdw')
            self.ftp.retrbinary("RETR " + filename, f.write)
            self.ftp.sendcmd('SITE nordw')
        else:
            self.ftp.retrbinary("RETR " + filename, f.write)
        f.close()

    def getlines(self, filename):
        """generator function yields a line read from sequential file or
        PDS member specified by filename

        :param filename: read file or pds member
        """
        lines=[]
        self.ftp.retrlines("RETR " + filename, lines.append)
        for line in lines:
            yield line

    def getfile(self, filename, outfile, xlate='', cmp=False):
        """copy text file from ftp to file

        :param filename: read file or pds member
        :param outfile: optional output file to receive contents
        :param xlate:  convert data from EBCDIC to ASCII (option)
            specify name for dataset of the form hlq.<xlate>.TCPXLBIN
        :param cmp: if set to true: compare file gotten with the outfile

        :returns: True if contents of file 'filename' same as file 'outfile'
                  and cmp == True else False
        """
        unchanged = False

        if xlate:
            self.ftp.sendcmd('SITE sbdatacon=%s' % xlate)

        # first try to read file into tempname
        # in order not to destroy an older version of the outfile in case
        # of some problem with the remote file
        dir, fname = os.path.split(outfile)
        tempname = os.path.join(dir, '@' + fname)
        f = open(tempname, 'w')

        if self.verbose>2:
            print('Writing to %s for member %s'%(outfile,filename))
        # use a lambda to add newlines to the lines read from the server

        if 0: # print lines that ftp retrieves (very verbose)
            def w(s):
                global lnr
                lnr += 1
                print(lnr, '%r' % s)
                f.write(s+'\n')
            self.ftp.retrlines("RETR " + filename, w)
        else:
            self.ftp.retrlines("RETR " + filename, lambda s, w=f.write: w(s+"\n"))
        f.close()

        if cmp and os.access(outfile, os.R_OK):
            unchanged = filecmp.cmp(tempname,outfile,shallow=False) # compare contents

        if unchanged: # file contents has not changed
            os.remove(tempname) # delete downloaded file
        else:
            try:
                os.remove(outfile)
            except os.error:
                # filename might not exist
                pass
            os.rename(tempname, outfile)

        return unchanged


    def memberlines(self, dsn):
        """Generator function returns the member lines of a PDS (= directory list)
        :param dsn:  dataset name of a PDS or PDSE
        """
        lines=[]
        self.ftp.cwd(dsn)
        if self.verbose>2:
            pwd = self.ftp.pwd()
            print('Dataset =', repr(pwd))

        self.ftp.retrlines('LIST', lines.append)

        for line in lines:
            yield line

    def members(self, dsn):
        """Generator function returns Member namedtuple
        :param dir:  dataset name of a PDS or PDSE
        """
        lines = self.memberlines(dsn)
        line1 = next(lines)    # read header
        if self.verbose>2:
            print('heading', line1)

        if not line1.startswith(' Name     VV.MM'):
            print('%s is not a PDS/PDSE dataset' % dsn)
            print(line1)
        else:
            mode = '-'  # directory
            for line in lines:
                words = line.split(None, 8)
                if len(words) > 0:
                    name=words[0]
                    if len(words) > 8:
                        changed=words[3]+' '+words[4]
                        userid=words[8].strip()
                        size=int(words[5])
                    else:
                        changed=''
                        userid=''
                        size=9999   # unkown
                    m = Member(name, changed, size, userid)
                    if self.verbose>2:
                        # print(line)
                        # print(name, mdate, mtime, userid, size)
                        print('   ', m)
                    yield m

    def memberinfo(self, dsn):
        """returns plain pds member directory listing for .mirrorinfo"""

        info={}
        lines=[]

        self.ftp.cwd(dsn)
        if self.verbose>2:
            pwd = self.ftp.pwd()
            print('Dataset =', repr(pwd))

        try:
            self.ftp.retrlines('LIST', lines.append)

            line = lines.pop(0)
            if self.verbose>2:
                print('heading', line)
            if not line.startswith(' Name     VV.MM'):
                print('%s is not a PDS/PDSE dataset' % dsn)
                print(line)

        except ftplib.error_perm as e:
            if e.message.endswith('No members found.'):
                print(e.message)
                pass
            else:
                raise

        for line in lines:
            if self.verbose > 2: print('-->', repr(line))
            words = line.split(None, 8)
            if len(words) > 0:
                filename=words[0]
                infostuff=line[:-1]
                info[filename]=infostuff
            else:
                print("Skipping file entry '%s'" % line)
                continue
        return info

    def storemember(self,pds,fname):
        """ upload file to pds member
        :param pds: partitioned dataset name
        :param fname: file in current directory to be uploaded to pds
        """
        try:
            self.ftp.cwd(pds)
            if self.verbose:
                pwd = self.ftp.pwd()
                print('Dataset =', repr(pwd))

            root,basext = os.path.split(fname)
            # get basename and extension (root may be '')
            fn,fext = os.path.splitext(basext)
            f=open(fname,'rb')  # 'b' needed in PY3
            self.ftp.storlines('STOR '+fn, f)
        except ftplib.all_errors as e:
            print('unable to upload %s to %s(%s)' % (fname,pds,fn))
            for msg in e.args:
                print(' '*3, msg)
            raise

    def submit(self,f):
        """submit job

           :param f: opened file object with JCL to submit
                     Must be bytes type data (Latin1) in Python 3

           :return jobid:  job number string e.g. JOB12345
                           or '' of submit failed
        """
        self.ftp.sendcmd('SITE file=jes') # switch to Spool mode
        fresp = self.ftp.storlines('STOR myjob.seq', f)
        self.ftp.sendcmd('SITE file=seq') # switch to File mode
        # '250-It is known to JES as JOB13768\n250 Transfer completed successfully.'
        if fresp.startswith('250-'):
            jobid = fresp.split()[6]
            if jobid.startswith('JOB') and len(jobid)==8:
                return jobid
        return ''

    def submitWait(self,jcl,wait=30):
        """
        :param jcl: dataset or pds(member) containting JCL to submit
        :param wait: wait time in seconds until function is to return
        :return Job: Job object containing information on Job submitted
                     or None

        >>> fz=ftptoolz.Ftpzos('zibm','mm','pw',verbose=2)
        >>> j=fz.submitWait("'mm.jobs(copyy)'")
        >>> x.cc
        'AE37'

        """
        j=None
        f=StringIO()   # py2/3
        for line in self.getlines(jcl):
            f.write(line+'\n')
        f.seek(0)
        self.ftp.sendcmd('SITE file=jes') # switch to Spool mode
        try:
            if PY3:
                # convert to latin1 (iso-8859-1) byte string
                f = BytesIO(f.read().encode('latin1'))
            fresp = self.ftp.storlines('STOR myjob.seq', f)
            if fresp.startswith('250-'):
                jobid = fresp.split()[6]
                if jobid.startswith('JOB') and len(jobid)==8:
                    j=Job(jobid,jcl)

        finally:
            self.ftp.sendcmd('SITE file=seq') # switch to File mode

        if not j:
            return j

        for i in range(wait):
            js,sp = self.listjob(j.jobid)
            j.status=js.status
            j.jobstatus=js
            if js.status=='OUTPUT':
                j.cc=js.cc
                j.spoolfiles=sp
                break
            elif js.status=='ACTIVE':
                j.cputime=js.cputime
                j.elapsed=js.elapsed
            time.sleep(1.)
        return j

    def listjobs(self,jobname='',jobowner='*',jobstat='ALL'): # stat OUTPUT ACTIVE
        self.ftp.sendcmd('SITE file=jes') # switch to Spool mode
        if jobname:
            jnparm = 'JESJOBNAME=%s' % jobname
        else:
            jnparm = 'JESJOBNAME=*'
        site='SITE %s JESOWNER=%s JESSTATUS=%s'%(
                   jnparm, '*', jobstat)
        self.ftp.sendcmd(site)
        print(self.ftp.retrlines('LIST'))  # list directory contents
        self.ftp.sendcmd('SITE file=seq')  # switch to File mode

        # JOBNAME  JOBID    OWNER    STATUS CLASS
        # MM10007  STC22616 ACF2STC  OUTPUT STC      ABEND=000 1 spool files
        # MMP8     JOB23114 ACF2STC  OUTPUT K        RC=0000 5 spool files
        # MMCMP009 JOB13738 MM       OUTPUT K        RC=0000 7 spool files
        # 250 List completed successfully.

        #return jobstatlist

    def listjob(self,jobid,jobowner='*',jobstat='ALL'): # stat ALL OUTPUT ACTIVE
        """List specific job given by jobid
        :param jobid: job id e.g. 'JOB12345'
        :param jobowner: job owner
        :param jobstat: job status: one of ALL, OUTPUT or ACTIVE
        :returns: jobstatus namedtuple and spoolfiles namedtuples
        """
        self.ftp.sendcmd('SITE file=jes') # switch to Spool mode
        site='SITE JESJOBNAME=* JESOWNER=* JESSTATUS=%s' % jobstat
        print(site)
        self.ftp.sendcmd(site)
        jl=[]
        self.ftp.retrlines('LIST '+jobid, jl.append)  # list spool files of 1 job
        self.ftp.sendcmd('SITE file=seq')  # switch to File mode

        #JOBNAME  JOBID    OWNER    STATUS CLASS
        #MMP8     JOB23114 ACF2STC  OUTPUT K        RC=0000
        #--------
        #         ID  STEPNAME PROCSTEP C DDNAME   BYTE-COUNT
        #         001 JES2              X JESMSGLG      1169
        #         002 JES2              X JESJCL        3380
        #         003 JES2              X JESYSMSG      3911
        #         004 RES      A        X DDDRUCK        756
        #         005 RES      A        X DDPRINT       3053
        #5 spool files

        #JOBNAME  JOBID    OWNER    STATUS CLASS
        #MM8      STC40321 ACF2STC  ACTIVE STC
        #--------
        #         STEPNAME ++++++++ PROCNAME     MM8
        #         CPUTIME     0.000 ELAPSED TIME 158321.355

        if self.verbose:
            for j in jl:
                print('retrlines:%s' % j)

        jobstatus=None

        if len(jl)<2 or not jl[0].startswith('JOBNAME'):
            return None,[]

        # get jobstatus
        js = jl[1].split()  # job line
        ns = 0 # number of spool files
        cc = '' # condition code
        cpu=elapsed=0.0
        step=''
        proc=''
        if len(js) > 5:   # condition code set (and may be spools files)
            tc = js[5].split('=')
            if tc[0] == 'ABEND':    # condition code 'AFFA' or '0000'
                cc='A'+tc[1] # A000
            else:
                cc=tc[1] # A000
            # get number of spool files
            spl = jl[-1]
            if spl.rstrip().endswith('spool files'):
                spl.split()
                ns=int(spl[0])

        #           Jobstatus('MMP8','JOB23114','ACF2STC','OUTPUT','K','0000',5,0,0,'','')
        jobstatus = Jobstatus(js[0],js[1],js[2],js[3],js[4],cc,ns,cpu,elapsed,step,proc)

        if not len(jl)>4:
            return jobstatus,[]

        if not jl[-1].rstrip().endswith('spool files'):
            if jobstatus.status=='ACTIVE':
                stepproc = jl[3].split()
                cpuelap  = jl[4].split()
                if len(stepproc) == 4:
                    _, step, _, proc = stepproc
                if len(cpuelap) == 5:
                    _, cpu, _,_, elapsed = cpuelap
                jobstatus._replace(cputime=float(cpu),elapsed=float(elapsed),stepname=step,procname=proc)
                return jobstatus,[]

        # get spool files
        spoolfiles=[]
        for i in range(ns):
            sline = jl[-1-ns+i]
            sli = sline.split()
            if len(sli) == 6: # procstep could be empty
                ps = sli[2]
            else:
                ps = ''
            nb=int(sli[-1])  # number of bytes

            #    Spoolfile(1,'JES2','STEP1','X','JESJCL',7362)
            sf = Spoolfile(i+1,sli[1],ps,sli[-3],sli[-2],nb)
            spoolfiles.append(sf)
        return jobstatus,spoolfiles

    def touchmembers(self, pds, membertimes, touchtemplate):
        """Submit TOUCH job to set modification times in members of a
           partitioned dataset.

        :param pds: partitioned dataset name
        :param membertimes: list of (membername, modtime, uid, size) tuples
                            modtime is of datetime type or
                            of string 'yyyymmdd.HHMMSS'
        :param touchtemplate: Touch template job skeleton
                              (see touchtemplate_sample for further
                              details
        """
        if len(membertimes)==0:
            return
        f=StringIO()   # py2/3
        f.write(touchtemplate % pds.upper().strip())

        for m, t, u, s in membertimes:
            # if touchuid/touchdate given as parameter asmdate will only count lines
            if self.verbose:
                print(m, t, u)
            if t:
                if isinstance(t,datetime.datetime):
                    ttime = t.strftime('%Y%m%d.%H%M%S')
                else:
                    ttime = t   # 'yyyymmdd.HHMMSS'
                f.write('SET DATE=%s\n' % ttime)
            if u:
                f.write('SET USER=%s\n' % u.upper())
            if s:
                f.write('SET LINES=%d\n' % s)
            f.write(m.upper()+'\n')

        f.write('//\n')  # end of job
        f.seek(0)   # rewind
        if self.test:
            print('\nThe following generated TOUCH job is not submitted in test mode:)')
            for line in f:
                print(line[:-1])
        else:
            if PY3:
                # convert to latin1 (iso-8859-1) byte string
                f = BytesIO(f.read().encode('latin1'))
            self.ftp.sendcmd('SITE file=jes') # switch to Spool mode
            self.ftp.storlines('STOR touch.seq', f)
            self.ftp.sendcmd('SITE file=seq') # switch to File mode

class Job(object):
    """ stores the JES job information
    """
    def __init__(self,jobid,jcl):
        self.jobid=jobid
        self.status=''
        self.cc=''          # condition code if in status=OUTPUT
        self.jcl=jcl
        self.jobstatus=None
        self.spoolfiles=None

def getasmdate(line):
    """ find execution date in a line of an assembly or binder listing
        :param line:
        :returns date: date is a string of format YYYYMMDD.hhmm00
    """
    dt = '' # no date yet
    pos = line.find('HLASM')
    if pos > -1:
        words = line[pos:].split()
        if len(words)<4:
            print('cannot find HLASM date:',member, line)
        else:
            dats, tims = words[2:4]
            dats = dats.replace('/','')
            tims = tims.replace('.','')
            dt='%s.%s00' % (dats,tims)
    else:
        pos = line.find('BINDER')
        if pos > -1:
            words = line[pos:].split()
            if len(words)<6:
                print('cannot find BINDER date:',member, line)
            else:
                tims,dayn,month,day, year = words[1:]   #BINDER     23:26:41 MONDAY OCTOBER 30, 2006
                mon = MONTHDICT[month]
                day = day.replace(',','')   # chop comma
                day = '%02d'%(int(day))     # 2 digit string
                dats = year+mon+day
                tims = tims.replace(':','')
                dt='%s.%s' % (dats,tims)
    return dt


def writedict(dict, filename):
    """Write a dictionary to a file in a way that can be read back using
       rval() but is still somewhat readable (i.e. not a single long line).
       Also creates a backup file.
    """
    dir, fname = os.path.split(filename)
    tempname = os.path.join(dir, '@' + fname)
    backup = os.path.join(dir, fname + '~')
    try:
        os.unlink(backup)   # delete backup
    except os.error:
        pass
    fp = open(tempname, 'w')
    fp.write('{\n')
    for key, value in dict.items():
        fp.write('%r: %r,\n' % (key, value))
    fp.write('}\n')
    fp.close()
    try:
        os.rename(filename, backup)
    except os.error:
        pass
    os.rename(tempname, filename)

def readjson(filename):
    # return a dictionary from a json file
    with open(filename, 'r') as fp:
        # make sure old single quotes and comma after last item are removed
        jstr = fp.read().replace("'",'"').replace('",\n}','"\n}')
    return json.loads(jstr)

def writejson(dict, filename):
    """Write a dict as json file"""
    dir, fname = os.path.split(filename)
    tempname = os.path.join(dir, '@' + fname)
    backup = os.path.join(dir, fname + '~')
    try:
        os.unlink(backup)
    except os.error:
        pass
    with open(tempname, 'w') as fp:
        # write dict as json file
        json.dump(dict,fp,indent=0,separators=(',', ':\t'))
    try:
        os.rename(filename, backup)
    except os.error:
        pass
    os.rename(tempname, filename)

