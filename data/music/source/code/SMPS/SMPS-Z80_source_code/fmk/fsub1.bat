echo off
echo/
echo ---- now writing these datas to file : %5  ---------
echo **/ proj. name:%1  / date:%2 / game name:%3 / parson:%4 /**

if "%1"=="" goto usage

sed -f subtmp.tm1 %5 > subtmp.tm2
copy subtmp.tm2 %5 > nul

goto end

:usage
	echo  / proj. name:%1  / date:%2 / game name:%3 / parson:%4 /FILE:%5 **
	echo  WHEN SET THESE DATAS , WRITE THESE DATAS THE FILE %7
:end

/FILE:%5 **
	echo  WHEN SET THESE DATAS , WRITE THESE DATAS THE FILE %7
:end

g subtmp.tm1>%5

goto end

:usage
	echo  / proj. name:%1  / date:%2 / game name:%3 / parson:%4 /FILE:%5 **
	echo  WHEN SET THESE DATAS , WRITE THESE DATAS THE FILE %7
:end

