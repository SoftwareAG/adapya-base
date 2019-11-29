#! python2
"""ftpz -- sync up members of Z/OS PDS with local directory

The syncronization depends on the modification time stamps
in the file system and the PDS directory

"""
epilog="""
    Examples:

    1. sync-up PDS mm.test.adasrc from current directory and delete
       member that do not exist in source

       ftpz upsync --user xyz --pwd secret --host da3f MM.TEST.ADASRC

    2. update all changed members PDS mm.test.adasrc from current directory

       ftpz upload --user xyz --pwd secret --host da3f MM.TEST.ADASRC

    3. ftpz upsync -t mm.test.adasrc   # dry run without updating

    4. set configuration default values
       ftpz config --user xyz --pwd secret --host da3f # set config
       ftpz config                                     # list config
       ftpz upload MM.TEST.ADASRC                      # use config

    When a configuration file is set up with the most common parameters in use -
    (user, host and password (pwd)) these do not have to be typed
    on each script execution. The password is encrypted so that it is not
    plainly readable on the command line. See example 2.

    5. download
       Download all missing or changed members of PDS mm.test.adasrc to
       current directory

       ftpz download MM.TEST.ADASRC

    6. downsync
       same as 'download' and in addition delete members in directory that
       are missing in PDS

       ftpz downsync MM.TEST.ADASRC

    7. download all changed members for all PDS starting with high-level quailfier (HLQ).
       The current directory is used as the base matching its subdirectories name with
       partitioned datasets HLQ.name. Optionally exclude or include parameters can
       specifiy a list of libraries to exclude or include separated by space

       ftpz download mm.test. --exclude unwanted abandond

       Will process pds mm.test.source and mm.test.macros but
       exclude mm.test.unwanted and mm.test.abandond

    8. download specific missing or changed members 'FOO' and 'BAR' of a PDS as
       foo.s and bar.s in current directory:

       ftpz download mm.test.source --include foo bar

    9. download to use extension .c and special translation table for
       ibm-1047 to ibm-819 with EBCDIC LF = 0x15

       ftpz download mm.c.source -e .c -s sbdataconn=MM.OEMVS31.TCPXLBIN

"""
_TODO="""
      touch with userid and number of lines
      move config to ftptoolz
      Unit test
      Test data: mm.test.adasrc / mm.test.adasrc.copy
              run from D:\adas\adapy\trunk\test\adasrc
"""
__date__='$Date$'

import argparse
from binascii import hexlify, unhexlify
import sys,os
import ftplib
from datetime import datetime
import string
from adapya.base.ftptoolz import crypt, Ftpzos, writedict, invalid_name
from adapya.base.ftptoolz import writejson, readjson
from adapya.base.touch import ftouch
from adapya.base import jconfig

debug = 0

