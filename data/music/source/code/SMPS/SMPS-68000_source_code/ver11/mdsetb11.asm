;=======================================================;
;	    $$$SETB.ASM  (Sound S.E. Address Table)	;
;  			ORG. MDSETB11.ASM		;
;		'Sound-Source'				;
;		 for Mega Drive (68K)			;
;			Ver  1.1 / 1990.9.1		;
;				      By  H.Kubota	;
;=======================================================;

	public	setb,backtb

	extern	SA0,SA1,SA2,SA3,SA4,SA5,SA6,SA7,SA8
	extern	SA9,SAA,SAB,SAC,SAD,SAE,SAF
	extern	SD0,SD1,SD2,SD3

	include mdEQ11.lib

	ifz	prg
	org	se_top
	endif

;=======================================;
;					;
;	    S.E. ADDRESS TABLE		;
;					;
;=======================================;
setb:
	if	seend>0A0H-1
		DL	SA0
	endif
	if	seend>0A1H-1
		DL	SA1
	endif
	if	seend>0A2H-1
		DL	SA2
	endif
	if	seend>0A3H-1
		DL	SA3
	endif
	if	seend>0A4H-1
		DL	SA4
	endif
	if	seend>0A5H-1
		DL	SA5
	endif
	if	seend>0A6H-1
		DL	SA6
	endif
	if	seend>0A7H-1
		DL	SA7
	endif
	if	seend>0A8H-1
		DL	SA8
	endif
	if	seend>0A9H-1
		DL	SA9
	endif
	if	seend>0AAH-1
		DL	SAA
	endif
	if	seend>0ABH-1
		DL	SAB
	endif
	if	seend>0ACH-1
		DL	SAC
	endif
	if	seend>0ADH-1
		DL	SAD
	endif
	if	seend>0AEH-1
		DL	SAE
	endif
	if	seend>0AFH-1
		DL	SAF
	endif
	if	seend>0B0H-1
		DL	SB0
	endif
	if	seend>0B1H-1
		DL	SB1
	endif
	if	seend>0B2H-1
		DL	SB2
	endif
	if	seend>0B3H-1
		DL	SB3
	endif
	if	seend>0B4H-1
		DL	SB4
	endif
	if	seend>0B5H-1
		DL	SB5
	endif
	if	seend>0B6H-1
		DL	SB6
	endif
	if	seend>0B7H-1
		DL	SB7
	endif
	if	seend>0B8H-1
		DL	SB8
	endif
	if	seend>0B9H-1
		DL	SB9
	endif
	if	seend>0BAH-1
		DL	SBA
	endif
	if	seend>0BBH-1
		DL	SBB
	endif
	if	seend>0BCH-1
		DL	SBC
	endif
	if	seend>0BDH-1
		DL	SBD
	endif
	if	seend>0BEH-1
		DL	SBE
	endif
	if	seend>0BFH-1
		DL	SBF
	endif
	if	seend>0C0H-1
		DL	SC0
	endif
	if	seend>0C1H-1
		DL	SC1
	endif
	if	seend>0C2H-1
		DL	SC2
	endif
	if	seend>0C3H-1
		DL	SC3
	endif
	if	seend>0C4H-1
		DL	SC4
	endif
	if	seend>0C5H-1
		DL	SC5
	endif
	if	seend>0C6H-1
		DL	SC6
	endif
	if	seend>0C7H-1
		DL	SC7
	endif
	if	seend>0C8H-1
		DL	SC8
	endif
	if	seend>0C9H-1
		DL	SC9
	endif
	if	seend>0CAH-1
		DL	SCA
	endif
	if	seend>0CBH-1
		DL	SCB
	endif
	if	seend>0CCH-1
		DL	SCC
	endif
	if	seend>0CDH-1
		DL	SCD
	endif
	if	seend>0CEH-1
		DL	SCE
	endif
	if	seend>0CFH-1
		DL	SCF
	endif

backtb:
		DL	SD0
		DL	SD1
		DL	SD2
		DL	SD3

