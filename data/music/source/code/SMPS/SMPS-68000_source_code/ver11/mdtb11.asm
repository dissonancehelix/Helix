;=======================================================;
;	    $$$TB.ASM  (Sound Adddress & Data Table)	;
;  			ORG. MDTB11.ASM			;
;		'Sound-Source'				;
;		 for Mega Drive (68K)			;
;			Ver  1.1 / 1990.9.1		;
;				      By  H.Kubota	;
;=======================================================;

	list off
	include mdEQ11.lib
	include mdMCR11.lib
	include mdTB11.lib
	list on

	public 	adrtb
	public	bgmtb,envetb,prtb
	extern	S81,S82,S83,S84,S85,S86,S87,S88,S89,S8A,S8B,S8C,S8D,S8E,S8F
	extern	S90,S91,S92,S93,S94,S95,S96,S97

	if	prg
	extern  sound
	extern  setb
	extern  backtb
	org	sound_top
	else
sound	equ	control_top
setb	equ	se_top
backtb	equ	setb+(seend-sestrt+1)*4
	org	song_top
	endif

;=======================================;
;					;
;	     TABLE.ASM START		;
;					;
;=======================================;


;=======================================;
;					;
;	      ADDRESS TABLE		;
;					;
;=======================================;

adrtb:
	dc.l	prtb			; priority
	dc.l	backtb			; back se
	dc.l	bgmtb			; bgm
	dc.l	setb			; s.e
	dc.l	prtb			; dmy (vibr)
	dc.l	envetb			; envelope
	dc.l	sestrt			; se start no.
	dc.l    sound			; 7th fix (for sound editor)

;=======================================;
;					;
;	      ENVELOPE TABLE		;
;					;
;=======================================;
envetb:
	DL	EV1,EV2,EV3,EV4,EV5,EV6
	DL	EV7,EV8

EV1	EQU	$
	DB	0,0,0,1,1,1,2,2,2,3,3,3
	DB	4,4,4,5,5,5,6,6,6
	DB	7,TBEND
EV2	EQU	$
	DB	0,2,4,6,8,10H,TBEND
EV3	EQU	$
	DB	0,0,1,1,3,3,4,5,TBEND
EV4	EQU	$
	DB	0,0,2,3,4,4,5,5,5
	DB	6,TBEND			;HIHAT(THEN CMGATE,3)
EV6	EQU	$
	DB	4,4,4,4,3,3,3,3,2,2,2,2
	DB	1,1,1,1
EV5	EQU	$
	DB	0,0,0,0,0,0,0,0,0,0
	DB	1,1,1,1,1,1,1,1,1,1
	DB	1,1,1,1,2,2,2,2,2,2
	DB	2,2,3,3,3,3,3,3,3,3
	DB	4,TBEND
EV7	EQU	$
	DB	2,TBEND			;HIHAT
EV8	EQU	$
	DB	0,0,0,0,0,1,1,1,1,1
	DB	2,2,2,2,2,2,3,3,3,3,3
	DB	4,4,4,4,4,5,5,5,5,5
	DB	6,6,6,6,6,7,7,7,TBEND

;=======================================;
;					;
;	    SONG ADDRESS TABLE		;
;					;
;=======================================;
bgmtb:
	DL	S81			; 81
	DL	S82			; 82
	DL	S83			; 83
	DL	S84			; 84
	DL	S85			; 85
	DL	S86			; 86
	DL	S81			; 87
	DL	S81			; 88
	DL	S81			; 89
	DL	S81			; 8A
	DL	S81			; 8B
	DL	S81			; 8C
	DL	S81			; 8D
	DL	S81			; 8E
	DL	S81			; 8F

