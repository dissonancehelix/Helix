echo off
echo/
echo M5INT13.SRC Å® %1INT.SRC
copy	\m5\z80\ver13\m5int13.src	%1int.src
echo/
echo M5CNT13.SRC Å® %1CNT.SRC
copy	\m5\z80\ver13\m5cnt13.src	%1cnt.src
echo/
echo M5CMD13.SRC Å® %1CMD.SRC
copy	\m5\z80\ver13\m5cmd13.src	%1cmd.src
echo/
echo M5FMDR13,SRC Å® %1FMDR.SRC
copy	\m5\z80\ver13\m5fmdr13.src	%1fmdr.src
echo/
echo M5PSG13.SRC Å® %1PSG.SRC
copy	\m5\z80\ver13\m5psg13.src	%1psg.src
echo/
echo M5PCM13.SRC Å® %1PCM.SRC
copy	\m5\z80\ver13\m5pcm13.src	%1pcm.src
echo/
echo M5TB13.SRC Å® %1TB.SRC
copy	\m5\z80\ver13\m5tb13.src       	%1tb.src
echo/
echo M5SETB13.SRC Å® %1SETB.SRC
copy	\m5\z80\ver13\m5setb13.src	%1setb.src
echo/
echo M5EQ13.LIB Å® %1EQ.LIB
copy	\m5\z80\ver13\m5eq13.lib      	%1eq.lib
echo/
echo M5TB13.LIB Å® %1TB.LIB
copy	\m5\z80\ver13\m5tb13.lib      	%1tb.lib
echo/
echo M5MCR13.LIB Å® %1MCR.LIB
copy	\m5\z80\ver13\m5mcr13.lib      	%1mcr.lib 
echo/
if "%2"=="src" goto skip
if "%2"=="SRC" goto skip
echo M5SE13.S Å® %1SE.S
copy	\m5\z80\ver13\m5se13.s         	%1se.s  
echo/
echo M5SE113.S Å® %1SE1.S
copy	\m5\z80\ver13\m5se113.s        	%1se1.s  
echo/
echo M5SE213.S Å® %1SE2.S
copy	\m5\z80\ver13\m5se213.s        	%1se2.s  
echo/
echo M5SE313.S Å® %1SE3.S
copy	\m5\z80\ver13\m5se313.s        	%13se.s  
echo/
echo M5SNG113.S Å® %1SNG81.S
copy	\m5\z80\ver13\m5sng113.s       	%1sng81.s
echo/
echo M5SNG213.S Å® %1SNG82.S
copy	\m5\z80\ver13\m5sng213.s       	%1sng82.s
echo/
echo M5SNG313.S Å® %1SNG83.S
copy	\m5\z80\ver13\m5sng313.s       	%1sng83.s
echo/
echo M5SNG413.S Å® %1SNG84.S
copy	\m5\z80\ver13\m5sng413.s       	%1sng84.s
echo/
echo M5SNG513.S Å® %1SNG85.S
copy	\m5\z80\ver13\m5sng513.s       	%1sng85.s
echo/
echo M5SNG613.S Å® %1SNG86.S
copy	\m5\z80\ver13\m5sng613.s       	%1sng86.s
echo/
echo M5SNG713.S Å® %1SNG87.S
copy	\m5\z80\ver13\m5sng713.s       	%1sng87.s
echo/
echo M5SNG813.S Å® %1SNG88.S
copy	\m5\z80\ver13\m5sng813.s       	%1sng88.s
echo/
echo M5SNG913.S Å® %1SNG89.S
copy	\m5\z80\ver13\m5sng913.s       	%1sng89.s
echo/
echo M5SNGA13.S Å® %1SNG8A.S
copy	\m5\z80\ver13\m5snga13.s       	%1sng8a.s
echo/
echo M5SNGB13.S Å® %1SNG8B.S
copy	\m5\z80\ver13\m5sngb13.s       	%1sng8b.s
echo/
echo M5SNGC13.S Å® %1SNG8C.S
copy	\m5\z80\ver13\m5sngc13.s       	%1sng8c.s
echo/
echo M5SNGD13.S Å® %1SNG8D.S
copy	\m5\z80\ver13\m5sngd13.s       	%1sng8d.s
echo/
echo M5SNGE13.S Å® %1SNG8E.S
copy	\m5\z80\ver13\m5snge13.s       	%1sng8e.s
echo/
echo M5SNGF13.S Å® %1SNG8F.S
copy	\m5\z80\ver13\m5sngf13.s        %1sng8f.s
echo/
echo voice1.S Å® 
copy	\m5\z80\ver13\voice1.s
echo/

echo M513.BAT Å® %1.BAT
copy	\m5\z80\ver13\m513.bat         	%1.bat
echo/
echo M5Z13.BAT Å® %1Z.BAT
copy	\m5\z80\ver13\m5z13.bat        	%1z.bat
echo/
echo M5Z13.MAC Å® %1Z.MAC
copy	\m5\z80\ver13\m5z13.mac        	%1z.mac
echo/
echo M513.DOC Å® %1.DOC
copy	\m5\z80\ver13\m513.doc        	%1.doc
echo/

echo M513.MKF Å® %1.MKF
copy	\m5\z80\ver13\m513.mkf   	%1.mkf
echo/
echo M513.LIB Å® %1.LNK
copy	\m5\z80\ver13\m513.lnk   	%1.lnk
echo/
echo ALL.LNK Å® ALL.LNK
copy	\m5\z80\ver13\all.lnk
echo/
echo makerule.def Å® makerule.def
copy	\m5\z80\ver13\makerule.def
echo/

echo C.CMD Å® C.CMD
copy	\m5\z80\ver13\C.CMD
echo/
echo ERX68K.MAC Å® ERX68K.MAC
copy	\m5\z80\ver13\ERX68K.MAC
:skip
