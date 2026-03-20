echo off
if	"%1"==""	goto usage

	cd ..
	md %1 
	cd %1
	COMMAND /C \m5\Z80\fmk\fcopy %1 %2

:------------ このパラメータ(year.manth.day proj-name parson)
:						を書き換えてください。---------
:	command /c \m5\Z80\fmk\fsub %1 year.manth.day proj-name parson %2
	command /c \m5\Z80\fmk\fsub %1 1990.12.25 xxxxxxxxxxxxx Y.YYYYY %2
	command /c \m5\Z80\fmk\mkfsub %1 %2
	del subtmp.*
	goto end
:usage
	ECHO	FMK PRJ [mode]
	echo	  mode = src then only .src   .lib

:end
echo ----------------------   終了しました　-----------------------
