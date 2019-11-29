"""
dtconv - Date and Time conversion functions
===========================================

The module adapya.base.dtconv contains various routines to convert
datetime values between various formats.

For Gregorian to Julian date conversions and vice versa see

    http://en.wikipedia.org/wiki/Julian_day#Calculation

"""
from __future__ import print_function          # PY3

import time                     # for clock_time()
from datetime import datetime

# 0001-01-01 in Julian days is actually 1721425.5
# because the Julian calendar started at noon. For convenience of
# calculation we start 12 hours earlier at midnight:
RATADIE = 1721426
DAYSECS = 86400                 # seconds in a day
SECS1970 = 719162 * DAYSECS     # seconds since epoch 0001-01-01 to 1970-01-01

UTC1900=(1900,1,1,0,0,0,0)
UTC1970=(1970,1,1,0,0,0,0)
UTC1582=(1582,1,1,0,0,0,0)
UTCMAX=(9999,12,31,23,59,59,999999)
UTCMIN=(1,1,1,0,0,0,0)
UTC2008SAMPLE=(2008,12,31,13,20,59,123456)
MIC1970=62135596800000000       # microseconds since 0001-01-01 00:00:00.000000

class InvalidDateException(Exception): pass

def checkdate(year,month,day):
    """ Check Gregorian date given as year, month, day

    :raises InvalidDateException: if invalid input values are given
            otherwise returns silently

    Invalid date raises exception:

    >>> checkdate(2008,12,32)   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    InvalidDateException: day 32 not in range 1..31

    Valid dates go trough quiet:

    >>> checkdate(2008,12,31)

    """

    monthdays=(31,28,31,30,31,30,31,31,30,31,30,31)

    if not (1 <= year <= 9999):
        raise InvalidDateException('year %d not in range 1..9999' % year )

    if not (1 <= month <= 12):
        raise InvalidDateException('month %d not in range 1..12' % month )

    maxday = monthdays[month-1]
    if month == 2 and (
          # leapyear divisible by 4 but not by 100 unless by 400
          (year%400 == 0) or (year%4 == 0) and (year%100 != 0)):
        maxday+=1
    if not (1 <= day <= maxday):
        raise InvalidDateException('day %d not in range 1..%d' % (day,maxday) )


def jul2jdn(year,month,day):
    """Calculate Julian day number from julian date

    - Earliest supported date is March 1, -4800
    - 1 BC is year 0, 2 BC is -1 etc. (astronomical year numbering)
    - Julian year starts at 1. March
    """

    if year < -4800:
        raise InvalidDateException('year %d outside range (-4800,9999)' % (year,) )
    if year == -4800 and month < 3:
        raise InvalidDateException('month %d outside range (3,12) for year %d' % (month,year) )

    a = (14-month)//12   # Jan/Feb: a=1 else a=0
    y = year + 4800 - a  # astronomical year numbering
    m = month + 12*a - 3 # Mar=0, ... Feb=11

    # 153 days in each 5 month cycle starting May
    jdn = day + (153*m+2)//5 + 365*y + y//4 - 32083
    return jdn

def greg2jdn(year,month,day):
    """Calculate the Julian day number for a proleptic gregorian date:

        November 24, 4714 BC  is Julian day 0 at noon

    """
    a = (14-month)//12
    y = year + 4800 - a  # astronomical year numbering
    m = month + 12*a - 3

    jdn = day + (153*m+2)//5 + 365*y + y//4 - y//100 + y//400 - 32045
    return jdn


