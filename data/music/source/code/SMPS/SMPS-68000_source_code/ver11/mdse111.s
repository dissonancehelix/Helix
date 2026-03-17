;=======================================================;
;	    $$$SE1.S  (S.E. Data)			;
;  			ORG. MDSE111.S			;
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

	PUBLIC	SA0,SA1,SA2,SA3,SA4,SA5,SA6,SA7
	PUBLIC	SA8,SA9,SAA,SAB,SAC,SAD,SAE,SAF

;=======================================;
;		   SA0			;
;=======================================;
SA0:

	TDW	TIMBA0,SA0		; Voice Top Address
	DB	1,2			; Base,Use Channel Total

	DB	80H,080H		; Flag,Channel
	TDW	TABA00,SA0		; FM 1ch Table Pointer
	DEFB	00H,003H	 	; Bias,Volm

	DB	80H,0A0H		; Flag,Channel
	TDW	TABA01,SA0		; FM 1ch Table Pointer
	DEFB	00H,003H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA00	EQU	$
	DB	NL,2
	DB	FDT,10
	DB	EV,3
TA00	EQU	$
	DB	0C1H,3,0C3H,0C5H
	DB	PVADD,2
	DB	CMBIAS,-1
	DB	CMREPT,0,4
	JDW	TA00
TA01	EQU	$
	DB	0C1H,3,0C3H,0C5H
	DB	PVADD,2
	DB	CMBIAS,1
	DB	CMREPT,0,2
	JDW	TA01
	DB	CMEND

TABA01	EQU	$
	DB	EV,3
TA001	EQU	$
	DB	0C1H,2,0C3H,0C5H
	DB	PVADD,2
	DB	CMBIAS,-1
	DB	CMREPT,0,6
	JDW	TA001
TA011	EQU	$
	DB	0C1H,2,0C3H,0C5H
	DB	PVADD,2
	DB	CMBIAS,1
	DB	CMREPT,0,4
	JDW	TA011
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA0	EQU	$

;=======================================;
;		   SA1			;
;=======================================;
SA1:
	TDW	TIMBA1,SA1		; Voice Top Address
	DB	1,2			; Base,Use Channel Total

	DB	80H,080H		; Flag,Channel
	TDW	TABA10,SA1		; FM 1ch Table Pointer
	DEFB	0E8H,002H	 	; Bias,Volm

	DB	80H,0A0H		; Flag,Channel
	TDW	TABA11,SA1		; FM 1ch Table Pointer
	DEFB	0E8H,002H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA11	EQU	$
	DB	FDT,1
TABA10	EQU	$
TA100	EQU	$
	DB	0DDH,2,0DBH,0D9H
	DB	CMREPT,0,3
	JDW	TA100
TA101	EQU	$
	DB	0DBH,0D9H,0D7H
	DB	CMREPT,0,3
	JDW	TA101
TA102	EQU	$
	DB	0D9H,0D7H,0D5H
	DB	CMREPT,0,3
	JDW	TA102
TA103	EQU	$
	DB	0DBH,0D9H,0D7H
	DB	CMREPT,0,3
	JDW	TA103

	DB	CMJUMP
	JDW	TA100

	DB	CMEND

;------------< Voice Data >-------------;
TIMBA1	EQU	$

;=======================================;
;		   SA2			;
;=======================================;
SA2:
	TDW	TIMBA2,SA2		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABA20,SA2		; FM 1ch Table Pointer
	DEFB	00H,006H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA20	EQU	$
	DB	FEV,0
TA20	EQU	$
	DB	0C4H,1,NL
	DB	CMREPT,0,10H
	JDW	TA20
	DB	CMJUMP
	JDW	TA20

;------------< Voice Data >-------------;
TIMBA2	EQU	$
	CNF	1,7
	MD	2,0,1,0,2,0,1,0
	RSAR	0,31,0,31,0,31,0,31
	D1R	0,0,0,0
	D2R	0,0,0,0
	RRL	15,0,15,0,15,0,15,0
	TL	27,50,40,0

;=======================================;
;		   SA3			;
;=======================================;
SA3:
	TDW	TIMBA3,SA3		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,005H		; Flag,Channel
	TDW	TABA30,SA3		; FM 1ch Table Pointer
	DEFB	24H,002H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA30	EQU	$
	DB	FEV,0
	DB	LFO,68H,30H
TABA31	EQU	$
	DB	FVR,1,2,0F8H,0FFH
	DB	0ADH,2AH
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA3	EQU	$
	CNF	4,7
	MD	2,0,1,0,2,0,1,0
	RSAR	0,31,0,0BH,0,31,0,0BH
	D1R	0,8,0,8
	D2R	1,0EH,1,0EH
	RRL	15,0,15,1,15,0,15,1
	TL	27,50,40,0

;=======================================;
;		   SA4			;
;=======================================;
SA4:
	TDW	TIMBA4,SA4		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABA40,SA4		; FM 1ch Table Pointer
	DEFB	0F4H,000H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA40	EQU	$
	DB	FEV,0
