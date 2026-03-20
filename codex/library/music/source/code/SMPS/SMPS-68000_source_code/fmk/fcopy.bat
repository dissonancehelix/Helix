echo off

echo *****************  ƒ\[ƒXƒtƒ@ƒCƒ‹‚ğƒRƒs[‚µ‚Ü‚·@*****************

:‚`‚r‚l@ƒtƒ@ƒCƒ‹

echo/
echo * mdCNT11.ASM ¨ %1CNT.ASM
copy	..\VER11\MDCNT11.ASM	%1CNT.ASM	> nul
echo/
echo * mdCMD11.ASM ¨ %1CMD.ASM
copy	..\VER11\MDCMD11.ASM	%1CMD.ASM	> nul
echo/
echo * mdPSG11.ASM ¨ %1PSG.ASM
copy	..\VER11\MDPSG11.ASM	%1PSG.ASM	> nul
echo/
echo * mdTB11.ASM ¨ %1TB.ASM
copy	..\VER11\MDTB11.ASM	%1TB.ASM	> nul
echo/
echo * mdSETB11.ASM ¨ %1SETB.ASM
copy	..\VER11\MDSETB11.ASM	%1SETB.ASM	> nul
echo/
echo * mdPCM11.ASM ¨ %1PCM.ASM
copy	..\VER11\MDPCM11.ASM	%1PCM.ASM	> nul
echo/
echo * mdVDT11.ASM ¨ %1VDT.ASM
copy	..\VER11\MDVDT11.ASM	%1VDT.ASM	> nul

:‚k‚h‚a@ƒtƒ@ƒCƒ‹

echo/
echo * mdEQ11.LIB ¨ %1EQ.LIB
copy	..\VER11\MDEQ11.lib	%1EQ.LIB	> nul
echo/
echo * mdTB11.LIB ¨ %1TB.LIB
copy	..\VER11\MDTB11.lib	%1TB.LIB	> nul
echo/
echo * mdMCR11.LIB ¨ %1MCR.LIB
copy	..\VER11\MDMCR11.lib	%1MCR.LIB 	> nul

if "%2"=="asm" goto skip
if "%2"=="ASM" goto skip

:‚r‚n‚m‚f@ƒtƒ@ƒCƒ‹

echo/
echo * mdSNG111.S ¨ %1SNG81.S
copy	..\VER11\MDSNG111.S	%1SNG81.S	> nul
echo/
echo * mdSNG211.S ¨ %1SNG82.S
copy	..\VER11\MDSNG211.S	%1SNG82.S	> nul
echo/
echo * mdSNG311.S ¨ %1SNG83.S
copy	..\VER11\MDSNG311.S	%1SNG83.S	> nul
echo/
echo * mdSNG411.S ¨ %1SNG84.S
copy	..\VER11\MDSNG411.S	%1SNG84.S	> nul
echo/
echo * mdSNG511.S ¨ %1SNG85.S
copy	..\VER11\MDSNG511.S	%1SNG85.S	> nul
echo/
echo * mdSNG611.S ¨ %1SNG86.S
copy	..\VER11\MDSNG611.S	%1SNG86.S	> nul
echo/
echo * mdSNG711.S ¨ %1SNG87.S
copy	..\VER11\MDSNG711.S	%1SNG87.S	> nul
echo/
echo * mdSNG811.S ¨ %1SNG88.S
copy	..\VER11\MDSNG811.S	%1SNG88.S	> nul
echo/
echo * mdSNG911.S ¨ %1SNG89.S
copy	..\VER11\MDSNG911.S	%1SNG89.S	> nul
echo/
echo * mdSNGA11.S ¨ %1SNG8A.S
copy	..\VER11\MDSNGA11.S	%1SNG8A.S	> nul
echo/
echo * mdSNGB11.S ¨ %1SNG8B.S
copy	..\VER11\MDSNGB11.S	%1SNG8B.S	> nul
echo/
echo * mdSNGC11.S ¨ %1SNG8C.S
copy	..\VER11\MDSNGC11.S	%1SNG8C.S	> nul
echo/
echo * mdSNGD11.S ¨ %1SNG8D.S
copy	..\VER11\MDSNGD11.S	%1SNG8D.S	> nul
echo/
echo * mdSNGE11.S ¨ %1SNG8E.S
copy	..\VER11\MDSNGE11.S	%1SNG8E.S	> nul
echo/
echo * mdSNGF11.S ¨ %1SNG8F.S
copy	..\VER11\MDSNGF11.S	%1SNG8F.S	> nul

:‚rD‚dD@ƒtƒ@ƒCƒ‹

echo/
echo * mdSE111.S ¨ %1SE1.S
copy	..\VER11\MDSE111.S	%1SE1.S		> nul
echo/
echo * mdSE211.S ¨ %1SE2.S
copy	..\VER11\MDSE211.S	%1SE2.S		> nul
echo/
echo * mdSE311.S ¨ %1SE3.S
copy	..\VER11\MDSE311.S	%1SE3.S		> nul
echo/
echo * mdBSE11.S ¨ %1BSE.S
copy	..\VER11\MDBSE11.S	%1BSE.S		> nul

:‚»‚Ì‘¼‚Ìƒtƒ@ƒCƒ‹

echo/
echo * md11.DOC ¨ %1.DOC
copy	..\VER11\MD11.DOC	%1.DOC		> nul
echo/
echo * md11.BAT ¨ %1.BAT
copy	..\VER11\MD11.BAT	%1.BAT		> nul
echo/
echo * md11.LNK ¨ %1.LNK
copy	..\VER11\MD11.LNK	%1.LNK		> nul
echo/
echo * ALL.LNK ¨ ALL.LNK
copy	..\VER11\ALL.LNK	ALL.lNK		> nul
echo/
echo * md11.MKF ¨ %1.MKF
copy	..\VER11\MD11.MKF	%1.MKF		> nul
echo/
echo * MAKERULE.DEF ¨ MAKERULE.DEF
copy	..\VER11\MAKERULE.DEF	MAKERULE.DEF	> nul

:‚U‚W‚j@‚h‚b‚d—p@ƒtƒ@ƒCƒ‹

echo/
echo * ERX68K.MAC ¨ ERX68K.MAC
copy	..\VER11\ERX68K.MAC	ERX68K.MAC	> nul
echo/
echo * Z.CMD ¨ Z.CMD
copy	..\VER11\Z.CMD		Z.CMD		> nul

:‚y‚W‚O@ƒtƒ@ƒCƒ‹

echo/
echo * pcm\mdDR11.SRC ¨ pcm\%1DR.SRC
copy	..\VER11\PCM\MDDR11.SRC		PCM\%1DR.SRC	> nul
echo/
echo * pcm\mdDT11.SRC ¨ pcm\%1DT.SRC
copy	..\VER11\PCM\MDDT11.SRC		PCM\%1DT.SRC	> nul
echo/
echo * pcm\mdVT11.SRC ¨ pcm\%1VT.SRC
copy	..\VER11\PCM\MDVT11.SRC		PCM\%1VT.SRC	> nul
echo/
echo * pcm\mdZ11.BAT ¨ pcm\%1Z.BAT
copy	..\VER11\PCM\MDZ11.BAT		PCM\%1Z.BAT	> nul
echo/
echo * pcm\mdZ11.MKF ¨ pcm\%1Z.MKF
copy	..\VER11\PCM\MDZ11.MKF		PCM\%1Z.MKF	> nul
echo/
echo * pcm\MAKERULE.DEF ¨ pcm\MAKERULE.DEF
copy	..\VER11\PCM\MAKERULE.DEF	PCM\MAKERULE.DEF > nul
echo/
echo * pcm\mdDR11.HHH ¨ pcm\%1DR.HHH
copy	..\VER11\PCM\MDDR11.HHH		PCM\%1DR.HHH	> nul
echo/
echo * pcm\mdVT11.HHH ¨ pcm\%1VT.HHH
copy	..\VER11\PCM\MDVT11.HHH		PCM\%1VT.HHH	> nul

:‚y‚W‚O@‚h‚b‚d—p@ƒtƒ@ƒCƒ‹

echo/
echo * pcm\mdZZ11.BAT ¨ pcm\%1ZZ.BAT
copy	..\VER11\PCM\MDZZ11.BAT		PCM\%1ZZ.BAT	> nul
echo/
echo * pcm\mdZZ11.MAC ¨ pcm\%1ZZ.MAC
copy	..\VER11\PCM\MDZZ11.MAC		PCM\%1ZZ.MAC	> nul
echo/
echo * pcm\INIT.MCR ¨ pcm\INIT.MCR
copy	..\VER11\PCM\INIT.MCR		PCM\INIT.MCR	> nul

:‚y‚W‚O@‚o‚b‚l@ƒTƒ“ƒvƒ‹ƒtƒ@ƒCƒ‹

echo/
echo * pcm\BASSDRUM.HHH ¨ pcm\BASSDRUM.HHH
copy	..\VER11\PCM\BASSDRUM.HHH	PCM\BASSDRUM.HHH > nul
echo/
echo * pcm\SNARE.HHH ¨ pcm\SNARE.HHH
copy	..\VER11\PCM\SNARE.HHH		PCM\SNARE.HHH > nul
echo/
echo * pcm\HANDCLAP.HHH ¨ pcm\HANDCLAP.HHH
copy	..\VER11\PCM\HANDCLAP.HHH	PCM\HANDCLAP.HHH > nul
echo/
echo * pcm\OPEN_HAT.HHH ¨ pcm\OPEN_HAT.HHH
copy	..\VER11\PCM\OPEN_HAT.HHH	PCM\OPEN_HAT.HHH > nul
echo/
echo * pcm\TOMTOM.HHH ¨ pcm\TOMTOM.HHH
copy	..\VER11\PCM\TOMTOM.HHH		PCM\TOMTOM.HHH > nul
echo/
echo * pcm\HATO.HHH ¨ pcm\HATO.HHH
copy	..\VER11\PCM\HATO.HHH		PCM\HATO.HHH > nul

:skip
:end

