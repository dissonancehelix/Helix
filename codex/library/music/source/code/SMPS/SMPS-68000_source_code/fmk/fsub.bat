echo off
echo *****************  ƒtƒ@ƒCƒ‹‚Ìˆê•”•ª‚ğ•ÏX‚µ‚Ü‚·@*****************
echo/
echo               Project Name : %1
echo                       Date : %2
echo                  Game Name : %3
echo                     Person : %4

:‚r‚d‚cƒXƒNƒŠƒvƒgƒtƒ@ƒCƒ‹‚Ì•ÏX

sed -e s/@1/%1/g -e s/@2/%2/g -e s/@3/%3/g -e s/@4/%4/g ..\FMK\FSUB1.SED > temp1
sed -e s/@1/%1/g ..\FMK\FSUB2.SED > temp2

:‚`‚r‚l@ƒtƒ@ƒCƒ‹

echo/
echo * %1CNT.ASM
sed -f temp1 %1CNT.ASM | tee %1CNT.ASM > nul
echo/
echo * %1CMD.ASM
sed -f temp1 %1CMD.ASM | tee %1CMD.ASM > nul
echo/
echo * %1PSG.ASM
sed -f temp1 %1PSG.ASM | tee %1PSG.ASM > nul
echo/
echo * %1TB.ASM
sed -f temp1 %1TB.ASM | tee %1TB.ASM > nul
echo/
echo * %1SETB.ASM
sed -f temp1 %1SETB.ASM | tee %1SETB.ASM > nul
echo/
echo * %1PCM.ASM
sed -f temp1 %1PCM.ASM | tee %1PCM.ASM > nul
echo/
echo * %1VDT.ASM
sed -f temp1 %1VDT.ASM | tee %1VDT.ASM > nul

:‚k‚h‚a@ƒtƒ@ƒCƒ‹

echo/
echo * %1EQ.LIB
sed -f temp1 %1EQ.LIB | tee %1EQ.LIB > nul
echo/
echo * %1MCR.LIB
sed -f temp1 %1MCR.LIB | tee %1MCR.LIB > nul
echo/
echo * %1TB.LIB
sed -f temp1 %1TB.LIB | tee %1TB.LIB > nul

if "%5"=="ASM" goto skip
if "%5"=="ASM" goto skip

:‚r‚n‚m‚f@ƒtƒ@ƒCƒ‹

echo/
echo * %1SNG81.S
sed -f temp1 %1SNG81.S | tee %1SNG81.S > nul
echo/
echo * %1SNG82.S
sed -f temp1 %1SNG82.S | tee %1SNG82.S > nul
echo/
echo * %1SNG83.S
sed -f temp1 %1SNG83.S | tee %1SNG83.S > nul
echo/
echo * %1SNG84.S
sed -f temp1 %1SNG84.S | tee %1SNG84.S > nul
echo/
echo * %1SNG85.S
sed -f temp1 %1SNG85.S | tee %1SNG85.S > nul
echo/
echo * %1SNG86.S
sed -f temp1 %1SNG86.S | tee %1SNG86.S > nul
echo/
echo * %1SNG87.S
sed -f temp1 %1SNG87.S | tee %1SNG87.S > nul
echo/
echo * %1SNG88.S
sed -f temp1 %1SNG88.S | tee %1SNG88.S > nul
echo/
echo * %1SNG89.S
sed -f temp1 %1SNG89.S | tee %1SNG89.S > nul
echo/
echo * %1SNG8A.S
sed -f temp1 %1SNG8A.S | tee %1SNG8A.S > nul
echo/
echo * %1SNG8B.S
sed -f temp1 %1SNG8B.S | tee %1SNG8B.S > nul
echo/
echo * %1SNG8C.S
sed -f temp1 %1SNG8C.S | tee %1SNG8C.S > nul
echo/
echo * %1SNG8D.S
sed -f temp1 %1SNG8D.S | tee %1SNG8D.S > nul
echo/
echo * %1SNG8E.S
sed -f temp1 %1SNG8E.S | tee %1SNG8E.S > nul
echo/
echo * %1SNG8F.S
sed -f temp1 %1SNG8F.S | tee %1SNG8F.S > nul

:‚rD‚dD@ƒtƒ@ƒCƒ‹

echo/
echo * %1SE1.S
sed -f temp1 %1SE1.S | tee %1SE1.S > nul
echo/
echo * %1SE2.S
sed -f temp1 %1SE2.S | tee %1SE2.S > nul
echo/
echo * %1SE3.S
sed -f temp1 %1SE3.S | tee %1SE3.S > nul
echo/
echo * %1BSE.S
sed -f temp1 %1BSE.S | tee %1BSE.S > nul

:‚»‚Ì‘¼‚Ìƒtƒ@ƒCƒ‹

echo/
echo * %1.DOC
sed -f temp1 %1.DOC | tee %1.DOC > nul
sed -f temp2 %1.DOC | tee %1.DOC > nul
echo/
echo * %1.BAT
sed -f temp1 %1.BAT | tee %1.BAT > nul
sed -f temp2 %1.BAT | tee %1.BAT > nul
echo/
echo * %1.LNK
sed -f temp2 %1.LNK | tee %1.LNK > nul
echo/
echo * ALL.LNK
sed -f temp2 ALL.LNK | tee ALL.LNK > nul
echo/
echo * %1.MKF
sed -f temp2 %1.MKF | tee %1.MKF > nul
echo/
echo * ERX68K.MAC
sed -f temp2 ERX68K.MAC | tee ERX68K.MAC > nul

:‚y‚W‚O@ƒtƒ@ƒCƒ‹
echo/
echo * pcm\%1DR.SRC
sed -f temp1 pcm\%1DR.SRC | tee pcm\%1DR.SRC > nul
echo/
echo * pcm\%1DT.SRC
sed -f temp1 pcm\%1DT.SRC | tee pcm\%1DT.SRC > nul
echo/
echo * pcm\%1VT.SRC
sed -f temp1 pcm\%1VT.SRC | tee pcm\%1VT.SRC > nul
echo/
echo * pcm\%1Z.BAT
sed -f temp1 pcm\%1Z.BAT | tee pcm\%1Z.BAT > nul
sed -f temp2 pcm\%1Z.BAT | tee pcm\%1Z.BAT > nul
echo/
echo * pcm\%1Z.MKF
sed -f temp2 pcm\%1Z.MKF | tee pcm\%1Z.MKF > nul
echo/
echo * pcm\%1ZZ.BAT
sed -f temp2 pcm\%1ZZ.BAT | tee pcm\%1ZZ.BAT > nul
echo/
echo * pcm\%1ZZ.MAC
sed -f temp2 pcm\%1ZZ.MAC | tee pcm\%1ZZ.MAC > nul
echo/
echo * pcm\INIT.MCR
sed -f temp2 pcm\INIT.MCR | tee pcm\INIT.MCR > nul


:skip
:end
