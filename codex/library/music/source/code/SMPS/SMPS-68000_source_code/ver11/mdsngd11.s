;=======================================================;
;	    $$$SNG8D.S  (Song Data)			;
;  			ORG. MDSNG11D.S			;
;		'Sound-Source'				;
;		 for Mega Drive (68K)			;
;			Ver  1.1 / 1990.9.1		;
;				      By  H.Kubota	;
;=======================================================;

	public	S8D

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
;=====< S8D CHANNEL TOTAL >=====;
FM8D	EQU	6		; FM Channel Total
PSG8D	EQU	3		; PSG Channel Total
;=========< S8D TEMPO >=========;
TP8D	EQU	2		; Tempo
DL8D	EQU	5		; Delay
;==========< S8D BIAS >=========;
FB8D0	EQU	0		; FM 0ch
FB8D1	EQU	0		; FM 1ch
FB8D2	EQU	0		; FM 2ch
FB8D4	EQU	0		; FM 4ch
FB8D5	EQU	0		; FM 5ch
FB8D6	EQU	0		; FM 6ch (if don't use PCM drum)
PB8D8	EQU	0		; PSG 80ch
PB8DA	EQU	0		; PSG A0ch
PB8DC	EQU	0		; PSG C0ch
;==========< S8D VOLM >=========;
FA8D0	EQU	10H	   	; FM 0ch
FA8D1	EQU	10H	    	; FM 1ch
FA8D2	EQU	10H	    	; FM 2ch
FA8D4	EQU	10H	    	; FM 4ch
FA8D5	EQU	10H	    	; FM 5ch
FA8D6	EQU	10H	    	; FM 6ch (if don't use PCM drum)
PA8D8	EQU	08H		; PSG 80ch
PA8DA	EQU	08H		; PSG A0ch
PA8DC	EQU	08H		; PSG C0ch
;==========< S8D ENVE >=========;
PE8D8	EQU	0		; PSG 80ch
PE8DA	EQU	0		; PSG A0ch
PE8DC	EQU	0		; PSG C0ch

;===============================================;
;						;
;		     HEADER			;
;						;
;===============================================;
S8D:
	TDW	TIMB8D,S8D		; Voice Top Address
	DB	FM8D,PSG8D,TP8D,DL8D	; FM Total,PSG Total,Tempo,Delay

	TDW	TAB8DD,S8D		; PCM Drum Table Pointer
	DEFB	0,0			; Bias,Volm (Dummy)

	TDW	TAB8D0,S8D		; FM 0ch Table Pointer
	DEFB	FB8D0,FA8D0	 	; Bias,Volm

	TDW	TAB8D1,S8D		; FM 1ch Table Pointer
	DEFB	FB8D1,FA8D1		; Bias,Volm

	TDW	TAB8D2,S8D		; FM 2ch Table Pointer
	DEFB	FB8D2,FA8D2		; Bias,Volm

	TDW	TAB8D4,S8D		; FM 4ch Table Pointer
	DEFB	FB8D4,FA8D4		; Bias,Volm

	TDW	TAB8D5,S8D		; FM 5ch Table Pointer
	DEFB	FB8D5,FA8D5		; Bias,Volm

;	TDW	TAB8D6,S8D		; FM 6ch Table Pointer
;	DEFB	FB8D6,FA8D6		; Bias,Volm (if don't use PCM drum)

	TDW	TAB8D8,S8D		; PSG 80ch Table Pointer
	DEFB	PB8D8,PA8D8,0,PE8D8	; Bias,Volm,Dummy,Enve

	TDW	TAB8DA,S8D		; PSG A0ch Table Pointer
	DEFB	PB8DA,PA8DA,0,PE8DA	; Bias,Volm,Dummy,Enve

	TDW	TAB8DC,S8D		; PSG C0ch Table Pointer
	DEFB	PB8DC,PA8DC,0,PE8DC	; Bias,Volm,Dummy,Enve

;===============================================;
;						;
;		   SONG TABLE			;
;						;
;===============================================;
;===============================================;
;		     FM 0ch			;
;===============================================;
TAB8D0	EQU	$
	DB	CMEND
;===============================================;
;		     FM 1ch			;
;===============================================;
TAB8D1	EQU	$
	DB	CMEND
;===============================================;
;		     FM 2ch			;
;===============================================;
TAB8D2	EQU	$
	DB	CMEND
;===============================================;
;		     FM 4ch			;
;===============================================;
TAB8D4	EQU	$
	DB	CMEND
;===============================================;
;		     FM 5ch			;
;===============================================;
TAB8D5	EQU	$
	DB	CMEND
;===============================================;
;	  FM 6ch (if don't use PCM drum)	;
;===============================================;
;TAB8D6	EQU	$
;	DB	CMEND
;===============================================;
;		     PSG 80ch			;
;===============================================;
TAB8D8	EQU	$
	DB	CMEND
;===============================================;
;		     PSG A0ch			;
;===============================================;
TAB8DA	EQU	$
	DB	CMEND
;===============================================;
;		     PSG C0ch			;
;===============================================;
TAB8DC	EQU	$
	DB	CMEND
;===============================================;
;		     PCM DRUM			;
;===============================================;
TAB8DD	EQU	$
	DB	CMEND

;===============================================;
;						;
;		      VOICE			;
;						;
;===============================================;
TIMB8D	EQU	$

