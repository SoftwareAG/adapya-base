#
# IBM System management Facilities (SMF) record structures
# (only some SMF30 record types)
#

from adapya.base.datamap import Datamap,Bytes,str_str,Int2,Int4,\
    NETWORKBO,String,Packed,str_str,\
    T_NONE,T_HEX,T_STCK,Uint1,Uint2,Uint4,Uint8


percent = lambda i: "%d %%" % i
plural_s = lambda j: '' if j == 1 else 's'
dezi = lambda i: dot1 * i  # dezi(123) returns decimal('12.3')

div256 = lambda i: '%.2f' % (i/256.,)

def dtime100(i):
    "return readable time since midnight 1/100 sec precision"
    hh = i/(100*3600)
    mm = i/(100*60) - hh*60
    ss = i/100 - hh*60*60 - mm*60
    hs = i%100
    return '%02d:%02d:%02d.%02d' % (hh,mm,ss,hs)

def idate(i):
    " Return string from IBM date 0cyyddd "
    if i > 100000:
        return '20%02d.%03d' % ( (i-100000)/1000, i%1000 )
    else:
        return '19%02d.%03d' % (i/1000, i%1000)

def i2dt(idat,itim):
    """Convert industry date time to datetime object

        :param idat: integer IBM industry date 0cyyddd
        :param itim: integer IBM time in 100ths of a second in day
    """
    from datetime import datetime, timedelta
    hh=mm=ss=hs=0

    if idat > 100000:
        yy = 2000 + (idat-100000) // 1000
    else:
        yy = 2000 + idat // 1000
    tdays = timedelta(idat%1000 - 1) # day in year starting with 0

    if itim:
        hh = itim/(100*3600)
        mm = itim/(100*60) - hh*60
        ss = itim/100 - hh*60*60 - mm*60
        hs = itim%100
    return datetime(yy,1,1,hh,mm,ss,hs*10000)+tdays

#
# Standard SMF record header
#
class Smf(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'SMF Record Header',
    Int2('rlen'), # Record length        RDW header
    Uint1('seg'), # Segment control
    Uint1('seg2'), # Segment control 2 (unused)

    Bytes('flg',1,caption='System indicator'), # System indicator flags
    #q Asfxxx   equ    x'80'               subsystem id follows system id
    #q Asfstv   equ    x'40'               subtypes are valid
    #q Asfv4    equ    x'10'               mvs/sp v4 and above
    #q Asfv3    equ    x'08'               mvs/sp v3 and above
    #q Asfv2    equ    x'04'               mvs/sp v2 and above
    #q Asfvs2   equ    x'02'               vs2

    Uint1('rty',caption='SMF record type'),  # SMF record type

    Uint4('tme',ppfunc=dtime100,caption='Record creation time'), # Time since midnight
                                  # when record was moved into smf buffer in 1/100 sec

    Packed('dte',4,ppfunc=idate,caption='Record creation date'), # Date when record was
                                  # moved into smf buffer as 0cyydddf

    String('sid',4,caption='System identifier'), # smfprmxx sid
    # up to here if SMF record withtout subtypes

    String('ssi',4,caption='Subsystem identifier'),
    Uint2('sty',caption='Subtype'), # Subtype  ppfunc=Asbase.assty_str
    byteOrder=NETWORKBO,ebcdic=1,**kw)
SMFWOS = 0x12   # without subtypes
# dmlen = 0x18  # with subtypes

