if "%1"=="" goto usage
if "%5"=="s" goto data
if "%5"=="S" goto data

COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2int13.src  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2cnt13.src  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2cmd13.src  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2fmdr13.src %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2psg13.src  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2pcm13.src  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2tb13.src   %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2setb13.src %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2eq13.lib   %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2tb13.lib   %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2mcr13.lib  %3 %4

if "%5"=="src" goto end
if "%5"=="SRC" goto end
:data
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2se13.s     %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng113.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng213.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng313.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng413.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng513.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng613.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng713.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng813.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sng913.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2snga13.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sngb13.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sngc13.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sngd13.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2snge13.s  %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2sngf13.s  %3 %4
if "%5"=="s" goto END
if "%5"=="S" goto END

COMMAND/C \M5\Z80\FMK\DAYSUB %1 %213.bat     %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2z13.bat    %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %2z13.mac    %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %213.doc     %3 %4

COMMAND/C \M5\Z80\FMK\DAYSUB %1 %213.mkf     %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 %213.lnk     %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 all.lnk    %3 %4
COMMAND/C \M5\Z80\FMK\DAYSUB %1 erx68k.mac %3 %4
:skip
:usage
	echo	off
	echo	ｐｒｊｅｃｔ　ファイルの日付を変えます。
	echo ｄａｙ　＜ｄｉｒ＞　＜ｐｒｊ＞　＜旧日付＞　＜新日付＞ [OPTION]

	ECHO 	OPTION = S : $$$.s file only
	ECHO 	OPTION = SRC : $$$.SRC file only
:END
