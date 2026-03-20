echo off
if "%1"=="" goto usage
	cd \m5\z80\%1
  command /c \m5\z80\\src\rewrite 13 14 \m5\z80\ver13\m5int13.src %1int.src
	 sub s/%1setb/m5setb13/g \m5\z80\ver13\m5int13.src>TEMP1
	 copy temp1 \m5\z80\ver13\m5int13.src
  command /c \m5\z80\fmk\rewrite 14 15 \m5\z80\ver13\m5cnt13.src %1cnt.src
  command /c \m5\z80\fmk\rewrite 13 14 \m5\z80\ver13\m5cmd13.src %1cmd.src
   command /c \m5\z80\fmk\rewrite 13 14 \m5\z80\ver13\m5fmdr13.src %1fmdr.src
   command /c \m5\z80\fmk\rewrite 13 14 \m5\z80\ver13\m5psg13.src %1psg.src
   command /c \m5\z80\fmk\rewrite 12 13  \m5\z80\ver13\m5tb13.src  %1tb.src
   command /c \m5\z80\fmk\rewrite 9 10 \m5\z80\ver13\m5setb13.src %1setb.src
   command /c \m5\z80\fmk\rewrite 9 10 \m5\z80\ver13\m5eq13.lib   %1eq.lib
   command /c \m5\z80\fmk\rewrite 9 10 \m5\z80\ver13\m5tb13.lib   %1tb.lib
   command /c \m5\z80\fmk\rewrite 9 10 \m5\z80\ver13\m5mcr13.lib  %1mcr.lib 
	del temp1
	cd \m5\z80\ver13
	goto end
	
	

:usage
	echo 	usage ------  recopy [directry name]
	echo 	新しいソースファイルの内容を　ｖｅｒ１３の
	echo 	ファイルに移します。
:end
