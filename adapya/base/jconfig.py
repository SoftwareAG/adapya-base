"""Manage configuration data in JSON file .ztools
in USERPROFILE/APPDATA/HOME directory
"""
from __future__ import print_function          # PY3
import os
import json
from adapya.base import xtea
from adapya.base.xtea import fromhex, tohex    # PY3

debug = 0
withkeyring = 1  # set to 1 if to use keyring

if withkeyring:
    # check that keyring package is installed
    try:
        # If keyring is installed we try to get/set passwords in a save place.
        # On Windows this is Windows Credential Locker
        # Script keyring [get|set|del] service user
        # e.g. for ftpz set service = host-name
        import keyring
        if debug: print('keyring is installed')
    except:
        withkeyring = 0


#: indicator to request display of the settings in getparms() and setparms()
SHOWCONFIG=1

#: default config file name
CFGFN = '.ztools'

tostr = lambda s: s if type(s) == type('') else s.encode('latin1') # convert from unicode for PY2

# D:\Users\mm or D:\Users\mm\AppData\Roaming
cfgpath = os.environ.get('USERPROFILE','') or \
          os.environ.get('APPDATA','') or \
          os.environ.get('HOME','')
fullname = lambda fn: os.path.abspath(os.path.join(cfgpath,fn))

iv = 'ABCDEFGH'
ckey = '0123456789012345'

def crypt(string):
    global iv, ckey
    return xtea.crypt(ckey,string,iv)

def get(name, cf=CFGFN):
    """ get subject from config JSON file
        :param name: subject dictionary
        :param cf: config file name
    """
    try:
        fp = open(fullname(cf),'r')
        toolsdict = json.load(fp)
        return toolsdict.get(name,'')
        fp.close()
    except IOError as e:
        # [Errno 2] No such file or directory: '.ztools'
        # [Errno 129] No such file or directory: '.ztools'  / USS
        if str(e).startswith('[Errno 2]') or str(e).startswith('[Errno 129]'):
            return None
        else:
            raise

def set(name, value, cf=CFGFN):
    """ set subject in config JSON file
        :param name: subject dictionary
        :param cf: config file name
    """
    try:
        fp = open(fullname(cf),'r')
        toolsdict = json.load(fp)
        fp.close()
    except IOError as e:
        # [Errno 2] No such file or directory: '.ztools'
        # [Errno 129] EDC5129I No such file or directory.: '.ztools'  / USS
        if not str(e).startswith('[Errno 2]') and not str(e).startswith('[Errno 129]'):
            raise
        # file does not exist
        toolsdict={}
    except ValueError as e:
        print( "Ignoring error accessing configuration file: %s" % fullname)
        print( str(e))
        # has no configuration dictionary yet
        toolsdict={}
    fp = open(fullname(cf),'w')
    toolsdict[name]=value
    json.dump(toolsdict,fp)
    fp.close()


def getparms(subject, show, cf=CFGFN, **parms):
    """ get for a subject configuration data unless
    provided by parameter values in parms
    :param subject: select parameters by subject e.g. 'ftp'
    :param parms: parameters that are requested
    :param show:  if > 0: print parameters

    >>> setparms('ftp',False,cf='.test',host='big',password='secret',user='hugo')
    >>> getparms('ftp',False,cf='.test',host='',password='',user='')
    {'host': 'big', 'password': 'secret', 'user': 'hugo'}

    """
    cfg = get(subject) or {}

    if cfg: # non-empty subject
        if parms:
            for k, v in parms.items():
                if not v:
                    # try to fill empty value for k with config
                    vcfg = cfg.get(k,v)
                    if k in ('pwd','password'): # crypted binary data
                        if withkeyring:
                            # keyring support for passwords
                            # try to get user/host from parms as fallback from cfg
                            kuser = parms.get('user',tostr(cfg.get('user','')))
                            khost = parms.get('host',tostr(cfg.get('host','')))
                            if khost and kuser:
                                # used as parameter service,user for keyring
                                vcfg = keyring.get_password(khost,kuser)
                                if debug: print( '\nKeyring: service=%s, user=%s, password=%s' % (khost,kuser,vcfg))
                        elif vcfg:
                            if debug: print(repr(vcfg))
                            vcfg = crypt( fromhex( vcfg ))
                            if debug: print(repr(vcfg))
                    if vcfg:
                        parms[k] = tostr(vcfg)
    if show:
        print( "The following configuration is stored in %r for %r:" %
            (cf, subject))
        for k, t in parms.items():
            if k in ('pwd', 'password') and not debug:
                t='*password*'
            print( '%15s: %s' % (k,t))
    return parms


def setparms(subject, show, cf=CFGFN, **parms):
    """Set configuration parameters for a subject

    :param subject: select parameters by subject e.g. 'ftp'
    :param parms: parameter that should be set
                  If the value of a parameter is None it is ignored.
                  This simplifies setting up call: no dynamic creation
                  of parms dictionary needed.
    :param show:  if True print parameters

    >>> setparms('ftp',True,cf='.test',user='Anna',password='H2o',host='mojave')
    The following configuration is stored in '.test' for 'ftp':
               host: mojave
           password: *password*
               user: Anna

    """
    cfg = get(subject) or {}

    if show:
        print( "\nThe following configuration is stored in %r for %r:" %
            (cf,subject))
    for k, v in sorted(parms.items()):
        if v == None: # skip this parameter
            continue
        if k == 'cf': continue # skip configuration file name
        if k in ('pwd','password'):
            if withkeyring:
                # keyring support for passwords: user and host are keys to store password
                #   if not passed as parameter: try to get it from stored configuration
                kuser = parms.get('user')
                if kuser == None:
                    kuser = tostr(cfg.get('user',''))
                khost = parms.get('host')
                if khost == None:
                    khost = tostr(cfg.get('host',''))
                if debug: print('password %s %s %r' % (khost, kuser, v))
                if khost and kuser: # used as parameter service,user for keyring
                    if v:
                        keyring.set_password(khost,kuser,v)
                        if debug: print('Password set in keyring:  %s %s %s' % (khost, kuser, repr(v) if debug else '*password*'))
                    else: # might be '' but not None
                        try:
                            keyring.delete_password(khost,kuser)
                            if debug: print('Password deleted in keyring: %s %s' % (khost, kuser))
                        except:
                            pass

                    if show: print( '%15s: %s on keyring(service=%s, user=%s)' % (k, v if debug else '*password*', khost,kuser))
                    v = '' # reset in cfg
            else:
                v = tohex(crypt(v))
                if show: print( '%15s: %s' % (k, v if debug else '*password*' ))
        else:
            if show: print( '%15s: %s' % (k,v))
        cfg[k]=v
    set(subject,cfg)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