def syncdir(locdir,pds='',include=[],exclude=[],user=''):
    """ Synchronize PDS with local directory 'locdir' or if pds is a
    dataset prefix synchronize all PDS with the prefix

    :param locdir: if parameter is empty start with current directory
    :param pds: partitioned dataset on z/OS. If last letter is '.'
        this is taken as prefix and all pds with that prefix are processed
        e.g.: pds='dev.abc.' works on all libraries starting with 'dev.abc.'
        dev.abc.comp1, dev.abc.comp2 etc.
    :param include:   list of libraries (subdirectories) or members
                      to include
    :param exclude:   list of libraries (subdirectories) or members
                      to exclude
    :param user:      userid to be set when upload/syncing files (touch)

    """
    if not locdir:
        locdir=os.getcwd()

    if pds and pds[-1]=='.':
        dsnprefix=pds[:-1].upper()      # working with prefix and several libraries

        # filter included and excluded libraries
        ##libs=[lib for lib in ftpt.pdsnames("'%s'" % dsnprefix)
        ##        if (lib in include) or (not include and lib not in exclude)]
        libs = []
        for lib in ftpt.pdsnames("'%s'" % dsnprefix, recfm='?B*'):  # select FB/VB/FBA/VBA
            # print('lib = %s' % lib)
            if (lib in include) or (not include and lib not in exclude):
                libs.append(lib)
                # print('libs = %r' % libs)

    else:
        dsnprefix=''
        libs=[]

    if verbose>0:
        print('syncdir(): on root %s vs. dsn = %s / %s on libraries:'%(locdir,dsnprefix,pds))
        print(libs)

    errcount=0

    if test:
        print('\n*** "test" was specified. Any following actions are not performed ***\n')

    for root,dirs,files in os.walk(locdir):    # get files and subdirs of current directory
        if verbose>2:
            print('walk(): root=%s\n\tdirs=%s\n\tfiles=%s' % (root,dirs,files))

        if libs and dirs:    # still libraries there
            for i in range(len(dirs)-1,-1,-1):  # going backwards to avoid index i
                                                #   re-adjusting after del dirs[i]
                # print('current index = %d dir = %s' % (i, dirs[i]))
                if dirs[i] == '.svn':           # skip .svn directories
                    del dirs[i]                 # with topdown=True this
                elif dirs[i].upper() not in libs:   #   removes it from dirs list
                    print('skipping index = %d dir = %s' % (i, dirs[i]))
                    del dirs[i]                 #   reused by walk()

        if verbose>2:
            print('walk(): root=%s\ndirs=%s\nfiles=%s' % (root,dirs,files))

        if dirs and dsnprefix:   # on the upper level of libraries do not process files
            continue

        # remove starting working directory string from root and separating
        #   (back)slash (empty if locdir==root)
        lib=root.replace(locdir,'',1)[1:].upper()

        if dsnprefix:
            if lib not in libs:
                if verbose>2:
                    print('skipping subdirectory' , lib)
                continue    # root has advanced to library level but current lib not wanted
            else:
                pds=('%s.%s'%(dsnprefix,lib)).upper()
                # print('current directory:', root)

        quopds="'%s'" % pds

        memdict={}
        downloaded=[] # list of members downloaded
        try:
            for member in ftpt.members(quopds):
                name = member.name
                if invalid_name(name):
                    continue
                if not dsnprefix:   # full PDS name was specified -> include/excl. on members
                    if include and name not in include:
                        continue
                    elif exclude and name in exclude:
                        continue
                memdict[name]=member
        except ftplib.error_perm as e:
            if e.args[0].endswith('550 No members found.'):
                pass    # empty PDS (partitioned data set)
            else:
                print(' ****** Error getting member list of PDS %s' % (quopds,))
                print(' ****** %s' % e.message)
                raise

        pdict=dict(cfunc=func.capitalize(),pth=os.path.abspath(root),nf=len(files),pds=pds,nm=len(memdict))

        if func in ('download', 'downsync'):
            print('%(cfunc)s files from PDS %(pds)s (%(nm)d) to %(pth)s (%(nf)d)'%pdict)
        elif func in ('upload', 'upsync'):
            print('%(cfunc)s files from %(pth)s (%(nf)d) to PDS %(pds)s (%(nm)d)'%pdict)
        else:
            print('%(cfunc)s files between PDS %(pds)s (%(nm)d) and %(pth)s (%(nf)d)'%pdict)

        if ext != '.s':
            print('\tusing extension %r, selection based last modification times' %(ext,))
        memtimes=[]   # list of tuples (membername,modtime,user,size)
        for file in files:
            ff=os.path.join(root,file)
            fn,fext = os.path.splitext(file)
            if fn.startswith('.') or fext != ext:
                continue    # skip irrelevant files
            if len(fn)>8:
                continue
            if not dsnprefix:   # full PDS name was specified -> include/excl. on files
                if include and fn.upper() not in include:
                    continue
                elif exclude and fn.upper() in exclude:
                    continue
            fmtimes = os.path.getmtime(ff)
            dtfm = datetime.fromtimestamp(fmtimes)      # localtime vs. local PDS times (better be same timezone)
            # dtfm = datetime.utcfromtimestamp(fmtimes) # --utctime
            dtfm = dtfm.replace(second=0,microsecond=0) # pds times have minute precision
            member = memdict.pop(fn.upper(),None)
            if verbose > 3:
                'processing file=%r, member=%r' %(fn+fext,member)
            if member:  # member == filename exists
                # compare member mod.times
                if member.changed:  # member has modification time set in PDS directory
                    dat,tim = member.changed.split() # '2006/12/12 14:35'
                    y,m,d = dat.split('/')
                    hh,mm = tim.split(':')
                    # PDS times are z/OS Server times e.g. Europe/Berlin local
                    dtmm = datetime(int(y),int(m),int(d),int(hh),int(mm)) #,59,999999)

                    if dtmm < dtfm:   # member in pds is older
                        # print('member %r file %r' % (dtmm,dtfm))
                        if func in ('upload','upsync','sync'):
                            print('  U %-8s upload file of %s over %s' % (
                                        member.name, dtfm.strftime('%Y/%m/%d %H:%M'),
                                        member.changed ))
                            if not test:
                                ftpt.storemember(quopds,ff)
                            memtimes.append((fn,dtfm,user,0))
                        else:
                            if verbose>0:
                                print('    %-8s no download older file of %s over %s' %(
                                    member.name, member.changed, dtfm.strftime('%Y/%m/%d %H:%M'),))
                    elif dtmm > dtfm:   # member in pds is younger
                        if func in ('download','downsync','sync'):
                            print('  U %-8s download file of %s over %s' % (
                                        member.name, member.changed, dtfm.strftime('%Y/%m/%d %H:%M'),
                                        ))
                            if not test:
                                try:
                                    ftpt.getfile(member.name,ff)
                                    ftouch(ff, (int(y),int(m),int(d),int(hh),int(mm),0,0,0,-1))
                                    downloaded.append(member)
                                except ftplib.error_perm as e:
                                    print(' ****** Error getting member %s ******' % (member.name,))
                                    if e.args[0].endswith('used exclusively by someone else.'):
                                        print('******', e.args[0], '******')
                                        errcount += 1
                                        pass
                                    else:
                                        raise
                        else:
                            pass
                    else:
                        if verbose>0:
                            print('    %-8s unchanged date %s' %(member.name, member.changed))
                else: # member has no modification time
                    if func in ('upload','upsync'):
                        print('  U %-8s upload file of %s over member w/o date ' % (member.name,
                                        dtfm.strftime('%Y/%m/%d %H:%M:%S')))
                        if not test:
                            ftpt.storemember(quopds,ff)
                        memtimes.append((fn,dtfm,user,0))

                    elif func in ('download','downsync'):
                        if keepsame:
                            if test:
                                print('  U %-8s download file w/o date over %s' % (
                                    member.name, dtfm.strftime('%Y/%m/%d %H:%M') ))
                            else:
                                try:
                                    unchanged = ftpt.getfile(member.name,ff,cmp=True)
                                    if not unchanged:
                                        print('  U %-8s downloaded changed file w/o date over %s' % (
                                            member.name, dtfm.strftime('%Y/%m/%d %H:%M') ))
                                        downloaded.append(member)
                                except ftplib.error_perm as e:
                                    print(' ****** Error getting member %s ******' % (member.name,))
                                    if e.args[0].endswith('used exclusively by someone else.'):
                                        print('******', e.args[0], '******')
                                        errcount += 1
                                        pass
                                    else:
                                        raise
                        else:
                            print('  E %-8s cannot download member w/o date over %s' % (
                                member.name, dtfm.strftime('%Y/%m/%d %H:%M:%S')))

            else:       # member does not exist
                if func in ('upload','upsync','sync'):
                    # upload member
                    if invalid_name(fn):
                        continue
                    print('  N %-8s upload new file of %s' % (fn.upper(),
                                  dtfm.strftime('%Y/%m/%d %H:%M:%S')))
                    if not test:
                        ftpt.storemember(quopds,ff)
                    memtimes.append((fn,dtfm,user,0))
                elif func == 'downsync':
                    print('  - %-8s to be deleted (later with "svndeladd" from SVN) %s '\
                        %(fn.upper(), dtfm.strftime('%Y/%m/%d %H:%M:%S')))

        # remaining members (not in source directory)
        for mname, member in memdict.items():
            if func in ('upsync'):
                print('  - %-8s deleted %s' %(mname, member.changed))
                if not test:
                    ftp.delete(mname)       # ftplib function delete
            elif func in ('download','downsync'):
                print('  N %-8s download missing file of %s'%(mname, member.changed))
                ffile = os.path.join(root,mname.lower()+ext)
                if not test:
                    try:
                        ftpt.getfile(mname,ffile)
                        downloaded.append(mname)
                        if member.changed:  # member has modification time set in PDS directory
                            dat,tim = member.changed.split() # '2006/12/12 14:35'
                            y,m,d = dat.split('/')
                            hh,mm = tim.split(':')
                            ftouch(ffile, (int(y),int(m),int(d),int(hh),int(mm),0,0,0,-1))
                    except ftplib.error_perm as e:
                        print(' ****** Error getting member %s ******' % (member.name,))
                        if ignerr and e.args[0].endswith('used exclusively by someone else.'):
                            print('******', e.args[0], '******')
                            errcount += 1
                            pass
                        else:
                            raise

        if not test:
            if func in ('upload','upsync','sync'):
                ftpt.touchmembers(quopds,memtimes) # submit TOUCH job

            if func in ('download','downsync','sync') and len(downloaded)>0:
                infofile = os.path.join(root,infofilename)
                info=ftpt.memberinfo(quopds)

                if not dsnprefix and func=='download':
                    # in case of mixed directory with multiple source pds do not
                    # delete member info of the other members
                    try:
                        if not os.path.exists(infofile):
                            oldinfo= {} # empty
                        else:
                            oldinfo = readjson(infofile)
                        for m in downloaded:
                            oldinfo[m]=info[m]  # update oldinfo with selected member info
                        writejson(oldinfo,infofile)
                    except:
                        toDelete = []
                        for m in info.keys():
                            # must use copy of keys do not use .iterkeys() cause deleting entries
                            if m not in downloaded:
                                toDelete.append(m)
                        for m in toDelete:
                            del info[m]             # only keep info on downloaded members
                        writejson(info, infofile)   # only write info on downloaded members
                else:
                    # writedict(info, infofile) # the old way
                    writejson(info, infofile)

        if not dsnprefix:
            break # don't go to lower directories

    if errcount:
        print('syncdir() encountered %d errors' % errcount)
        if not ignerr:
            sys.exit(1)

    # --- end of syncdir ---