TA40	EQU	$
	DB	0A0H,60h
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA4	EQU	$
	CNF	3,7
	MD	2,5,1,3,1,5,1,5
	RSAR	0,0CH,0,0CH,0,12H,0,12H
	D1R	0EH,0,0EH,0CH
	D2R	0,0,0,0EH
	RRL	15,4,15,0,15,5,15,3
	TL	15H,13H,1CH,0

;=======================================;
;		   SA5			;
;=======================================;
SA5:
	TDW	TIMBA5,SA5		; Voice Top Address
	DB	1,2			; Base,Use Channel Total

	DB	80H,0A0H		; Flag,Channel
	TDW	TABA50,SA5		; FM 1ch Table Pointer
	DEFB	0F4H,000H	 	; Bias,Volm

	DB	80H,0C0H		; Flag,Channel
	TDW	TABA51,SA5		; FM 1ch Table Pointer
	DEFB	0F4H,000H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA50	EQU	$
	DB	EV,1
	DB	FVR,1,1,50H,17H
	DB	09BH,0Ah
TA50	EQU	$
	DB	0A3H,4,PVADD,2
	DB	CMREPT,0,6
	JDW	TA50
	DB	CMEND
TABA51	EQU	$
	DB	EV,1
	DB	FVR,2,1,20H,10H,CMNOIS,NOIS7
	DB	0C4H,0AH
TA51	EQU	$
	DB	0C2H,02H,PVADD,1
	DB	CMREPT,0,12
	JDW	TA51
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA5	EQU	$
	CNF	0,7
	MD	15,0,15,0,15,0,15,0
	RSAR	0,31,0,31,0,31,0,14
	D1R	0,0,0,10
	D2R	0,0,0,25
	RRL	15,0,15,0,15,0,15,1
	TL	7,7,7,0

;=======================================;
;		   SA6			;
;=======================================;
SA6:
	TDW	TIMBA6,SA6		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABA60,SA6		; FM 1ch Table Pointer
	DEFB	00H,004H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA60	EQU	$
	DB	FEV,0
TBA6	EQU	$
	DB	0A0h,14
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA6	EQU	$
	CNF	0,5
	MD	3,0,0,7,1,3,0,0
	RSAR	0,31,0,31,1,31,1,31
	D1R	3,3,3,2
	D2R	1,2,2,3
	RRL	15,10,15,2,15,2,15,5
	TL	30,25,22,0

;=======================================;
;		   SA7			;
;=======================================;
SA7:
	TDW	TIMBA7,SA7		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,0C0H		; Flag,Channel
	TDW	TABA70,SA7		; FM 1ch Table Pointer
	DEFB	00H,000H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA70	EQU	$
	DB	CMNOIS,NOIS7
	DB	FVR,1,1,7,2
	DB	EXCOM,S_PSE,ON
TA70	EQU	$
	DB	0A0H,4,CMBIAS,1,CMREPT,0,20H
	JDW	TA70
	DB	20
	DB	EXCOM,S_PSE,OFF
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA7	EQU	$

;=======================================;
;		   SA8			;
;=======================================;
SA8:
	TDW	TIMBA8,SA8		; Voice Top Address
	DB	1,2			; Base,Use Channel Total

	DB	80H,4			; Flag,Channel
	TDW	TABA81,SA8		; FM 1ch Table Pointer
	DEFB	0F2H,008H	 	; Bias,Volm

	DB	80H,5			; Flag,Channel
	TDW	TABA80,SA8		; FM 1ch Table Pointer
	DEFB	0F2H,008H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA80	EQU	$
	DB	FEV,0
	DB	CMJUMP
	JDW	TA80
TABA81	EQU	$
	DB	FEV,0
TA80	EQU	$
	DB	0B0H,2,CMTAB,0AEh,1,CMTAB,CMBIAS,-1
	DB	CMREPT,0,20H
	JDW	TA80
	DB	CMBIAS,20H
TA81	EQU	$
	DB	090H,2,NL,1
	DB	CMREPT,0,5
	JDW	TA81
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA8	EQU	$
;-----------< Voice Data 0 >------------;
	CNF	3,7
	MD	12,3,9,3,0,3,1,3
	RSAR	3,31,0,31,0,31,3,31
	D1R	4,5,4,1
	D2R	4,4,4,2
	RRL	15,15,15,0,15,1,15,10
	TL	41,32,15,0
;-----------< Voice Data 1 >------------;
	CNF	5,7
	MD	1,0,2,0,0,0,1,0
	RSAR	0,31,0,14,0,14,0,14
	D1R	7,31,31,31
	D2R	0,0,0,0
	RRL	15,1,15,0,15,0,15,0
	TL	23,13,12,12

;=======================================;
;		   SA9			;
;=======================================;
SA9:
	TDW	TIMBA9,SA9		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,5			; Flag,Channel
	TDW	TABA90,SA9		; FM 1ch Table Pointer
	DEFB	00H,006H	 	; Bias,Volm

;------------< Table Data >-------------;
TABA90	EQU	$
	DB	FEV,0
	DB	NL,1
	DB	FVR,0,1,0D0H,0FFH
	DB	0C5H,0FH
	DB	CMEND