;=======================================;
;					;
;	      PRIORITY TABLE		;
;					;
;=======================================;
prtb:
	if	lstno>081H-1
		DB	PR81
	endif
	if	lstno>082H-1
		DB	PR82
	endif
	if	lstno>083H-1
		DB	PR83
	endif
	if	lstno>084H-1
		DB	PR84
	endif
	if	lstno>085H-1
		DB	PR85
	endif
	if	lstno>086H-1
		DB	PR86
	endif
	if	lstno>087H-1
		DB	PR87
	endif
	if	lstno>088H-1
		DB	PR88
	endif
	if	lstno>089H-1
		DB	PR89
	endif
	if	lstno>08AH-1
		DB	PR8A
	endif
	if	lstno>08BH-1
		DB	PR8B
	endif
	if	lstno>08CH-1
		DB	PR8C
	endif
	if	lstno>08DH-1
		DB	PR8D
	endif
	if	lstno>08EH-1
		DB	PR8E
	endif
	if	lstno>08FH-1
		DB	PR8F
	endif
	if	lstno>090H-1
		DB	PR90
	endif
	if	lstno>091H-1
		DB	PR91
	endif
	if	lstno>092H-1
		DB	PR92
	endif
	if	lstno>093H-1
		DB	PR93
	endif
	if	lstno>094H-1
		DB	PR94
	endif
	if	lstno>095H-1
		DB	PR95
	endif
	if	lstno>096H-1
		DB	PR96
	endif
	if	lstno>097H-1
		DB	PR97
	endif
	if	lstno>098H-1
		DB	PR98
	endif
	if	lstno>099H-1
		DB	PR99
	endif
	if	lstno>09AH-1
		DB	PR9A
	endif
	if	lstno>09BH-1
		DB	PR9B
	endif
	if	lstno>09CH-1
		DB	PR9C
	endif
	if	lstno>09DH-1
		DB	PR9D
	endif
	if	lstno>09EH-1
		DB	PR9E
	endif
	if	lstno>09FH-1
		DB	PR9F
	endif
	if	lstno>0A0H-1
		DB	PRA0
	endif
	if	lstno>0A1H-1
		DB	PRA1
	endif
	if	lstno>0A2H-1
		DB	PRA2
	endif
	if	lstno>0A3H-1
		DB	PRA3
	endif
	if	lstno>0A4H-1
		DB	PRA4
	endif
	if	lstno>0A5H-1
		DB	PRA5
	endif
	if	lstno>0A6H-1
		DB	PRA6
	endif
	if	lstno>0A7H-1
		DB	PRA7
	endif
	if	lstno>0A8H-1
		DB	PRA8
	endif
	if	lstno>0A9H-1
		DB	PRA9
	endif
	if	lstno>0AAH-1
		DB	PRAA
	endif
	if	lstno>0ABH-1
		DB	PRAB
	endif
	if	lstno>0ACH-1
		DB	PRAC
	endif
	if	lstno>0ADH-1
		DB	PRAD
	endif
	if	lstno>0AEH-1
		DB	PRAE
	endif
	if	lstno>0AFH-1
		DB	PRAF
	endif
	if	lstno>0B0H-1
		DB	PRB0
	endif
	if	lstno>0B1H-1
		DB	PRB1
	endif
	if	lstno>0B2H-1
		DB	PRB2
	endif
	if	lstno>0B3H-1
		DB	PRB3
	endif
	if	lstno>0B4H-1
		DB	PRB4
	endif
	if	lstno>0B5H-1
		DB	PRB5
	endif
	if	lstno>0B6H-1
		DB	PRB6
	endif
	if	lstno>0B7H-1
		DB	PRB7
	endif
	if	lstno>0B8H-1
		DB	PRB8
	endif
	if	lstno>0B9H-1
		DB	PRB9
	endif
	if	lstno>0BAH-1
		DB	PRBA
	endif
	if	lstno>0BBH-1
		DB	PRBB
	endif
	if	lstno>0BCH-1
		DB	PRBC
	endif
	if	lstno>0BDH-1
		DB	PRBD
	endif
	if	lstno>0BEH-1
		DB	PRBE
	endif
	if	lstno>0BFH-1
		DB	PRBF
	endif
	if	lstno>0C0H-1
		DB	PRC0
	endif
	if	lstno>0C1H-1
		DB	PRC1
	endif
	if	lstno>0C2H-1
		DB	PRC2
	endif
	if	lstno>0C3H-1
		DB	PRC3
	endif
	if	lstno>0C4H-1
		DB	PRC4
	endif
	if	lstno>0C5H-1
		DB	PRC5
	endif
	if	lstno>0C6H-1
		DB	PRC6
	endif
	if	lstno>0C7H-1
		DB	PRC7
	endif
	if	lstno>0C8H-1
		DB	PRC8
	endif
	if	lstno>0C9H-1
		DB	PRC9
	endif
	if	lstno>0CAH-1
		DB	PRCA
	endif
	if	lstno>0CBH-1
		DB	PRCB
	endif
	if	lstno>0CCH-1
		DB	PRCC
	endif
	if	lstno>0CDH-1
		DB	PRCD
	endif
	if	lstno>0CEH-1
		DB	PRCE
	endif
	if	lstno>0CFH-1
		DB	PRCF
	endif
	if	lstno>0D0H-1
		DB	PRD0
	endif
	if	lstno>0D1H-1
		DB	PRD1
	endif
	if	lstno>0D2H-1
		DB	PRD2
	endif
	if	lstno>0D3H-1
		DB	PRD3
	endif
	if	lstno>0D4H-1
		DB	PRD4
	endif
	if	lstno>0D5H-1
		DB	PRD5
	endif
	if	lstno>0D6H-1
		DB	PRD6
	endif
	if	lstno>0D7H-1
		DB	PRD7
	endif
	if	lstno>0D8H-1
		DB	PRD8
	endif
	if	lstno>0D9H-1
		DB	PRD9
	endif
	if	lstno>0DAH-1
		DB	PRDA
	endif
	if	lstno>0DBH-1
		DB	PRDB
	endif
	if	lstno>0DCH-1
		DB	PRDC
	endif
	if	lstno>0DDH-1
		DB	PRDD
	endif
	if	lstno>0DEH-1
		DB	PRDE
	endif
	if	lstno>0DFH-1
		DB	PRDF
	endif
	if	lstno>0E0H-1
		DB	PRE0
	endif
	if	lstno>0E1H-1
		DB	PRE1
	endif
	if	lstno>0E2H-1
		DB	PRE2
	endif
	if	lstno>0E3H-1
		DB	PRE3
	endif
	if	lstno>0E4H-1
		DB	PRE4
	endif
	if	lstno>0E5H-1
		DB	PRE5
	endif
	if	lstno>0E6H-1
		DB	PRE6
	endif
	if	lstno>0E7H-1
		DB	PRE7
	endif
	if	lstno>0E8H-1
		DB	PRE8
	endif
	if	lstno>0E9H-1
		DB	PRE9
	endif
	if	lstno>0EAH-1
		DB	PREA
	endif
	if	lstno>0EBH-1
		DB	PREB
	endif
	if	lstno>0ECH-1
		DB	PREC
	endif
	if	lstno>0EDH-1
		DB	PRED
	endif
	if	lstno>0EEH-1
		DB	PREE
	endif
	if	lstno>0EFH-1
		DB	PREF
	endif

;=======================================;
;	      END OF FILE		;
;=======================================;

