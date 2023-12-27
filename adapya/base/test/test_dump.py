# -*- coding: cp1252 -*-
""" Demonstrate and test some dump.py functions
$Date: 2017-02-24 15:09:26 +0100 (Fri, 24 Feb 2017) $
$Rev: 740 $
"""
from __future__ import print_function          # PY3




if __name__=='__main__':

    if 0:
        import sys
        import binascii


        ud1="""
       1A20C0A0 F16BC24B F3000000 3F30303F 000C0001    C6C4E600 0120C100 F3000000 3F30303F   *1,B.3...........FDW...A.3.......*
       1A20C0C0 000C0001 C6C4E600 0120C100 44422020    20202020 202020C8 00000033 31373438   *....FDW...A............H........*
       1A20C0E0 31303730 37202020 20202001 00000000    00000000 00000000 00000000 00000000   *................................*
       1A20C100 00000000 00000000 00000000 0400006B    C26BC2F0 6BF46BC2 6BC2F16B F46BC26B   *...............,B,B0,4,B,B1,4,B,*


      0USER SUBPOOL STORAGE
      000006020                   00000000 00000000    1B6F2F68 80FCAFE8 9B6F1F20 00000000   *        .........?.....Y.?......*
       00006040 0015C000 1B4F8C38 000C77E3 0011CEC8    1B6E9BD8 1A201F00 1A2015E8 1B6705DC   *..{..|.....T...H.>.Q.......Y....*
       00006060 1B6E7568 0015C000 9B66D5F0 1B6D5008    00000000 00000000 00000000 00000000   *.>....{...N0._&.................*
       00006080 00000000 00000000 00000000 00000000    00000000 00000000 00000000 00000000   *................................*
             LINE 000060A0  SAME AS ABOVE

       00006680 00000000 00000001 1A201FF9 1A201FF9    00000000 00000001 00000000 00000001   *...........9...9................*
       000066A0 C4C3C2C5 00380000 00000000 00000000    00800000 00000000 00000000 00000000   *DCBE............................*
       000066C0 00000000 00000000 00000000 00000000    00000000 00000000                     *........................        *

       1B81EC40 406CE46C 404D8396 5D40E296 86A3A681    998540C1 C7000000 00000000 00000000   * %U% (co) Software AG...........*
       1B81EC60 00000000 00000000 00000000 00000000    00000000 00000000 00000000 00000000   *................................*
             LINES 1B81EC80-1B81ECA0  SAME AS ABOVE
       1B81ECC0 00000000 00000000 00000000 00000000    7C4D7B5D 5BC9847A 4082A483 96949793   *................@(#)$Id: bucompl*
       1B81ECE0 994B836B A540F14B F440F2F0 F0F361F0    F161F2F8 40F1F97A F4F37AF5 F840A4A2   *r.c,v 1.4 2003/01/28 19:43:58 us*


      """


        sys.exit()

        rbuf="""
      1) AN ISN LIST WITH AN EXPLICIT ISN FOLLOWED BY RANGES ONLY RETURNS THE EXPLICIT ISN

      URBH... 01......................GOODRG&S                        URBI...@...-....
      EDCC0004FF00000B0000000000000000CDDCDC5E444444444444444444444444EDCC000700060001
      492800000101000C0000000000000000766497020000000000000000000000004929000C0000000C

      INITSTATOUT1    INST.G..I199FALL
      CDCEEECEDEEF4444CDEE0C08CFFFCCDD444444444444444444444444444444444444444444444444
      95932313643100009523070F91996133000000000000000000000000000000000000000000000000

      ............................
      0000FFFF00000000FFFF0000FFFF
      0001FFFF00020003FFFF0004FFFE

       x000000! E4D9C2C8 00000040 F0F10001 000000C0  00000153 BB4F748B C94CA900 0FA10000 !  x000000!URBH    01     {   ??!??I<z  ~  !
       x000020! D9C5D7E3 D6D94040 00000000 00000000  00000000 00000000 00000000 00000000 !  x000020!REPTOR                          !
       x000040! E4D9C2E2 00000080 C9D5C9E3 E2E3C1E3  C9D5E2E3 C9D5C9E3 BB4F748B C9492500 !  x000040!URBS   ?INITSTATINSTINIT?!??I?  !
       x000060! 00000000 00000000 40404040 40404040  C9F1F9F9 C6C1D3D3 40404040 40404040 !  x000060!                I199FALL        !
       x000080! 40404040 40404040 00000000 00000000  00000000 00000000 00000000 00C7008F !  x000080!                             G ?!
       x0000a0! 00000000 00000000 00000000 00000000  00000000 00000000 00000000 00000000 !  x0000A0!                                !
       end of message
       x000000! E4D9C2C8 00000040 F0F10001 00000140  00000154 BB4F748B D471B800 0FA10000 !  x000000!URBH    01         ??!??M??  ~  !
       x000020! D9C5D7E3 D6D94040 00000000 00000000  00000000 00000000 00000000 00000000 !  x000020!REPTOR                          !
       x000040! E4D9C2E3 00000070 C4F1F9F9 C6F1F4F3  00000000 00000001 BB4F748B CEEC2D40 !  x000040!URBT   ?D199F143        ?!????  !
       x000060! BB4F748B D4583920 00C70000 11111111  33333333 BB4F748B C96FDA40 00000000 !  x000060!?!??M?   G          ?!??I??     !
       x000080! 0FA10000 008F0000 0FA10000 404040E8  C9D5C9E3 E2E3C1E3 40000000 00000000 !  x000080!?~   ?   ~     YINITSTAT        !
       x0000a0! 00000000 00000000 00000000 00000000  E4D9C2D9 00000040 00000001 0001008F !  x0000A0!                URBR           ?!
       x0000c0! 00000001 BB4F748B CEEBEA80 D9400000  00000000 40404040 40404040 00000000 !  x0000C0!    ?!??????R                   !
       x0000e0! 00000000 00000000 00000000 00000000  E4D9C2C4 00000030 00000020 00000007 !  x0000E0!                URBD            !
       x000100! 00000001 C1000000 00000000 00000000  C1C1C1C1 C1C1C100 00000000 00000000 !  x000100!    A           AAAAAAA         !
       x000120! E4D9C2C5 00000020 C4F1F9F9 C6F1F4F3  00000000 00000000 00000000 00000000 !  x000120!URBE    D199F143                !
       end of message
       x000000! E4D9C2C8 00000040 F0F10001 000000C0  00000155 BB4F748B D491D880 0FA10000 !  x000000!URBH    01     {   @?!??MjQ? ~  !
       x000020! D9C5D7E3 D6D94040 00000000 00000000  00000000 00000000 00000000 00000000 !  x000020!REPTOR                          !
       x000040! E4D9C2E2 00000080 C9D5C9E3 E2E3C1E3  C9D5E2E3 C3D4D7D3 BB4F748B D45A0220 !  x000040!URBS   ?INITSTATINSTCMPL?!??M!  !
       x000060! 00000000 00000000 40404040 40404040  C9F1F9F9 C6C1D3D3 40404040 40404040 !  x000060!                I199FALL        !
       x000080! 40404040 40404040 00000000 00000000  00000000 00000000 00000000 00C7008F !  x000080!                             G ?!
       x0000a0! 00000000 00000000 00000000 00000000  00000000 00000000 00000000 00000000 !  x0000A0!                                !
       end of message

      2) AN ISNLIST WITH RANGES FOLLOWED BY A NON EXISTENT EXPLICIT ISN RESULTS IN THE RANGES BEING RETURNED BUT NO RSP-113 FOR THE EXPLICIT ISN

      URBH... 01......................2RNG&113                        URBI...@...-....
      EDCC0004FF00000B0000000000000000FDDC5FFF444444444444444444444444EDCC000700060001
      492800000101000C0000000000000000295701130000000000000000000000004929000C0000000C

      INITSTATOUT1    INST.G..I199FALL
      CDCEEECEDEEF4444CDEE0C08CFFFCCDD444444444444444444444444444444444444444444444444
      95932313643100009523070F91996133000000000000000000000000000000000000000000000000

      ..........................C.
      FFFF00000000FFFF0000000000C5
      FFFF00010002FFFF000300040031

       x000000! E4D9C2C8 00000040 F0F10001 000000C0  00000282 BB4F78E6 F79F2C40 0FA10000 !  x000000!URBH    01     {   b?!?W7�   ~  !
       x000020! D9C5D7E3 D6D94040 00000000 00000000  00000000 00000000 00000000 00000000 !  x000020!REPTOR                          !
       x000040! E4D9C2E2 00000080 C9D5C9E3 E2E3C1E3  C9D5E2E3 C9D5C9E3 BB4F78E6 F79BAC20 !  x000040!URBS   ?INITSTATINSTINIT?!?W7?? !
       x000060! 00000000 00000000 40404040 40404040  C9F1F9F9 C6C1D3D3 40404040 40404040 !  x000060!                I199FALL        !
       x000080! 40404040 40404040 00000000 00000000  00000000 00000000 00000000 00C7008F !  x000080!                             G ?!
       x0000a0! 00000000 00000000 00000000 00000000  00000000 00000000 00000000 00000000 !  x0000A0!                                !
       end of message
       x000000! E4D9C2C8 00000040 F0F10001 00000290  00000283 BB4F78E6 FFAEF720 0FA10000 !  x000000!URBH    01     ?   c?!?W ?7  ~  !
       x000020! D9C5D7E3 D6D94040 00000000 00000000  00000000 00000000 00000000 00000000 !  x000020!REPTOR                          !
       x000040! E4D9C2E3 00000070 C4F1F9F9 C6F1F4F3  00000000 00000004 BB4F78E6 FD182E60 !  x000040!URBT   ?D199F143        ?!?W?  -!
       x000060! BB4F78E6 FF980B40 00C70000 11111111  33333333 BB4F78E6 F7C42A80 00000000 !  x000060!?!?W q   G          ?!?W7D ?    !
       x000080! 0FA10000 008F0000 0FA10000 404040E8  C9D5C9E3 E2E3C1E3 40000000 00000000 !  x000080!?~   ?   ~     YINITSTAT        !
       x0000a0! 00000000 00000000 00000000 00000000  E4D9C2D9 00000040 00000001 0001008F !  x0000A0!                URBR           ?!
       x0000c0! 00000001 BB4F78E6 FCD59800 D9400000  00000000 40404040 40404040 00000000 !  x0000C0!    ?!?W?Nq R                   !
       x0000e0! 00000000 00000000 00000000 00000000  E4D9C2C4 00000030 00000020 00000007 !  x0000E0!                URBD            !
       x000100! 00000001 C1000000 00000000 00000000  C1C1C1C1 C1C1C100 00000000 00000000 !  x000100!    A           AAAAAAA         !
       x000120! E4D9C2D9 00000040 00000002 0001008F  00000002 BB4F78E6 FD173700 D9400000 !  x000120!URBR           ?    ?!?W?   R   !
       x000140! 00000000 40404040 40404040 00000000  00000000 00000000 00000000 00000000 !  x000140!                                !
       x000160! E4D9C2C4 00000030 00000020 00000007  00000001 C1000000 00000000 00000000 !  x000160!URBD                A           !
       x000180! C1C1C1C1 C1C1C100 00000000 00000000  E4D9C2D9 00000040 00000003 0001008F !  x000180!AAAAAAA         URBR           ?!
       x0001a0! 00000003 BB4F78E6 FD17A620 D9400000  00000000 40404040 40404040 00000000 !  x0001A0!    ?!?W? w R                   !
       x0001c0! 00000000 00000000 00000000 00000000  E4D9C2C4 00000030 00000020 00000007 !  x0001C0!                URBD            !
       x0001e0! 00000001 C1000000 00000000 00000000  C1C1C1C1 C1C1C100 00000000 00000000 !  x0001E0!    A           AAAAAAA         !
       x000200! E4D9C2D9 00000040 00000004 0001008F  00000004 BB4F78E6 FD17F760 D9400000 !  x000200!URBR           ?    ?!?W? 7-R   !
       x000220! 00000000 40404040 40404040 00000000  00000000 00000000 00000000 00000000 !  x000220!                                !
       x000240! E4D9C2C4 00000030 00000020 00000007  00000001 C1000000 00000000 00000000 !  x000240!URBD                A           !
       x000260! C1C1C1C1 C1C1C100 00000000 00000000  E4D9C2C5 00000020 C4F1F9F9 C6F1F4F3 !  x000260!AAAAAAA         URBE    D199F143!
       x000280! 00000000 00000000 00000000 00000000
       end of message
       x000000! E4D9C2C8 00000040 F0F10001 000000C0  00000284 BB4F78E6 FFBF8C20 0FA10000 !  x000000!URBH    01     {   d?!?W ??  ~  !
       x000020! D9C5D7E3 D6D94040 00000000 00000000  00000000 00000000 00000000 00000000 !  x000020!REPTOR                          !
       x000040! E4D9C2E2 00000080 C9D5C9E3 E2E3C1E3  C9D5E2E3 C3D4D7D3 BB4F78E6 FF9A8F80 !  x000040!URBS   ?INITSTATINSTCMPL?!?W ???!
       x000060! 00000000 00000000 40404040 40404040  C9F1F9F9 C6C1D3D3 40404040 40404040 !  x000060!                I199FALL        !
       x000080! 40404040 40404040 00000000 00000000  00000000 00000000 00000000 00C7008F !  x000080!                             G ?!
       x0000a0! 00000000 00000000 00000000 00000000  00000000 00000000 00000000 00000000 !  x0000A0!                                !
       end of message

      """
        buffs=hexRbuf(rbuf)
        for i in range(len(buffs)):
            dump(buffs[i],header='buffer %d'%i)

        sys.exit()



        hxTso="""
      URBH... 01.....�....]]]]]]]]....INITSTA1........................
      EDCC0004FF00000A0001BBBBBBBB0000CDCEEECF000000000000000000000000
      492800000101000C0000BBBBBBBB060095932311000000000000000000000000

      URBI...%...-....TOKEN001MQ1     INST....FILE002I
      EDCC000600060000EDDCDFFFDDF44444CDEE0000CCDCFFFC
      4929000C0000000C36255001481000009523060269350029

                      ............................................
      444444444444444400000000000000000000000000000000FFFF00000000
      000000000000000000000000000000000000000000000000FFFF00020004
      """

        h3=hex3buf(hxTso)

        dump(h3)

        sys.exit()


        hx="""
      E4D9C2C8 00000040 F0F10001 000000A0  00000010 BBBBBBBB BBBBBBBB 00060000
      C9D5C9E3 E2E3C1F1 00000000 00000000  00000000 00000000 00000000 00000000
      E4D9C2C9 00000060 00000060 00000000  E3D6D2C5 D5F0F0F1 D4D8F140 40404040
      C9D5E2E3 00060002 C6C9D3C5 F0F0F0F2  40404040 40404040 40404040 40404040
      00000000 00000000 00000000 00000000  00000000 00000000 00000000 00000000
        """

        dump(hex2buf(hx))

        sys.exit()


        dump(ascpribles, header='ASCII')
        dump(ebcpribles, header='EBCDIC')

        bbbb='\
        55524248 40000000 30310100 C0000000\
        55524248 40000000 30310100 C0000000\
        01000000 A05EDC18 E3AF08BB 17270000\
        52455054 4F522020 00000000 00000000\
        00000000 00000000 00000000 00000000\
        00000000 00000000 00000000 00000000\
        55524253 80000000 00000000 00000000\
        20202020 53545254 A28DBDF7 E2AF08BB\
        20202020 53545254 A28DBDF7 E2AF08BB\
        00000000 00000000 20202020 20202020\
        20202020 20202020 20202020 20202020\
        20202020 20202020 20202020 20202020\
        20202020 20202020 20202020 20202020\
        20202020 20202020 00000000 00000000\
        00000000 00000000 00000000 00000000\
        00000000 00000000 00000000 00000000\
        00000000 00000000 00000000 00000000\
        00000000 00000000 00000000 00'

        sbbb = binascii.unhexlify(string.replace(bbbb, ' ',''))
        dump(sbbb)



        for i in range(1,16):
            print( 'i=%d' % i )
            dump(ebcpribles[224:224+i], header='ASCII')


        print('Now writing to dump.log')
        fd=open('dump.log', 'w')

        dump(ascpribles, header='ASCII', fd=fd)

        dump(ebcpribles, header='EBCDIC', fd=fd)

        for i in range(1,16):
            print( 'i=%d' % i, file=fd)
            dump(ebcpribles[224:224+i], header='EBCDIC', fd=fd)

        fd.close() # close dump.log

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
