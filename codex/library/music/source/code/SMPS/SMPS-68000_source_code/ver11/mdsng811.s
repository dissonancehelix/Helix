;=======================================================;
;	    $$$SNG88.S  (Song Data)			;
;  			ORG. MDSNG118.S			;
;		'Sound-Source'				;
;		 for Mega Drive (68K)			;
;			Ver  1.1 / 1990.9.1		;
;				      By  H.Kubota	;
;=======================================================;

	public	S88

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
;=====< S88 CHANNEL TOTAL >=====;
FM88	EQU	6		; FM Channel Total
PSG88	EQU	3		; PSG Channel Total
;=========< S88 TEMPO >=========;
TP88	EQU	2		; Tempo
DL88	EQU	5		; Delay
;==========< S88 BIAS >=========;
FB880	EQU	0		; FM 0ch
FB881	EQU	0		; FM 1ch
FB882	EQU	0		; FM 2ch
FB884	EQU	0		; FM 4ch
FB885	EQU	0		; FM 5ch
FB886	EQU	0		; FM 6ch (if don't use PCM drum)
PB888	EQU	0		; PSG 80ch
PB88A	EQU	0		; PSG A0ch
PB88C	EQU	0		; PSG C0ch
;==========< S88 VOLM >=========;
FA880	EQU	10H	   	; FM 0ch
FA881	EQU	10H	    	; FM 1ch
FA882	EQU	10H	    	; FM 2ch
FA884	EQU	10H	    	; FM 4ch
FA885	EQU	10H	    	; FM 5ch
FA886	EQU	10H	    	; FM 6ch (if don't use PCM drum)
PA888	EQU	08H		; PSG 80ch
PA88A	EQU	08H		; PSG A0ch
PA88C	EQU	08H		; PSG C0ch
;==========< S88 ENVE >=========;
PE888	EQU	0		; PSG 80ch
PE88A	EQU	0		; PSG A0ch
PE88C	EQU	0		; PSG C0ch

;===============================================;
;						;
;		     HEADER			;
;						;
;===============================================;
S88:
	TDW	TIMB88,S88		; Voice Top Address
	DB	FM88,PSG88,TP88,DL88	; FM Total,PSG Total,Tempo,Delay

	TDW	TAB88D,S88		; PCM Drum Table Pointer
	DEFB	0,0			; Bias,Volm (Dummy)

	TDW	TAB880,S88		; FM 0ch Table Pointer
	DEFB	FB880,FA880	 	; Bias,Volm

	TDW	TAB881,S88		; FM 1ch Table Pointer
	DEFB	FB881,FA881		; Bias,Volm

	TDW	TAB882,S88		; FM 2ch Table Pointer
	DEFB	FB882,FA882		; Bias,Volm

	TDW	TAB884,S88		; FM 4ch Table Pointer
	DEFB	FB884,FA884		; Bias,Volm

	TDW	TAB885,S88		; FM 5ch Table Pointer
	DEFB	FB885,FA885		; Bias,Volm

;	TDW	TAB886,S88		; FM 6ch Table Pointer
;	DEFB	FB886,FA886		; Bias,Volm (if don't use PCM drum)

	TDW	TAB888,S88		; PSG 80ch Table Pointer
	DEFB	PB888,PA888,0,PE888	; Bias,Volm,Dummy,Enve

	TDW	TAB88A,S88		; PSG A0ch Table Pointer
	DEFB	PB88A,PA88A,0,PE88A	; Bias,Volm,Dummy,Enve

	TDW	TAB88C,S88		; PSG C0ch Table Pointer
	DEFB	PB88C,PA88C,0,PE88C	; Bias,Volm,Dummy,Enve

;===============================================;
;						;
;		   SONG TABLE			;
;						;
;===============================================;
;===============================================;
;		     FM 0ch			;
;===============================================;
TAB880	EQU	$
	DB	CMEND
;===============================================;
;		     FM 1ch			;
;===============================================;
TAB881	EQU	$
	DB	CMEND
;===============================================;
;		     FM 2ch			;
;===============================================;
TAB882	EQU	$
	DB	CMEND
;===============================================;
;		     FM 4ch			;
;===============================================;
TAB884	EQU	$
	DB	CMEND
;===============================================;
;		     FM 5ch			;
;===============================================;
TAB885	EQU	$
	DB	CMEND
;===============================================;
;	  FM 6ch (if don't use PCM drum)	;
;===============================================;
;TAB886	EQU	$
;	DB	CMEND
;===============================================;
;		     PSG 80ch			;
;===============================================;
TAB888	EQU	$
	DB	CMEND
;===============================================;
;		     PSG A0ch			;
;===============================================;
TAB88A	EQU	$
	DB	CMEND
;===============================================;
;		     PSG C0ch			;
;===============================================;
TAB88C	EQU	$
	DB	CMEND
;===============================================;
;		     PCM DRUM			;
;===============================================;
TAB88D	EQU	$
	DB	CMEND

;===============================================;
;						;
;		      VOICE			;
;						;
;===============================================;
TIMB88	EQU	$