def gx2utc(halfhours, microsecs):
    """Convert intermediate timestamp of two 32 bit integers to utc form:

       year,month,day,hour,minute,second,microsecond

    :param halfhours: number of halfhours since the epoch 0000-01-02
    :param microsecs: number of microseconds within half hour

    >>> gx2utc(0,0)                     # 0000-01-02 00:00:00.000000
    (0, 1, 2, 0, 0, 0, 0)

    >>> gx2utc(175316351,1799999999)    # 9999-12-31 23:59:59.999999
    (9999, 12, 31, 23, 59, 59, 999999)

    >>> gx2utc(34537296,0)              # 1970-01-01 00:00:00.000000
    (1970, 1, 1, 0, 0, 0, 0)

    >>> gx2utc(35221034,1259123456)     # UTC2008SAMPLE
    (2008, 12, 31, 13, 20, 59, 123456)

    """
    y,m,d,h,i,s = sec2utc(halfhours*30*60 + microsecs//10**6 - 365*DAYSECS)
    return y,m,d,h,i,s, microsecs%10**6


def jdn2greg( jdn ):
    """Calculate gregorian year, month, day from julian day number.

    astronomical year numbering year 0 is 1 B.C., -1 is 2 B.C. etc.

    Even though the first day in the Julian calendar correctly starts
    at noon rather than on midnight here we assume it to start
    at midnight (12 hours earlier)

    """
    j = jdn + 32044

    b = (4*j+3)//146097
    c = j - (b*146097)//4

    d = (4*c+3)//1461
    e = c - (1461*d)//4
    m = (5*e+2)//153

    day   = e - (153*m+2)//5 + 1
    month = m + 3 - 12*(m//10)
    year  = b*100 + d - 4800 + m//10

    return year,month,day


def jdn2jul( jdn ):
    """Calculate julian year, month, day from julian day number
    """
    b = 0
    c = jdn + 32082

    d = (4*c+3)//1461
    e = c - (1461*d)//4
    m = (5*e+2)//153

    day   = e - (153*m+2)//5 + 1
    month = m + 3 - 12*(m//10)
    year  = b*100 + d - 4800 + m//10

    return year,month,day


def micro2nattime(mic):
    """Convert microseconds since 0001-01-01
    to NATTIME Value in 10th of second precision
    """
    return  mic//10**5 + 365*DAYSECS*10


def micro2utc(microsecs):
    """Convert seconds since epoch value to list composed of::

       year,month,day,hour,minute,second,microsecond

    :param microsec: number of microseconds since the epoch 0001-01-01

    >>> micro2utc(0)                    # 0001-01-01 00:00:00.000000
    (1, 1, 1, 0, 0, 0, 0)

    >>> micro2utc(315537897599999999)  # 9999-12-31 23:59:59.999999
    (9999, 12, 31, 23, 59, 59, 999999)

    >>> micro2utc(62135596800000000)   # 1970-01-01 00:00:00.000000
    (1970, 1, 1, 0, 0, 0, 0)

    >>> micro2utc(63366326459123456)   # UTC2008SAMPLE
    (2008, 12, 31, 13, 20, 59, 123456)

    """
    microsec = int(microsecs) % 10**6
    i = int(microsecs)//10**6
    second = i % 60
    i //= 60
    minute = i % 60
    i //= 60
    hour = i % 24
    i //= 24
    year, month, day = jdn2greg(i + RATADIE)

    return int(year),int(month),int(day),int(hour), \
            int(minute),int(second),int(microsec)


def nattime2utc(nt):
    """ convert NATTIME Value in 10th of second precision to
        DATETIME value
    """
    y,m,d,h,i,s = sec2utc(nt//10 - 365*DAYSECS)
    return y,m,d,h,i,s, nt%10 * 10**5

def nattime2micro(nt):
    """ convert NATTIME Value in 10th of second precision to
        microseconds since 1.1.1
    """
    return nt*10**5 - 365*DAYSECS*10**6

def sec2utc(seconds):
    """Convert seconds since epoch value to tuple composed of

        year,month,day,hour,minute,second

    :param seconds: number of seconds since the epoch 0001-01-01
                    if a float value is given:
                    fraction of seconds yield microseconds
    """
    microsecs = int(seconds*10**6)
    year,month,day,hour,minute,second,microsec = micro2utc(microsecs)

    if microsec !=0:
        second += float(microsec)/10**6

    return year,month,day,hour,minute,second

def sec2interval(seconds):
    """Convert seconds to tuple of day, hour, minute and second

    :param seconds: integer
    :returns: tuple day, hour, minute, second

    """
    i = int(seconds)
    second = i % 60
    i //= 60
    minute = i % 60
    i //= 60
    hour = i % 24
    i //= 24
    return i, hour, minute, second

def intervalstr(i):
    days, hours, minutes, seconds = sec2interval(i)

    days = '%dd' % (days) if days else ''
    hours = '%dh' % (hours) if hours else ''
    minutes = '%dm' % (minutes) if minutes else ''
    seconds = '%ds' % (seconds) if seconds else ''

    if days or hours or minutes or seconds:
        # compose nonempty strings with blanks in between
        return ' '.join([x for x in (days,hours,minutes,seconds) if x])
    else:
        return '0s'

def usecintervalstr(u):
    s = int(u//10**6)
    usec = u - s*10**6
    return intervalstr(s) + ' %010.3fus' % usec


stckintervalstr = lambda i: intervalstr(int(i* 1.048576))
stckdintervalstr = lambda i: usecintervalstr(i/4096.)

def unix2utc(seconds):
    """ same as sec2utc() only with epoch 1970-01-01"""
    return sec2utc(seconds+SECS1970)


def utc2gx(*secmsec):
    """Convert list composed of year,month,day,hour,minute,second,microsecond
    to gx format list of two 32 bit integers (halfhours, microsecs) since epoch 0000-01-02

    :param secmsec: list of year,month,day,hour,minute,second,microsecond
    :returns: (halfhours, microsecs) since epoch 0000-01-02
    """
    mics = utc2micro(*secmsec)
    return (mics+365*DAYSECS*10**6)//(1800*10**6), \
           (mics+365*DAYSECS*10**6)%(1800*10**6)


def utc2micro(*secmsec):
    """Convert list composed of year,month,day,hour,minute,second,microsecond

    :param secmsec: list of year,month,day,hour,minute,second,microsecond

    :returns: number of microseconds since the epoch 0001-01-01 00:00:00.000000

    XTIMESTAMP(epoch 0001)

    >>> utc2micro(*UTCMIN)           # 0001-01-01 00:00:00.000000
    0
    >>> '%d' % utc2micro(*UTCMAX)    # 9999-12-31 23:59:59.999999
    '315537897599999999'
    >>> '%d' % utc2micro(*UTC1970)   # 1970-01-01 00:00:00.000000
    '62135596800000000'
    >>> '%d' % utc2micro(*UTC2008SAMPLE)    # 2008-12-31 13:20:59.123456
    '63366326459123456'

    XTIMESTAMP(epoch 1970)

    >>> '%d' % (utc2micro(*UTCMIN)-utc2micro(*UTC1970))
    '-62135596800000000'
    >>> '%d' % (utc2micro(*UTCMAX)-utc2micro(*UTC1970))
    '253402300799999999'
    >>> '%d' % (utc2micro(*UTC1970)-utc2micro(*UTC1970))
    '0'
    >>> '%d' % (utc2micro(*UTC2008SAMPLE)-utc2micro(*UTC1970))
    '1230729659123456'

    """

    if len(secmsec) < 2:
        raise InvalidDateException(
            'Only provided %d parameters for utc2sec() with %s'
            % (len(secmsec), repr(secmsec))
            )

    microsec = int(secmsec[-1])
    second   = int(secmsec[-2])

    minute=hour=day=month=year=days=0

    if len(secmsec) > 2:
        if not( 0 <= second < 60):
            raise InvalidDateException(
                'Invalid Value for second: %d utc2micro(%s)'
                % ( second, repr(secmsec))
                )
        minute = int(secmsec[-3])
        if len(secmsec) > 3:
            hour = int(secmsec[-4])
            if not( 0 <= minute < 60):
                raise InvalidDateException(
                    'Invalid Value for minute: %d utc2micro(%s)'
                    % (minute, repr(secmsec))
                    )
            if len(secmsec) > 4:
                days = day = int(secmsec[-5])
                if not( 0 <= hour < 60):
                    raise InvalidDateException(
                        'Invalid Value for hour: %d utc2micro(%s)'
                        % (hour, repr(secmsec))
                        )
                if len(secmsec) > 5:
                    month = int(secmsec[-6])
                    if len(secmsec) > 6:
                        year = int(secmsec[-7])

                    if not( 1 <= day <= 31):
                        raise InvalidDateException(
                            'Invalid Value for day: %d utc2micro(%s)'
                            % (day, repr(secmsec))
                            )
                    elif not( 1 <= month <= 12):
                        raise InvalidDateException(
                            'Invalid Value for month: %d utc2micro(%s)'
                            % (month, repr(secmsec))
                            )
                    elif not( 1 <= year <= 9999):
                        raise InvalidDateException(
                            'Invalid Value for year: %d utc2micro(%s)'
                            % (month, repr(secmsec))
                            )

                    days = greg2jdn(year,month,day) - RATADIE
    return microsec + 10**6 * (second + 60 * (minute + 60*hour) + days * DAYSECS)


def utc2nattime(*secmsec):
    """ convert utc timestamp since 0001-01-01
        to NATTIME Value in 10th of second precision
    """
    return  micro2nattime(utc2micro(*secmsec))


def utc2sec(*utc):
    """Convert list composed of year,month,day,hour,minute,second [,microsec]

    :param utc: list of year,month,day,hour,minute,second
    :returns: number of seconds since the epoch 0001-01-01
    """
    utc2=list(utc)
    if len(utc)<7:
        utc2.append(0)

    return int(utc2micro(*utc2)/10**6)


def utc2unix(*utc):
    """ same as sec2utc() only with epoch 1970-01-01"""
    return utc2sec(*utc)-SECS1970


def utc2xts(*secmsec):
    """Convert list composed of year,month,day,hour,minute,second,microsecond
    to XTIMESTAMP (UNIXTIME in microsecond precision)

    :param secmsec: list of year,month,day,hour,minute,second,microsecond
    :returns: number of microseconds since the epoch 1970-01-01 00:00:00.000000
    """
    return utc2micro(*secmsec)-MIC1970


def xts2utc(microseconds):
    """ same as micro2utc() only with epoch 1970-01-01 """
    return micro2utc(microseconds+MIC1970)

#
# --- Adabas datetime specific conversions ---
#
# from DATE
#

def date2datetime(year,month,day):
    return (year,month,day,0,0,0)

def date2timestamp(year,month,day):
    return (year,month,day,0,0,0,0)

def date2natdate(year,month,day):
    """Convert a gregorian date to a natdate integer

    No checking is done for valid dates. Natural
    does not allow dates earlier than 1582-01-01

    >>> date2natdate(1,1,1)
    365
    >>> date2natdate(0,1,1)
    -1
    >>> date2natdate(0,1,2)
    0
    >>> date2natdate(1900,1,1)
    693960
    >>> date2natdate(1582,1,1)
    577813
    >>> date2natdate(1970,1,1)
    719527
    >>> date2natdate(2000,1,1)
    730484
    >>> date2natdate(2008,12,31)
    733771
    >>> date2natdate(9999,12,31)
    3652423
    """
    return greg2jdn(year,month,day)-RATADIE+365


def date2nattime(year,month,day):
    return date2natdate(year,month,day) * DAYSECS * 10

def date2unixtime(year,month,day):
    return utc2unix(date2timestamp(year,month,day))

def date2xtimestamp(year,month,day):
    return utc2xts(date2timestamp(year,month,day))


#
# from datetime
#

def datetime2date(year,month,day,hour,minute,second):
    return year,month,day

def datetime2time(year,month,day,hour,minute,second):
    return hour,minute,second

def datetime2timestamp(year,month,day,hour,minute,second):
    return year,month,day,hour,minute,second,0

def datetime2natdate(year,month,day,hour,minute,second):
    return date2natdate(year,month,day)

def datetime2nattime(year,month,day,hour,minute,second):
    return utc2nattime(year,month,day,hour,minute,second)

def datetime2unixtime(year,month,day,hour,minute,second):
    return utc2unix(year,month,day,hour,minute,second,0)

def datetime2xtimestamp(year,month,day,hour,minute,second):
    return datetime2xtimestamp(year,month,day,hour,minute,second) * 10**6

#
# from timestamp
#

def timestamp2date(y,m,d,h,i,s,x):
    return y,m,d

def timestamp2datetime(y,m,d,h,i,s,x):
    return y,m,d,h,i,s

def timestamp2natdate(y,m,d,h,i,s,x):
    return date2natdate(y,m,d)

def timestamp2nattime(y,m,d,h,i,s,x):
    return utc2nattime(y,m,d,h,i,s,x)

def timestamp2unixtime(y,m,d,h,i,s,x):
    return utc2unix(y,m,d,h,i,s,x)

def timestamp2xtimestamp(y,m,d,h,i,s,x):
    return utc2xts(y,m,d,h,i,s,x)

#
# from natdate
#

def natdate2date(nd):
    return jdn2greg(nd+RATADIE-365)

def natdate2nattime(nd):
    """ convert NATDATE counting days since Jan. 2, 0000 to
        NATTIME Value in 10th of second precision
    """
    return nd*DAYSECS*10


#
# from nattime
#

def nattime2date(nt):
    return natdate2date(nt // (DAYSECS*10))

def nattime2datetime(nt):
    y,m,d,h,i,s,_ = nattime2utc(nt)
    return y,m,d,h,i,s

def nattime2timestamp(nt):
    return nattime2utc(nt)

def nattime2natdate(nt):
    """Convert NATTIME Value in 10th of second precision to
    NATDATE couning days since Jan. 2, 0000
    """
    return nt//(DAYSECS*10)

#
# from xtimestamp
#
def xtimestamp2timestamp(mics):
    """
    >>> xtimestamp2timestamp(0)
    (1970, 1, 1, 0, 0, 0, 0)

    """

    return xts2utc(mics)

#
# simple datetime tuple to string conversions
#
DTF="%Y-%m-%d %H:%M:%S"
DTN="%Y%m%d%H%M%S"

def dt2strf(*dt):
    """
    >>> dt2strf( 2010,4,30, 11, 55, 13)
    '2010-04-30 11:55:13'

    >>> d1=(2010,1,2,11,44,55)
    >>> dt2strf( *d1)
    '2010-01-02 11:44:55'

    """
    d = datetime(*dt)
    return d.strftime(DTF)

def ts2strf(*ts):
    """
    >>> ts2strf( 2010,4,30, 11, 55, 13, 999999)
    '2010-04-30 11:55:13.999999'

    """
    d = datetime(*ts)
    return d.strftime(DTF)+'.%06d'%d.microsecond


def dt2str(*dt):
    """ make a datetime string from a datetime tuple

    >>> dt2str( 2010,4,30, 11,55,13)
    '20100430115513'

    """
    d = datetime(*dt)
    return d.strftime(DTN)

def str2dt(ds):
    """ make a datetime tuple from a datetime string or number

    >>> str2dt( '20160229115513' )
    (2016, 2, 29, 11, 55, 13)
    >>> str2dt( b'20160301235513' )
    (2016, 3, 1, 23, 55, 13)

    """

    if not isinstance(ds, (bytes, bytearray, str)):
        ds=str(ds)   # make it a string if number

    zero = b'0' if isinstance(ds, (bytes,bytearray)) else '0'

    if len(ds) < 14:
        ds = zero*(14-len(ds))+ds

    if len(ds) == 14:                                       # Datetime
        ds = zero*(14-len(ds))+ds
        return int(ds[0:4]), int(ds[4:6]), int(ds[6:8]), \
               int(ds[8:10]), int(ds[10:12]), int(ds[12:14])
    elif len(ds) == 20:                                     # Timestamp
        return int(ds[0:4]), int(ds[4:6]), int(ds[6:8]), \
               int(ds[8:10]), int(ds[10:12]), int(ds[12:14]), \
               int(ds[14:20])


#
# test some functions
#

def testgreg2jdn():
    """Conversion of seconds to gregorian date"""

    samples = (
    # year, month, day, secs
    #
    (   1, 1, 1, 0000000000),
    ( 100, 1, 1, 3124137600),
    ( 100, 3, 1, 3129235200),
    ( 200, 1, 1, 6279811200),
    ( 200, 3, 1, 6284908800),
    ( 300, 1, 1, 9435484800),
    ( 300, 3, 1, 9440582400),
    ( 400, 1, 1, 12591158400),
    ( 400, 3, 1, 12596342400),
    ( 500, 1, 1, 15746918400),
    ( 500, 3, 1, 15752016000),
    ( 600, 1, 1, 18902592000),
    ( 600, 3, 1, 18907689600),
    ( 700, 1, 1, 22058265600),
    ( 700, 3, 1, 22063363200),
    ( 800, 1, 1, 25213939200),
    ( 800, 3, 1, 25219123200),
    ( 900, 1, 1, 28369699200),
    ( 900, 3, 1, 28374796800),
    ( 1000, 1, 1, 31525372800),
    ( 1000, 3, 1, 31530470400),
    ( 1100, 1, 1, 34681046400),
    ( 1100, 3, 1, 34686144000),
    ( 1200, 1, 1, 37836720000),
    ( 1200, 3, 1, 37841904000),
    ( 1300, 1, 1, 40992480000),
    ( 1300, 3, 1, 40997577600),
    ( 1400, 1, 1, 44148153600),
    ( 1400, 3, 1, 44153251200),
    ( 1500, 1, 1, 47303827200),
    ( 1500, 3, 1, 47308924800),
    ( 1582, 1, 1, 49891507200),       # 577448*DAYTICS),
    #
    ( 1600, 1, 1, 50459500800),
    ( 1600, 3, 1, 50464684800),
    ( 1700, 1, 1, 53615260800),
    ( 1700, 3, 1, 53620358400),
    ( 1800, 1, 1, 56770934400),
    ( 1800, 3, 1, 56776032000),
    ( 1900, 1, 1, 59926608000),
    ( 1900, 3, 1, 59931705600),
    ( 1970, 1, 1, 62135596800),       # 719162*DAYTICS
    ( 2000, 1, 1, 63082281600),
    ( 2000, 3, 1, 63087465600),
    ( 2100, 1, 1, 66238041600),
    ( 2100, 3, 1, 66243139200),
    ( 2200, 1, 1, 69393715200),
    ( 2200, 3, 1, 69398812800),
    ( 2300, 1, 1, 72549388800),
    ( 2300, 3, 1, 72554486400),
    ( 2400, 1, 1, 75705062400),
    ( 2400, 3, 1, 75710246400),
    ( 2500, 1, 1, 78860822400),
    ( 2500, 3, 1, 78865920000),
    ( 2600, 1, 1, 82016496000),
    ( 2600, 3, 1, 82021593600),
    ( 2700, 1, 1, 85172169600),
    ( 2700, 3, 1, 85177267200),
    ( 2800, 1, 1, 88327843200),
    ( 2800, 3, 1, 88333027200),
    ( 2900, 1, 1, 91483603200),
    ( 2900, 3, 1, 91488700800),
    ( 3000, 1, 1, 94639276800),
    ( 3000, 3, 1, 94644374400),
    ( 1 , 1, 1, 0),
    ( 1601, 1, 1, 50491123200),
    ( 1899, 12, 31, 59926521600),
    ( 1904, 1, 1, 60052752000),
    ( 1970, 1, 1, 62135596800),
    ( 2001, 1, 1, 63113904000),
    ( 9900, 3, 1, 312387321600),
    ( 9999, 12, 31, 315537811200)
    )

    for y,m,d,secs in samples:
        gy, gm, gd = jdn2greg(secs//DAYSECS + RATADIE)

        gsec = (greg2jdn(y,m,d)-RATADIE) * DAYSECS
        # print   Y  m  d  secs  days          natdate            nattime
        # print(  y, m, d, secs, secs//DAYSECS, secs//DAYSECS+365, (secs+DAYSECS*365)*10 )
        try:
            assert secs == gsec
            assert    y == gy
            assert    m == gm
            assert    d == gd
        except:
            print( "datetime assertion error:", y,m,d,secs, 'vs.', gy,gm,gd,gsec)

#
time0 = 0
clockbase0 = 0

def clock_time(resync=300):
    """:param resync: interval for resyncing with time()
    :returns: high resolution time
    """
    global time0, clockbase0

    clock1 = time.clock()

    if not time0 or (resync and resync < (clock1+clockbase0 - time0)):
        time0 = time.time()

        while 1:                   # until t=time() changes
            clock1 = time.clock()
            t = time.time()
            if t != time0:
                time0, clockbase0 = t, t-clock1
                # print( 'clock_time()', datetime.fromtimestamp(t))
                break

    return clock1+clockbase0

def demo_clock_time():
    # show differences in clock_time to time() when time() changes
    a = []
    t1 = time.time()
    for i in range(100000):
        c,t = clock_time(), time.time()
        if t != t1:
            t1=t
            a.append( (c, t) )
    for c,t  in a:
        print( datetime.fromtimestamp(c), datetime.fromtimestamp(t))


if __name__ == "__main__":
    import doctest
    doctest.testmod()

# $Date: 2017-05-17 20:51:16 +0200 (Wed, 17 May 2017) $
# $Rev: 768 $
#
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
