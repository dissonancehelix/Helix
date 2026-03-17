echo off
if "%2"=="src" goto skip
if "%2"=="SRC" goto skip
echo/
echo ------------ now file remaking : %1.MKF -----------------
sed -e s/13//g -e s/SNG/SNG8/g -e s/SNG8\./SNG./g -e s/8z/z/g %1.mkf > subtmp.tm1
copy subtmp.tm1 %1.mkf > nul

echo/
echo ------------ now file remaking : %1.LNK -----------------
sed -e s/13//g -e s/SNG/SNG8/g -e s,SNG8/,SNG/,g %1.lnk > subtmp.tm1
copy subtmp.tm1 %1.lnk > nul

echo/
echo ------------ now file remaking : ALL.LNK -----------------
sed -e s/13//g -e s/SNG/SNG8/g all.lnk > subtmp.tm1
copy subtmp.tm1 all.lnk > nul

echo/
echo ------------ now file remaking : %1.BAT -----------------
sed -e s/13//g %1.bat > subtmp.tm1
copy subtmp.tm1 %1.bat > nul

echo/
echo ------------ now file remaking : %1Z.BAT -----------------
sed -e s/13//g %1Z.bat > subtmp.tm1
copy subtmp.tm1 %1Z.bat > nul

echo/
echo ------------ now file remaking : %1Z.MAC -----------------
sed -e s/13//g %1Z.mac > subtmp.tm1
copy subtmp.tm1 %1Z.mac > nul

echo/
echo ------------ now file remaking : %1SE.S -----------------
sed -e s/setb13/setb/g %1se.s > subtmp.tm1
copy subtmp.tm1 %1se.s > nul

:skip
echo/
echo ------------ now file remaking : %1INT.SRC -----------------
sed -e s/setb13/setb/g %1int.src >subtmp.tm1
copy subtmp.tm1 %1int.src > nul

