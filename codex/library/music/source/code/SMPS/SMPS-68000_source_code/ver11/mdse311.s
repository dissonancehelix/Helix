;=======================================================;
;	    $$$SE3.S  (S.E. Data)			;
;  			ORG. MDSE113.S			;
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


	PUBLIC	SC0,SC1,SC2,SC3,SC4,SC5,SC6,SC7
	PUBLIC	SC8,SC9,SCA,SCB,SCC,SCD,SCE,SCF

;=======================================;
;		   SC0			;
;=======================================;
SC0:
	TDW	TIMBC0,SC0		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC00,SC0		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC00	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC0	EQU	$

;=======================================;
;		   SC1			;
;=======================================;
SC1:
	TDW	TIMBC1,SC1		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC10,SC1		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC10	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC1	EQU	$

;=======================================;
;		   SC2			;
;=======================================;
SC2:
	TDW	TIMBC2,SC2		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC20,SC2		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC20	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC2	EQU	$

;=======================================;
;		   SC3			;
;=======================================;
SC3:
	TDW	TIMBC3,SC3		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC30,SC3		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC30	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC3	EQU	$

;=======================================;
;		   SC4			;
;=======================================;
SC4:
	TDW	TIMBC4,SC4		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC40,SC4		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC40	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC4	EQU	$

;=======================================;
;		   SC5			;
;=======================================;
SC5:
	TDW	TIMBC5,SC5		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC50,SC5		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC50	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC5	EQU	$

;=======================================;
;		   SC6			;
;=======================================;
SC6:
	TDW	TIMBC6,SC6		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC60,SC6		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC60	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC6	EQU	$

;=======================================;
;		   SC7			;
;=======================================;
SC7:
	TDW	TIMBC7,SC7		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC70,SC7		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC70	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC7	EQU	$

;=======================================;
;		   SC8			;
;=======================================;
SC8:
	TDW	TIMBC8,SC8		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC80,SC8		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC80	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC8	EQU	$

;=======================================;
;		   SC9			;
;=======================================;
SC9:
	TDW	TIMBC9,SC9		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABC90,SC9		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABC90	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBC9	EQU	$

;=======================================;
;		   SCA			;
;=======================================;
SCA:
	TDW	TIMBCA,SCA		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABCA0,SCA		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABCA0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBCA	EQU	$

;=======================================;
;		   SCB			;
;=======================================;
SCB:
	TDW	TIMBCB,SCB		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABCB0,SCB		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABCB0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBCB	EQU	$

;=======================================;
;		   SCC			;
;=======================================;
SCC:
	TDW	TIMBCC,SCC		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABCC0,SCC		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABCC0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBCC	EQU	$

;=======================================;
;		   SCD			;
;=======================================;
SCD:
	TDW	TIMBCD,SCD		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABCD0,SCD		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABCD0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBCD	EQU	$

;=======================================;
;		   SCE			;
;=======================================;
SCE:
	TDW	TIMBCE,SCE		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABCE0,SCE		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABCE0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBCE	EQU	$

;=======================================;
;		   SCF			;
;=======================================;
SCF:
	TDW	TIMBCF,SCF		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABCF0,SCF		; FM 1ch Table Pointer
	DB	00H,000H	 	; Bias,Volm
;------------< Table Data >-------------;
TABCF0	EQU	$
	DB	CMEND

;------------< Voice Data >-------------;
TIMBCF	EQU	$

