;=======================================================;
;	    $$$SE2.S  (S.E. Data)			;
;  			ORG. MDSE112.S			;
;		'Sound-Source'				;
;		 for Mega Drive (68K)			;
;			Ver  1.1 / 1990.9.1		;
;				      By  H.Kubota	;
;=======================================================;

	list off
	include mdEQ11.LIB
	include mdMCR11.LIB
	include mdTB11.LIB
	list on

	PUBLIC	SB0,SB1,SB2,SB3,SB4,SB5,SB6,SB7
	PUBLIC	SB8,SB9,SBA,SBB,SBC,SBD,SBE,SBF

;=======================================;
;		   SB0			;
;=======================================;
SB0:
	TDW	TIMBB0,SB0		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB00,SB0		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB00	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB0	EQU	$

;=======================================;
;		   SB1			;
;=======================================;
SB1:
	TDW	TIMBB1,SB1		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB10,SB1		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB10	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB1	EQU	$

;=======================================;
;		   SB2			;
;=======================================;
SB2:
	TDW	TIMBB2,SB2		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB20,SB2		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB20	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB2	EQU	$

;=======================================;
;		   SB3			;
;=======================================;
SB3:
	TDW	TIMBB3,SB3		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB30,SB3		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB30	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB3	EQU	$

;=======================================;
;		   SB4			;
;=======================================;
SB4:
	TDW	TIMBB4,SB4		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB40,SB4		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB40	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB4	EQU	$

;=======================================;
;		   SB5			;
;=======================================;
SB5:
	TDW	TIMBB5,SB5		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB50,SB5		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB50	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB5	EQU	$

;=======================================;
;		   SB6			;
;=======================================;
SB6:
	TDW	TIMBB6,SB6		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB60,SB6		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB60	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB6	EQU	$

;=======================================;
;		   SB7			;
;=======================================;
SB7:
	TDW	TIMBB7,SB7		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB70,SB7		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB70	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB7	EQU	$

;=======================================;
;		   SB8			;
;=======================================;
SB8:
	TDW	TIMBB8,SB8		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB80,SB8		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB80	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB8	EQU	$

;=======================================;
;		   SB9			;
;=======================================;
SB9:
	TDW	TIMBB9,SB9		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABB90,SB9		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABB90	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBB9	EQU	$

;=======================================;
;		   SBA			;
;=======================================;
SBA:
	TDW	TIMBBA,SBA		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABBA0,SBA		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABBA0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBBA	EQU	$

;=======================================;
;		   SBB			;
;=======================================;
SBB:
	TDW	TIMBBB,SBB		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABBB0,SBB		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABBB0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBBB	EQU	$

;=======================================;
;		   SBC			;
;=======================================;
SBC:
	TDW	TIMBBC,SBC		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABBC0,SBC		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABBC0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBBC	EQU	$

;=======================================;
;		   SBD			;
;=======================================;
SBD:
	TDW	TIMBBD,SBD		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABBD0,SBD		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABBD0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBBD	EQU	$

;=======================================;
;		   SBE			;
;=======================================;
SBE:
	TDW	TIMBBE,SBE		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABBE0,SBE		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABBE0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBBE	EQU	$

;=======================================;
;		   SBF			;
;=======================================;
SBF:
	TDW	TIMBBF,SBF		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABBF0,SBF		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABBF0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBBF	EQU	$

