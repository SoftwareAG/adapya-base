#! /usr/bin/env python
"""
touch - set modification time of file(s)
========================================

The program works in 2 ways:

- with option -m:

  Find .mirrorinfo in current directory or subdirectory
  for each file in sub-/directory get its modifcation date
  from .mirrorinfo and set the file to this date

  * This can be used after SVN checkout where the mod. dates
    need to be reset from the checkin to the original date

  * The .mirrorinfo is created by the ftpmirroz.py ftpz.py programs
    a default extension '.s' is expected for the local files
    for comparison with the members listed in .mirrorinfo the extension
    is removed and the filename is upper cased

- with file_name and optional date/time:

  Sets file to current or given date/time

Usage::

    touch.py file_name [yyyy-mm-dd [HH:MM:SS]]

                    Other date/time forms:
                       date:  yyyy/mm/dd
                       time:  HH:MM

    touch.py [-m] [-v] [-x .ext]

    -m mirrorinfo  set dates according to .mirrorinfo
                   Either .mirrorinfo is on current directory or
                   in next lower subdirectory
    -v verbose
    -x extension   default extension is '.s'

"""
from __future__ import print_function          # PY3

import os
import os.path
import stat
import sys
import time
import shutil
import string


def ftouch(file,newtime):
    """Set new **modified** time for given file.
    Supports Unix and Windows (with win32 installed)

    :param file: file to be modified
    :param newtime: new time stamp to be set
    """
    try:
        import pywintypes, win32file
        #wintime = pywintypes.Time(newtime[:6]) # must limit to 6 or SetFileTime won't work
        import win32timezone, datetime
        localTZ=win32timezone.TimeZoneInfo.local()
        wintime = datetime.datetime(newtime,localTZ)   # this fixes time differences when in DST

        f = win32file.CreateFile(file,
                win32file.GENERIC_WRITE, # otherwise creation time not set
                0, None,
                win32file.OPEN_EXISTING, 0, 0)
        win32file.SetFileTime(f, wintime, wintime, wintime)
        # win32file.FlushFileBuffers(f)
        f.Close()
    except:
        it=time.mktime(newtime)
        os.utime(file, (it,it))       # update modification/creation time

def get_mirrorinfo_dict(path):
    """Read mirrorinfo. file containing the PDS directory
    and return it as dictionary. The .mirrorinfo file is
    produced by ftpmirroz.py)

    :param path: path without file name
    :return info: dictionary with PDS directory lines for each member key.
                  If not .mirrorinfo not found return empty dict
    """
    infofilename = os.path.join(path, '.mirrorinfo')
    try:
        text = open(infofilename, 'r').read()
    except IOError as e:
        text = '{}'
    try:
        info = eval(text)
    except (SyntaxError, NameError):
        print( 'Bad mirror info in', repr(infofilename), file=sys.stderr)
        info = {}
    return info

def print_filestatus(file,text):
    st = os.stat(file)

    print(text,file)
    print("last access       ", time.strftime( \
          "%Y-%m-%d %H:%M:%S ", time.localtime(st[stat.ST_ATIME])))
    print("last modification ", time.strftime( \
          "%Y-%m-%d %H:%M:%S", time.localtime(st[stat.ST_MTIME])))
    print("last status change", time.strftime( \
          "%Y-%m-%d %H:%M:%S", time.localtime(st[stat.ST_CTIME])))



if __name__ == '__main__':

    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'mrvx:')
    except getopt.error as e:
        print('getopt error', e.msg)
        print(__doc__)
        sys.exit(2)

    mirrinfo = 0
    verbose = 0
    ext='.s'        # extension default

    filecnt=0
    dircnt=0

    for o, a in opts:
        if o == '-m': mirrinfo=1
        if o == '-v': verbose=1
        if o == '-x': ext=a

    dirs1=[]
    if mirrinfo:
        cwd = os.getcwd()    # get current working directory

        for root, dirs, files in os.walk(cwd,topdown=True):
            for i in range(len(dirs)-1,-1,-1):          # going backwards to avoid index i
                                                        #   re-adjusting after del dirs[i]
                if dirs[i] == '.svn':                   # skip .svn directories
                    del dirs[i]                         # with topdown=True this
                                                        #   removes it from dirs list
                                                        #   reused by walk()
            if verbose:
                print('current directory', root)
            if '.mirrorinfo' in files:
                minfo = get_mirrorinfo_dict(root)
                dircnt+=1
                for file in files:
                    fn,fext = os.path.splitext(file)
                    if fext != ext:
                        continue


                    finfo = minfo.get(fn.upper(),'')
                    # print('    ', file,fn,finfo)
                    if finfo == '':  # file not in PDS directory
                        continue

                    words = finfo.split(None, 8)

                    if len(words) > 4:
                        filecnt+=1
                        mdate=words[3]
                        mtime=words[4]

                        y,m,d = string.split(mdate,'/')
                        hh,mm = string.split(mtime,':')

                        fullname = os.path.join(root,file)
                        if verbose:
                            print('touch', fullname, mdate, mtime)
                        # set creation/modification times to those of original files
                        ftouch(fullname, (int(y),int(m),int(d),int(hh),int(mm),0,0,0,-1))

                fn1 = os.path.join(root,'.mirrorinfo')
                fn2 = fn1+'~'
                shutil.copy2(fn1,fn2)   # copy+copystat .mirrorinfo to .mirrorinfo~
                if verbose:
                    print('Created', fn2)
        print( 'Reset modified time in %d files in %d directories' % (filecnt,dircnt),
            file=sys.stderr)
    else:
        if len(args) < 1 or len(args) > 3:
            print(__doc__)
            sys.exit(2)

        file = os.path.abspath(args[0])


        H=M=S=0     # reset defaults

        if len(args) > 1:
            sdate = args[1]
            sdate=sdate.replace('/','-')
            (y,m,d)=[int(s) for s in sdate.split('-')]

            if len(args) > 2:
                stime = args[2]
                stlist=stime.split(':')
                if len(stlist) > 0:
                    H = int(stlist[0])
                if len(stlist) > 1:
                    M = int(stlist[1])
                if len(stlist) > 2:
                    S = int(stlist[2])

            t=(y,m,d,H,M,S,0,0,-1)  # -1 = local time will adapt to DST/STD depending on season
        else:
          t=time.localtime()

        if verbose:
            print_filestatus(file,'before ftouch:')

        ftouch(file,t)

        if verbose:
            print_filestatus(file,'before ftouch:')


