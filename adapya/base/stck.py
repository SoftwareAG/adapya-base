"""
stck - STCK timestamp format conversion routines
================================================

The module stck.py contains functions for converting timestamp
values in STCK format (used on IBM mainframe computers).


"""
__date__='$Date: 2017-11-03 17:52:37 +0100 (Fri, 03 Nov 2017) $'
__revision__='$Rev: 779 $'

from datetime import datetime, timedelta, tzinfo
import time

sec1970=2208988800  # 2208988800L (w/o leap secs)
secyear=int(365*24*3600)

# needs review after June 28, 2017
leapnow=27      # last updated: Oct 2017
leapseconds = ( # last updated: Oct 2017
    (datetime(1972, 7, 1),  1),
    (datetime(1973, 1, 1),  2),
    (datetime(1974, 1, 1),  3),
    (datetime(1975, 1, 1),  4),
    (datetime(1976, 1, 1),  5),
    (datetime(1977, 1, 1),  6),
    (datetime(1978, 1, 1),  7),
    (datetime(1979, 1, 1),  8),
    (datetime(1980, 1, 1),  9),
    (datetime(1981, 7, 1), 10),
    (datetime(1982, 7, 1), 11),
    (datetime(1983, 7, 1), 12),
    (datetime(1985, 7, 1), 13),
    (datetime(1988, 1, 1), 14),
    (datetime(1990, 1, 1), 15),
    (datetime(1991, 1, 1), 16),
    (datetime(1992, 7, 1), 17),
    (datetime(1993, 7, 1), 18),
    (datetime(1994, 7, 1), 19),
    (datetime(1996, 1, 1), 20),
    (datetime(1997, 7, 1), 21),
    (datetime(1999, 1, 1), 22),
    (datetime(2006, 1, 1), 23),
    (datetime(2009, 1, 1), 24),
    (datetime(2012, 7, 1), 25),
    (datetime(2015, 7, 1), 26),
    (datetime(2017, 1, 1), 27),
    )

def leap4dt(dt):
    """Determine the leap seconds for a given datetime.

    :param dt: datetime value
    :returns:  leap seconds

    >>> leap4dt(datetime(1972, 6,30, 23,59,59))
    0
    >>> leap4dt(datetime(2017, 1,1))
    27

    """
    leapsec=0
    for leapdate, leaps in leapseconds:
        if dt >= leapdate:
            leapsec = leaps
        else:
            break
    return leapsec


def csec(stcksec):
    """returns seconds converted from stck seconds

    >>> csec(0xd69)
    3599.761408
    """
    return stcksec * 1.048576

def cstck(stck):
    ''' returns seconds_since_1970'''
    e=stck * 1.048576
    return e-sec1970

def cstckd(stckd):
    """converts long STCK time into local time and microseconds"""
    a = stckd>>12
    b=a//1000000 # seconds
    c=int(a%1000000) # micro sec
    d=b-sec1970+0.0 # seconds since the epoch 1970
    return (d, c)

def sstck(stck,gmt=0):
    ''' returns ISO date time string from local stck
        if gmt !=0: GMT STCK is assumed
    '''
    if stck==0:
        return ''
    e=stck * 1.048576
    if e >= sec1970:
        if gmt==0:
            return time.strftime('%Y-%m-%d %H:%M:%S',
                         time.localtime(e-sec1970))
        else:
            return time.strftime('%Y-%m-%d %H:%M:%S',
                         time.gmtime(e-sec1970))
    elif e <= secyear:
        return str(timedelta(seconds=int(e)))
    else:
        return 'stck=%s' % hex(stck)

def sstckgmt(stck):
    ''' returns ISO date time string assuming gmt stck value'''
    return sstck(stck,gmt=1)

def sstckd(stckd,gmt=0):
    """converts long STCK time into string
    of local time and microseconds
    if gmt !=0: GMT STCK is assumed
    """
    if stckd == 0:
        return ''
    a = stckd>>12
    b=a//1000000 # seconds
    c=int(a%1000000) # micro sec
    ns=int((stckd&0xfff)*1000//4096) # nsec
    d=b-sec1970+0.0 # seconds since the epoch 1970
    if d >= 0:
        if gmt==0:
            return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(d))+'.%6.6d.%3.3d'%(c,ns)
        else:
            return time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(d))+'.%6.6d.%3.3d'%(c,ns)
    elif b <= secyear:
        if b < 1000:
            return '%d.%6.6d.%3.3d' % (b,c,ns)
        return str(timedelta(microseconds=a))+'.%3.3d'%ns
    else:
        return 'stckd=%s' % hex(stckd)



# some helpers for stimet() function
class Utc(tzinfo):   # helper class for simple UTC timezone display
    def utcoffset(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return timedelta(0)
UTC = Utc()
dt1970 = datetime.fromtimestamp(0,UTC)
fmt = '%Y-%m-%d %H:%M:%S %Z (%z)'

def stimet(timet):
    """Convert time_t value into datetime string, allows negative values.
       Supports datetimes between 1900-01-01 and 9999-12-31

    >>> stimet(-(70*365+17)*24*3600)
    '1900-01-01 00:00:00 UTC (+0000)'

    >>> stimet((8035*365+121)*24*3600+23*3600+3599)
    '9999-12-31 23:59:59 UTC (+0000)'
    """
    dt=dt1970+timedelta(seconds=timet)
    return dt.strftime(fmt)


def stckdnow(leapsec=False):
    return utc2stckd(leapsec=leapsec)

def utc2stckd(dt=datetime.utcnow(),leapsec=False):
    """ convert a datetime to STCK format

        :param dt: datetime value to convert to STCK (detault now)
        :param leapsec: if True add in leap seconds relevant for
            the datetime dt
    """
    from .dtconv import utc2micro,UTC1900

    leap =  10**6 * leap4dt(dt) if leapsec else 0

    microsecs = utc2micro(dt.year,dt.month,dt.day,dt.hour,dt.minute,
             dt.second,dt.microsecond) - utc2micro(*UTC1900) \
             + leap
    return microsecs*2**12



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
