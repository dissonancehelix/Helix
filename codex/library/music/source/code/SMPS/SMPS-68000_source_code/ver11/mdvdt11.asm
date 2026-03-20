;=======================================================;
;	    $$$VDT.ASM  (Sound Voice Data 68K File)	;
;  			ORG. MDVDT11.ASM		;
;		'Sound-Source'				;
;		 for Mega Drive (68K)			;
;			Ver  1.1 / 1990.9.1		;
;				      By  H.Kubota	;
;=======================================================;

	public	pcm_vdt_top
	public	pcm_vdt_end

	include mdEQ11.LIB

	org	voice_top

;=======================================;
;	      INCLUDE FILE		;
;=======================================;
pcm_vdt_top	equ	$
	include	pcm\mdVT11.HHH
pcm_vdt_end	equ	$