#
# SMF record type 30: Accounting information "Common address space work"
#
class Smf30(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'SMF30 Acccounting Information Record',
    Int2('rlen'), # Record length        RDW header
    Uint1('seg'), # Segment control
    Uint1('seg2'), # Segment control 2 (unused)

    Bytes('flg',1,caption='System indicator'), # System indicator flags
    Uint1('rty',caption='SMF record type'),  # SMF record type

    Uint4('tme',ppfunc=dtime100,caption='Record creation time'), # Time since midnight
                                  # when record was moved into smf buffer in 1/100 sec

    Packed('dte',4,ppfunc=idate,caption='Record creation date'), # Date when record was
                                  # moved into smf buffer as 0cyydddf

    String('sid',4,caption='System identifier'), # smfprmxx sid
    String('ssi',4,caption='Subsystem identifier'),
    Uint2('sty',caption='Subtype'), # Subtype  ppfunc=Asbase.assty_str
    #q Asbasel  equ   *-asbase            length of standard header

    # Self-defining section offset 0x14 w/o RDW
    # Bytes('sds',152,opt=T_NONE,caption='Self defining section'), # too short

    # Subsystem section
    # following offsets number are + 4 because our record is w/o RDW
    Uint4('sof'),  # Offset to section from record start + 4
    Uint2('sln'),  # Length of subsystem section
    Uint2('son'),  # Number of subsystem section(s)

    # Identification section (always present)
    Uint4('iof'),  # Offset to id section from record start + 4
    Uint2('iln'),  # Length of id section
    Uint2('ion'),  # Number of id section(s)

    # I/O activity section
    Uint4('uof'),  # Offset to section from record start + 4
    Uint2('uln'),  # Length of section
    Uint2('uon'),  # Number of sections

    # Completion section
    Uint4('tof'),  # Offset to section from record start + 4
    Uint2('tln'),  # Length of section
    Uint2('ton'),  # Number of sections

    # Processor section
    Uint4('cof'),  # Offset to section from record start + 4
    Uint2('cln'),  # Length of section
    Uint2('con'),  # Number of sections

    # Accouting section
    Uint4('aof'),  # Offset to section from record start + 4
    Uint2('aln'),  # Length of section
    Uint2('aon'),  # Number of sections

    # Storage section
    Uint4('rof'),  # Offset to section from record start + 4
    Uint2('rln'),  # Length of section
    Uint2('ron'),  # Number of sections

    # Performance section
    Uint4('pof'),  # Offset to section from record start + 4
    Uint2('pln'),  # Length of section
    Uint2('pon'),  # Number of sections

    # Operator section
    Uint4('oof'),  # Offset to section from record start + 4
    Uint2('oln'),  # Length of section
    Uint2('oon'),  # Number of sections

    # EXCP section
    Uint4('eof'),  # Offset to section from record start + 4
    Uint2('eln'),  # Length of section
    Uint2('eon'),  # Number of sections

    Uint2('eor'),  # Number of segments in subsequent records (might be invalid)
    Uint2('rvd'),  # reserved
    Uint4('eos'),  # Number of segments in subsequent records (fullword)

    # APPC/MVS section
    Uint4('dro'),  # Offset to section from record start + 4
    Uint2('drl'),  # Length of section
    Uint2('drn'),  # Number of sections

    # APPC/MVS section cumulative
    Uint4('aro'),  # Offset to section from record start + 4
    Uint2('arl'),  # Length of section
    Uint2('arn'),  # Number of sections

    # OpenMVS section
    Uint4('opo'),  # Offset to section from record start + 4
    Uint2('opl'),  # Length of section
    Uint2('opn'),  # Number of sections
    Uint4('opm'),  # Number of sections in subsequent records

    # Usage section
    Uint4('udo'),  # Offset to section from record start + 4
    Uint2('udl'),  # Length of section
    Uint2('uds'),  # Number of sections

    # First ARM section
    Uint4('rmo'),  # Offset to section from record start + 4
    Uint2('rml'),  # Length of section
    Uint2('rmn'),  # Number of sections
    Uint4('rms'),  # Number of sections in subsequent records

    # MultiSystem Enclave Remote System Data section
    Uint4('mof'),  # Offset to section from record start + 4
    Uint2('mln'),  # Length of section
    Uint2('mno'),  # Number of sections
    Uint4('mos'),  # Number of sections in subsequent records

    # Counter Data section
    Uint4('cdo'),  # Offset to section from record start + 4
    Uint2('cdl'),  # Length of section
    Uint2('cdn'),  # Number of sections

    # zEDC usage statistics section
    Uint4('uso'),  # Offset to section from record start + 4
    Uint2('usl'),  # Length of section
    Uint2('usn'),  # Number of sections
    byteOrder=NETWORKBO,ebcdic=1,**kw)