if __name__=='__main__':

    #infofilename = os.path.join(localdir, '.mirrorinfo')
    infofilename = '.mirrorinfo'

    parser = argparse.ArgumentParser(description=__doc__,epilog=epilog,
                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-k','--keepsame',action='store_true',
        help='On download/sync do not overwrite old file if contents same as new file')
    parser.add_argument('-e','--ext',type=str,default='.s',nargs='?',const='',  # -e
        help='extension to process (default is .s) e.g. -e .c  -e without argument: no extension')
    parser.add_argument('-n','--host',type=str,default='',help='ftp z/OS host name')
    parser.add_argument('-p','--pwd',type=str,default='',help='ftp z/OS user id')
    parser.add_argument('-s','--site',type=str,default='',help='Set ftp server options per quote site')
    parser.add_argument('-u','--user',type=str,default='',help='ftp z/OS user password')
    parser.add_argument('-r','--ignerr',action='store_true',help='ignore ftp member access errors')
    parser.add_argument('-t','--test',action='store_true',help='dry run - list actions only')
    parser.add_argument('-v','--verbose',type=int,default=0,help='verbose output (1 to 3)')
    parser.add_argument('-d','--prefix',type=str,default=None,help='dataset prefix')
    parser.add_argument('-x','--exclude',type=str.upper,nargs='*',default=[],
        help='list of libraries/members to exlude from processing')
    parser.add_argument('-i','--include',type=str.upper,nargs='*',default=[],
        help='list of libraries/members to include in processing')
    parser.add_argument('func',type=str.lower,
        choices=['upsync','upload','download','downsync','config'],
        help="""\nProgram functions:
                - upsync:   upload changed members to partioned dataset (PDS)
                            and delete members not existing in source
                - upload:   upload changed files to partioned datasets (PDS)
                - download: download changed files from partioned datasets (PDS)
                - downsync: download changed members from partioned dataset (PDS)
                            and delete members not existing in PDS
                - config:  display or set configuration
             """
        )
    parser.add_argument('pds',nargs='?',default='',help='Partitioned Dataset name w/o quotes.'\
         ' With ending period: parameter is used as high-level qualifier')

    args = parser.parse_args()

    func, host, user, pwd, test, verbose, pds, ext, pfx, \
        exclude, include, site, ignerr, keepsame = \
        args.func, args.host, args.user, args.pwd, args.test, \
        args.verbose, args.pds, args.ext, args.prefix, \
        args.exclude, args.include, args.site, args.ignerr, \
        args.keepsame

    if ext and not ext.startswith('.'):
        ext='.'+ext


    cfg = jconfig.getparms('ftpz', 0, host=host, user=user, pwd=pwd, pfx=pfx, site=site)

    if func=='config':   # display or change configuration
        if not (host or user or pwd or pfx or site) :
            print(".ztools ftpz configuration defaults are set as follows:")
            for k, t in cfg.items():
                if k not in ('host', 'user', 'pwd', 'pfx', 'site'):
                    continue # skip any other parameters
                if k == 'pwd':
                    t = t if debug else '*password*'
                print('%15s: %s' % (k,t))
        else:
            # reset parm in config if set to '' otherwise set or ignore (=None)
            # second parm = 1: print
            jconfig.setparms('ftpz', 1,
                host = '' if host=="''" else host if host else None,
                user = '' if user=="''" else user if user else None,
                pwd  = '' if pwd=="''" else pwd if pwd else None,
                pfx  = '' if pfx=="''" else pfx if pfx else None,
                site = '' if site=="''" else site if site else None)

        sys.exit()

    # from here on all functions need host/user/pwd parameters
    if not host:
        host=cfg.get('host','')
        if not host:
            print('missing host name')
            sys.exit(1)
    if not pwd:
        # pwd=crypt( unhexlify( cfg.get('pwd','')))
        # print('pwd:%s, crypted:%s' % (pwd, sh['pwd']))
        pwd=cfg.get('pwd','')
        if debug: print('pwd:%s' % pwd)
    if not user:
        user=cfg.get('user','')
    if not site:
        site=cfg.get('site','')
    if pfx == None:
        pfx=cfg.get('pds_prefix',None)

    no_dsnprefix = True if pds and not pds[-1]=='.' else False

    if include:
        print('Include the following libraries:', include)
        if no_dsnprefix:  # members specified
            for m in include:
                if '.' in m:
                    print('Warning: to include, specify member name without extension  ', m)
    if exclude:
        print('Exclude the following libraries:', exclude)
        if no_dsnprefix:  # members specified
            for m in exclude:
                if '.' in m:
                    print('Error: to exclude, specify member name without extension', m)
                    sys.exit(1)


    if pfx:
        pds = "%s.%s" % (pfx,pds) # compose PDS name

    ftpt=Ftpzos(host,user,pwd,verbose=verbose,test=test)
    ftp=ftpt.ftp # get open ftplib.FTP session

    if site:
        print(ftp.sendcmd('SITE %s'%site)) # send special quote command

    syncdir('',pds,include=include,exclude=exclude,user=user)
    sys.exit(0)