;------------< Voice Data >-------------;
TIMBA9	EQU	$
	CNF	0,7
	MD	15,0,15,0,15,0,15,0
	RSAR	0,31,0,31,0,31,0,14
	D1R	0,0,0,11H
	D2R	0,0,0,13H
	RRL	15,0,15,0,15,0,15,1
	TL	7,7,7,0

;=======================================;
;		   SAA			;
;=======================================;
SAA:
	TDW	TIMBAA,SAA		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,0C0H		; Flag,Channel
	TDW	TABAA0,SAA		; FM 1ch Table Pointer
	DEFB	00H,001H	 	; Bias,Volm

;------------< Table Data >-------------;
TABAA0	EQU	$
	DB	FVR,1,1,0F0H,8,CMNOIS,NOIS7
	DB	0B0H,4,0CAH,4
TAA0	EQU	$
	DB	0C0h,1,PVADD,1,CMREPT,0,8
	JDW	TAA0
	DB	CMEND

;------------< Voice Data >-------------;
TIMBAA	EQU	$

;=======================================;
;		   SAB			;
;=======================================;
SAB:
	TDW	TIMBAB,SAB		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,0C0H		; Flag,Channel
	TDW	TABAB0,SAB		; FM 1ch Table Pointer
	DEFB	00H,000H	 	; Bias,Volm

;------------< Table Data >-------------;
TABAB0	EQU	$
	DB	EV,1
	DB	FVR,3,1,20H,8,CMNOIS,NOIS7
	DB	0A2H,3,0A6H,4
TAB0	EQU	$
	DB	0B2h,9,CMBIAS,2,PVADD,3,CMREPT,0,2
	JDW	TAB0
	DB	CMEND

;------------< Voice Data >-------------;
TIMBAB	EQU	$

;=======================================;
;		   SAC			;
;=======================================;
SAC:
	TDW	TIMBAC,SAC		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,05H			; Flag,Channel
	TDW	TABAC0,SAC		; FM 1ch Table Pointer
	DEFB	000H,002H	 	; Bias,Volm

;------------< Table Data >-------------;
TABAC0	EQU	$
	DB	FEV,0
	DB	08dH,02cH
	DB	CMEND

;------------< Voice Data >-------------;
TIMBAC	EQU	$
	CNF	4,7
	MD	2,0,0,0,1,0,1,0
	RSAR	0,31,0,31,0,31,0,31
	D1R	0,14,25,16
	D2R	0,12,0,15
	RRL	15,0,15,14,15,15,15,15
	TL	5,0,0,0

;=======================================;
;		   SAD			;
;=======================================;
SAD:
	TDW	TIMBAD,SAD		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,0C0H		; Flag,Channel
	TDW	TABAD0,SAD		; FM 1ch Table Pointer
	DEFB	00H,000H	 	; Bias,Volm

;------------< Table Data >-------------;
TABAD0	EQU	$
	DB	EV,2
	DB	FVR,1,1,0F0H,8,CMNOIS,NOIS7
TAD0	EQU	$
	DB	0B0H,4,NL,2
	DB	CMREPT,0,3
	JDW	TAD0
	DB	CMEND

;------------< Voice Data >-------------;
TIMBAD	EQU	$

;=======================================;
;		   SAE			;
;=======================================;
SAE:
	TDW	TIMBAE,SAE		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,0C0H		; Flag,Channel
	TDW	TABAE0,SAE		; FM 1ch Table Pointer
	DEFB	00H,004H	 	; Bias,Volm

;------------< Table Data >-------------;
TABAE0	EQU	$
TBAE	EQU	$
	DB	GN4,L2,FN4
	DB	CMJUMP
	JDW	TBAE

;------------< Voice Data >-------------;
TIMBAE	EQU	$
	CNF	0,5
	MD	3,0,0,7,1,3,0,0
	RSAR	0,31,0,31,1,31,1,31
	D1R	3,3,3,2
	D2R	1,2,2,3
	RRL	15,10,15,2,15,2,15,5
	TL	30,25,22,0

;=======================================;
;		   SAF			;
;=======================================;
SAF:
	TDW	TIMBAF,SAF		; Voice Top Address
	DB	1,1			; Base,Use Channel Total

	DB	80H,C0H			; Flag,Channel
	TDW	TABAF0,SAF		; FM 1ch Table Pointer
	DEFB	00H,000H	 	; Bias,Volm

;------------< Table Data >-------------;
TABAF0	EQU	$
	DB	CMNOIS,NOIS3
TAF0	EQU	$
	DB	GN4,L2,FN4
	DB	CMJUMP
	JDW	TAF0

;------------< Voice Data >-------------;
TIMBAF	EQU	$
	CNF	5,7
	MD	0,0,1,1,1,1,1,1
	RSAR	3,31,0,0DH,0,0DH,0,0DH
	D1R	1,10H,10H,10H
	D2R	1,12H,12H,12H
	RRL	15,0,15,1,15,1,15,1
	TL	31,0,0,0