#
#   Smf30pss - Product or Subsystem Section
#

class Smf30pss(Datamap):
  @staticmethod
  def subtyp_str(i):
    return str_str(i, {1:'Job/work unit start', 2:'Interval activity',
      3:'Last interval before step term', 4:'Step total',
      5:'Job/work unit term', 6:'System address space'})

  def __init__(self, **kw):
    Datamap.__init__(self, 'Product or Subsystem Section',
    Uint2('typ',caption='SMF30 sub type',ppfunc=self.subtyp_str),
    String('rs1',2,opt=T_NONE),
    String('rvn',2,caption='Record version number'),
    String('pnm',8,caption='Subsystem product name'),

    String('osl',8,caption='MVS product level'),
    String('syn',8,caption='System name'),
    String('syp',8,caption='Sysplex name'),
    byteOrder=NETWORKBO,ebcdic=1,**kw)

#
#   Smf30id - Job or Session Identification Section
#

class Smf30id(Datamap):
  def __init__(self, **kw):
    Datamap.__init__(self, 'Job/Session Id Section',
    String('jbn',8,caption='Job/session name'), # JMRJOB
    String('pgm',8,caption='Program name'),     # SCTPGMNM '*.DD.' if backward reference
    String('stm',8,caption='Step name'),        # SCTSNAME
    String('uif',8,caption='User id'), # JMRUSEID taken from the common exit parm
    String('jnm',8,caption='JES job id'),  # SSIB

    Uint2('stn',caption='Step number'),         # SCTSNUMB, first step = 1
    String('cls',1,caption='Job class'),        # JCTJCSMF, zero for TSO/started task
    Uint1('jb1',caption='Job/Session Id section flag'),
    Uint2('pgn',caption='Job performance group member'), # OUCBNPG
    Uint2('jpt',caption='JES input priority'),  # JCTJPRTY

    Uint4('ast',ppfunc=dtime100,caption='Device allocation start time'), # TCTAST
    Uint4('pss',ppfunc=dtime100,caption='Problem program start time'),   # TCTPPST
    Uint4('sit',ppfunc=dtime100,caption='Time initiator selected step'), # JCTJMRSS
    Packed('std',4,ppfunc=idate,caption='Date initiator selected step'), # JCTSSD
    Uint4('rst',ppfunc=dtime100,caption='Time reader found job card'), # JMRENTRY
    Packed('rsd',4,ppfunc=idate,caption='Date reader found job card'), # JMREDATE
    Uint4('ret',ppfunc=dtime100,caption='Time reader found end of job'),
    Packed('red',4,ppfunc=idate,caption='Date reader found end of job'),

    String('usr',20,caption='Programmers name'),# ACTPRGNM
    String('grp',8,caption='RACF group id'),    # ACEEGRPN
    String('rud',8,caption='RACF user id'),     # ACEEUSRI
    String('tid',8,caption='RACF terminal id'), # ACEETRMF

    String('tsn',8,caption='Terminal sybolic name'), # TSBTRMID
    String('psn',8,caption='Step name invoking procedure'), # SCTSCLPC, blanks if step not part of expanded procedure
    String('cl8',8,caption='Job class'), # LCTCLASS or JCTJCSMF
    Uint8('iss',opt=T_STCK,caption='Interval start time'), # TCTISS for subtype 2, 3 and 6 records
    Uint8('iet',opt=T_STCK,caption='Interval end time'),   # SMCXINTE for subtype 2, 3 and 6 records

    Uint4('ssn',ppfunc=dtime100,caption='Sub-step number'),# SCTSSNUM
    String('exn',16,caption='OpenMVS program name'),
    Uint2('asi',opt=T_HEX,caption='Address space id'),    # ASCBASID
    String('cor',64,opt=T_NONE,caption='JES job correlator'),  # JMRJOBCORRELATOR

    byteOrder=NETWORKBO,ebcdic=1,**kw)


#
#   Smf30prf - Performance Section
#              (currently only few selected fields :-)
#

