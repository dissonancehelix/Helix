;=======================================================;
;	    $$$SNG8F.S  (Song Data)			;
;  			ORG. MDSNG11F.S			;
;		'Sound-Source'				;
;		 for Mega Drive (68K)			;
;			Ver  1.1 / 1990.9.1		;
;				      By  H.Kubota	;
;=======================================================;

	public	S8F

	list off
	include	mdEQ11.LIB
	include	mdMCR11.LIB
	include	mdTB11.LIB
	list on

;===============================================;
;						;
;		     ASSIGN			;
;						;
;===============================================;
;=====< S8F CHANNEL TOTAL >=====;
FM8F	EQU	6		; FM Channel Total
PSG8F	EQU	3		; PSG Channel Total
;=========< S8F TEMPO >=========;
TP8F	EQU	2		; Tempo
DL8F	EQU	5		; Delay
;==========< S8F BIAS >=========;
FB8F0	EQU	0		; FM 0ch
FB8F1	EQU	0		; FM 1ch
FB8F2	EQU	0		; FM 2ch
FB8F4	EQU	0		; FM 4ch
FB8F5	EQU	0		; FM 5ch
FB8F6	EQU	0		; FM 6ch (if don't use PCM drum)
PB8F8	EQU	0		; PSG 80ch
PB8FA	EQU	0		; PSG A0ch
PB8FC	EQU	0		; PSG C0ch
;==========< S8F VOLM >=========;
FA8F0	EQU	10H	   	; FM 0ch
FA8F1	EQU	10H	    	; FM 1ch
FA8F2	EQU	10H	    	; FM 2ch
FA8F4	EQU	10H	    	; FM 4ch
FA8F5	EQU	10H	    	; FM 5ch
FA8F6	EQU	10H	    	; FM 6ch (if don't use PCM drum)
PA8F8	EQU	08H		; PSG 80ch
PA8FA	EQU	08H		; PSG A0ch
PA8FC	EQU	08H		; PSG C0ch
;==========< S8F ENVE >=========;
PE8F8	EQU	0		; PSG 80ch
PE8FA	EQU	0		; PSG A0ch
PE8FC	EQU	0		; PSG C0ch

;===============================================;
;						;
;		     HEADER			;
;						;
;===============================================;
S8F:
	TDW	TIMB8F,S8F		; Voice Top Address
	DB	FM8F,PSG8F,TP8F,DL8F	; FM Total,PSG Total,Tempo,Delay

	TDW	TAB8FD,S8F		; PCM Drum Table Pointer
	DEFB	0,0			; Bias,Volm (Dummy)

	TDW	TAB8F0,S8F		; FM 0ch Table Pointer
	DEFB	FB8F0,FA8F0	 	; Bias,Volm

	TDW	TAB8F1,S8F		; FM 1ch Table Pointer
	DEFB	FB8F1,FA8F1		; Bias,Volm

	TDW	TAB8F2,S8F		; FM 2ch Table Pointer
	DEFB	FB8F2,FA8F2		; Bias,Volm

	TDW	TAB8F4,S8F		; FM 4ch Table Pointer
	DEFB	FB8F4,FA8F4		; Bias,Volm

	TDW	TAB8F5,S8F		; FM 5ch Table Pointer
	DEFB	FB8F5,FA8F5		; Bias,Volm

;	TDW	TAB8F6,S8F		; FM 6ch Table Pointer
;	DEFB	FB8F6,FA8F6		; Bias,Volm (if don't use PCM drum)

	TDW	TAB8F8,S8F		; PSG 80ch Table Pointer
	DEFB	PB8F8,PA8F8,0,PE8F8	; Bias,Volm,Dummy,Enve

	TDW	TAB8FA,S8F		; PSG A0ch Table Pointer
	DEFB	PB8FA,PA8FA,0,PE8FA	; Bias,Volm,Dummy,Enve

	TDW	TAB8FC,S8F		; PSG C0ch Table Pointer
	DEFB	PB8FC,PA8FC,0,PE8FC	; Bias,Volm,Dummy,Enve

;===============================================;
;						;
;		   SONG TABLE			;
;						;
;===============================================;
;===============================================;
;		     FM 0ch			;
;===============================================;
TAB8F0	EQU	$
	DB	CMEND
;===============================================;
;		     FM 1ch			;
;===============================================;
TAB8F1	EQU	$
	DB	CMEND
;===============================================;
;		     FM 2ch			;
;===============================================;
TAB8F2	EQU	$
	DB	CMEND
;===============================================;
;		     FM 4ch			;
;===============================================;
TAB8F4	EQU	$
	DB	CMEND
;===============================================;
;		     FM 5ch			;
;===============================================;
TAB8F5	EQU	$
	DB	CMEND
;===============================================;
;	  FM 6ch (if don't use PCM drum)	;
;===============================================;
;TAB8F6	EQU	$
;	DB	CMEND
;===============================================;
;		     PSG 80ch			;
;===============================================;
TAB8F8	EQU	$
	DB	CMEND
;===============================================;
;		     PSG A0ch			;
;===============================================;
TAB8FA	EQU	$
	DB	CMEND
;===============================================;
;		     PSG C0ch			;
;===============================================;
TAB8FC	EQU	$
	DB	CMEND
;===============================================;
;		     PCM DRUM			;
;===============================================;
TAB8FD	EQU	$
	DB	CMEND

;===============================================;
;						;
;		      VOICE			;
;						;
;===============================================;
TIMB8F	EQU	$