class Smf30prf(Datamap):
  def __init__(self, **kw):
    Datamap.__init__(self, 'Performance section',
    Uint2('snf',ppfunc=div256,caption='zIIP normalization factor',pos=0x88),
    # to convert between real zIIP times and normalized zIIP times (=equivalent time on normal CP)
    # multiply zIIP time with snf and divide by 256
    Bytes('prf',0xd8,opt=T_NONE,caption='prf DSECT',pos=0), # todo: define more fields in structure
    byteOrder=NETWORKBO,ebcdic=1,**kw)

#
#   Smf30cas - CPU Accounting Section
#

class Smf30cas(Datamap):
  def __init__(self, **kw):
    Datamap.__init__(self, 'CPU accounting section',

    Uint2('pty',caption='Address space dispatching priority'), # from DPRTY parm on EXEC card or APG value in CVTAPG
    Bytes('tfl1',1,caption='Timer Flag1'),
    Bytes('tfl2',1,caption='Timer Flag2'),
    #o todo flag bits

    Uint4('cpt',ppfunc=dtime100,caption='Step CPU time under TCB'),
    # ASCBEJST OR (ACTJTIME + ASSBASST + RQSVECPT  - TCTEJST)
    # only consumption of GCP not zIIPs,zAAPs, includes enclave time

    Uint4('cps',ppfunc=dtime100,caption='Step CPU time under SRB'), # ASCBSRBT OR (SCTSRBT-TCTSRBT)

    Uint4('icu',ppfunc=dtime100,caption='Initiator CPU time under TCB'), # ASCBEJST+TCTITCB
    # Total working CPU time for initiator under the TCB. It includes values of
    # SMF30ICU_Step_Term (time spent in termination of the previous step) and
    # SMF30ICU_Step_Init (time spent in initialization of the current step)

    Uint4('isb',ppfunc=dtime100,caption='Initiator CPU time under SRB'), # ASCBSRBT+TCTISRB
    # Total working CPU time for the initiator under any SRB. It includes values of
    # SMF30ISB_Step_Term (time spent in termination of the previous step) and
    # SMF30ISB_Step_Init (time spent in initialization of the current step)

    Uint4('jvu',ppfunc=dtime100,caption='Step Vector usage time'),
    Uint4('ivu',ppfunc=dtime100,caption='Initiator Vector usage time'),
    Uint4('jva',ppfunc=dtime100,caption='Step Vector affinity time'),
    Uint4('iva',ppfunc=dtime100,caption='Initiator Vector affinity time'),

    Uint4('ist',ppfunc=dtime100,caption='Interval start time'), # for subtype 2,3 records
    Packed('idt',4,ppfunc=idate,caption='Interval start date'), # Date

    Uint4('iip',ppfunc=dtime100,caption='CPU time I/O Interrupts'),       # ASSBIIPT-TCTEIIP
    Uint4('rct',ppfunc=dtime100,caption='CPU time Region Control Task'),  # TCBTIME-TCTERCT

    Uint4('hpt',caption='Step CPU time transfers hiper space and A/S'), # ASSBHST-TCTEHPT
    Uint4('csc',caption='ICSF Crypto service count'), # ASSBFSC-TCTANSC

    Uint4('dmi',caption='ADMF moved pages writes'), # ASSBTPMT-TCTADMFW
    Uint4('dmo',caption='ADMF moved pages reads'), # ASSBTPMA-TCTADMFR

    Uint4('asr',ppfunc=dtime100,caption='Step CPU time preemptable and client SRBs'),  # ASSBASST, value included in cpt
    Uint4('enc',ppfunc=dtime100,caption='Step independent enclave CPU time'), # RQSVECPT, value included in cpt
    Uint4('det',ppfunc=dtime100,caption='Step dependent enclave CPU time'),  # RQSVDET, value included in cpt

    Uint4('cep',caption='CPU time while ENQ promoted'),  # in 1.024 millisec, cumulative even for interval records

    Bytes('tf2',1,caption='Timer Flag2'),
    #o todo
    Bytes('t32',1,caption='Timer Flag32'),
    Bytes('t33',1,caption='Timer Flag33'),
    Bytes('t34',1,opt=T_NONE),

    Uint4('toi',ppfunc=dtime100,caption='Time on IFA'),             # ASSB_Time_On_IFA, includes enclave time
    Uint4('etoi',ppfunc=dtime100,caption='Enclave time on IFA'),    # Rqsv_Enclave_Time_On_IFA
    Uint4('detoi',ppfunc=dtime100,caption='Dependent enclave time on IFA'),  # Rqsv_Dep_Enclave_Time_On_IFA

    Uint4('tic',ppfunc=dtime100,caption='IFA time on CP'),          # ASSB_Time_IFA_ON_CP IFA includes enclave time
    Uint4('etic',ppfunc=dtime100,caption='IFA enclave time on CP'), # Rqsv_Enclave_Time_IFA_ON_CP
    Uint4('detic',ppfunc=dtime100,caption='IFA dependent enclave time on CP'),  # Rqsv_Dep_Enclave_Time_IFA_ON_CP

    Uint4('cepi',caption='CPU time while ENQ promoted'),  # in 1.024 millisec, interval time

    Uint4('toz',ppfunc=dtime100,caption='Time on zIIP'),             # ASSB_Time_On_zIIP Time, includes enclave time
    Uint4('etoz',ppfunc=dtime100,caption='Enclave time on zIIP'),    # Rqsv_Enclave_Time_On_SUP
    Uint4('detoz',ppfunc=dtime100,caption='Dependent enclave time on zIIP'),  # Rqsv_DEPENC_Time_On_SUP

    Uint4('zoc',ppfunc=dtime100,caption='zIIP time on CP'),          # ASSB_Time_zIIP_ON_CP includes enclave time
    Uint4('ezoc',ppfunc=dtime100,caption='Enclave zIIP time on CP'), # Rqsv_Enclave_Time_SUP_ON_CP
    Uint4('dezoc',ppfunc=dtime100,caption='Dependent enclave zIIP time on CP'),  # Rqsv_DEPENC_Time_SUP_ON_CP

    Uint4('etozq',ppfunc=dtime100,caption='Enclave zIIP time on CP normalized'),  # Rqsv_Enclave_TIME_SUP_QUAL
    Uint4('detozq',ppfunc=dtime100,caption='Dependent enclave zIIP time on CP normalized'),  # Rqsv_DepEnc_TIME_SUP_QUAL

    Uint4('crp',caption='CPU time while CRM promoted'),  # in 1.024 millisec, time during interval
    # RqsvCPUtimeConsumedWhileCRMpromoted, CRM - chronic resource contention

    Uint4('icust',ppfunc=dtime100,caption='CPU TCB time for step term'), # included in icu
    Uint4('icusi',ppfunc=dtime100,caption='CPU TCB time for step init'), # included in icu
    Uint4('isbst',ppfunc=dtime100,caption='CPU SRB time for step term'), # included in isb
    Uint4('isbsi',ppfunc=dtime100,caption='CPU SRB time for step init'), # included in isb

    Uint4('mblk',caption='Missed I/O block counting '),      # w/o serialization to counter SMF30BLK, zero for startet tasks
    Uint4('mdct',caption='Missed device connect counting'), # w/o serialization to counter SMF30DCT, zero for started tasks

    Uint2('hit',ppfunc=percent,caption='Highest Task CPU percent'),  # TCB time * 100 / interval time
    String('hip',8,caption='Highest Task Program name'),

    Bytes('flag',1,caption='CPU Accounting flag'),
    Bytes('r0bb',1,opt=T_NONE),

    #dmlen should be == SMF30CASLEN
    byteOrder=NETWORKBO,ebcdic=1,**kw)
SMF30CASLEN = 0xbc  # 188


if __name__ == "__main__":
    import sys
    # import doctest
    # doctest.testmod()
    print('\n%s defines SMF record structures.\n\tIt has no main section - do not execute it directly.\n' % __file__)
    sys.exit(99)

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
