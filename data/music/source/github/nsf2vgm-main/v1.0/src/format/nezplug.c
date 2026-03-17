#include "nezplug.h"

#include "neserr.h"
#include "handler.h"
#include "audiosys.h"
#include "songinfo.h"

#include "device/kmsnddev.h"
#include "m_hes.h"
#include "m_gbr.h"
#include "m_zxay.h"
#include "m_nsf.h"
#include "m_kss.h"
#include "m_nsd.h"
#include "m_sgc.h"
#include "../vgmwrite.h"


Uint8 chmask[0x80]={
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
};

/* Define ioview function pointers (NSF-only, others unused) */
int (*ioview_ioread_DEV_2A03   )(int a) = NULL;
int (*ioview_ioread_DEV_FDS    )(int a) = NULL;
int (*ioview_ioread_DEV_MMC5   )(int a) = NULL;
int (*ioview_ioread_DEV_VRC6   )(int a) = NULL;
int (*ioview_ioread_DEV_N106   )(int a) = NULL;
int (*ioview_ioread_DEV_DMG    )(int a) = NULL;
int (*ioview_ioread_DEV_HUC6230)(int a) = NULL;
int (*ioview_ioread_DEV_AY8910 )(int a) = NULL;
int (*ioview_ioread_DEV_SN76489)(int a) = NULL;
int (*ioview_ioread_DEV_SCC    )(int a) = NULL;
int (*ioview_ioread_DEV_OPL    )(int a) = NULL;
int (*ioview_ioread_DEV_OPLL   )(int a) = NULL;
int (*ioview_ioread_DEV_ADPCM  )(int a) = NULL;
int (*ioview_ioread_DEV_ADPCM2 )(int a) = NULL;
int (*ioview_ioread_DEV_MSX    )(int a) = NULL;

struct {
	char* title;
	char* artist;
	char* copyright;
	char detail[1024];
}songinfodata;

int (*memview_memread)(int a) = NULL;


static Uint GetWordLE(Uint8 *p)
{
	return p[0] | (p[1] << 8);
}

static Uint32 GetDwordLE(Uint8 *p)
{
	return p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24);
}
#define GetDwordLEM(p) (Uint32)((((Uint8 *)p)[0] | (((Uint8 *)p)[1] << 8) | (((Uint8 *)p)[2] << 16) | (((Uint8 *)p)[3] << 24)))


NEZ_PLAY* NEZNew()
{
	NEZ_PLAY *pNezPlay = (NEZ_PLAY*)XMALLOC(sizeof(NEZ_PLAY));

	if (pNezPlay != NULL) {
		XMEMSET(pNezPlay, 0, sizeof(NEZ_PLAY));
		pNezPlay->song = SONGINFO_New();
		if (!pNezPlay->song) {
			XFREE(pNezPlay);
			return 0;
		}
		pNezPlay->frequency = 48000;
		pNezPlay->channel = 1;
		pNezPlay->naf_type = NES_AUDIO_FILTER_NONE;
		pNezPlay->naf_prev[0] = pNezPlay->naf_prev[1] = 0x8000;
	}


	return pNezPlay;
}

void NEZDelete(NEZ_PLAY *pNezPlay)
{
	if (pNezPlay != NULL) {
		ioview_ioread_DEV_2A03   =NULL;
		ioview_ioread_DEV_FDS    =NULL;
		ioview_ioread_DEV_MMC5   =NULL;
		ioview_ioread_DEV_VRC6   =NULL;
		ioview_ioread_DEV_N106   =NULL;
		ioview_ioread_DEV_DMG    =NULL;
		ioview_ioread_DEV_HUC6230=NULL;
		ioview_ioread_DEV_AY8910 =NULL;
		ioview_ioread_DEV_SN76489=NULL;
		ioview_ioread_DEV_SCC    =NULL;
		ioview_ioread_DEV_OPL    =NULL;
		ioview_ioread_DEV_OPLL   =NULL;
		ioview_ioread_DEV_ADPCM  =NULL;
		ioview_ioread_DEV_ADPCM2 =NULL;
		ioview_ioread_DEV_MSX    =NULL;
		memview_memread=NULL;

		vgm_stop();
		NESTerminate(pNezPlay);
		NESAudioHandlerTerminate(pNezPlay);
		NESVolumeHandlerTerminate(pNezPlay);
		SONGINFO_Delete(pNezPlay->song);
		XFREE(pNezPlay);
	}
}


void NEZSetSongNo(NEZ_PLAY *pNezPlay, Uint uSongNo)
{
	if (pNezPlay == 0) return;
	SONGINFO_SetSongNo(pNezPlay->song, uSongNo);
}


void NEZSetFrequency(NEZ_PLAY *pNezPlay, Uint freq)
{
	if (pNezPlay == 0) return;
	NESAudioFrequencySet(pNezPlay, freq);
}

void NEZSetChannel(NEZ_PLAY *pNezPlay, Uint ch)
{
	if (pNezPlay == 0) return;
	NESAudioChannelSet(pNezPlay, ch);
}

void NEZStop(NEZ_PLAY *pNezPlay)
{
	vgm_stop();
	if (pNezPlay == 0) return;
}

void NEZReset(NEZ_PLAY *pNezPlay)
{
	vgm_stop();
	if (pNezPlay == 0) return;
	NESReset(pNezPlay);
	vgm_start(NEZGetSongNo(pNezPlay));
	NESVolume(pNezPlay, pNezPlay->volume);
}

void NEZSetFilter(NEZ_PLAY *pNezPlay, Uint filter)
{
	if (pNezPlay == 0) return;
	NESAudioFilterSet(pNezPlay, filter);
}

void NEZVolume(NEZ_PLAY *pNezPlay, Uint uVolume)
{
	if (pNezPlay == 0) return;
	pNezPlay->volume = uVolume;
	NESVolume(pNezPlay, pNezPlay->volume);
}

void NEZAPUVolume(NEZ_PLAY *pNezPlay, Int32 uVolume)
{
	if (pNezPlay == 0) return;
	if (pNezPlay->nsf == 0) return;
	((NSFNSF*)pNezPlay->nsf)->apu_volume = uVolume;
}

void NEZDPCMVolume(NEZ_PLAY *pNezPlay, Int32 uVolume)
{
	if (pNezPlay == 0) return;
	if (pNezPlay->nsf == 0) return;
	((NSFNSF*)pNezPlay->nsf)->dpcm_volume = uVolume;
}

void NEZRender(NEZ_PLAY *pNezPlay, void *bufp, Uint buflen)
{
	if (pNezPlay == 0) return;
	NESAudioRender(pNezPlay, (Int16*)bufp, buflen);
}

Uint NEZGetSongNo(NEZ_PLAY *pNezPlay)
{
	if (pNezPlay == 0) return 0;
	return SONGINFO_GetSongNo(pNezPlay->song);
}

Uint NEZGetSongStart(NEZ_PLAY *pNezPlay)
{
	if (pNezPlay == 0) return 0;
	return SONGINFO_GetStartSongNo(pNezPlay->song);
}

Uint NEZGetSongMax(NEZ_PLAY *pNezPlay)
{
	if (pNezPlay == 0) return 0;
	return SONGINFO_GetMaxSongNo(pNezPlay->song);
}

Uint NEZGetChannel(NEZ_PLAY *pNezPlay)
{
	if (pNezPlay == 0) return 1;
	return SONGINFO_GetChannel(pNezPlay->song);
}

Uint NEZGetFrequency(NEZ_PLAY *pNezPlay)
{
	if (pNezPlay == 0) return 1;
	return NESAudioFrequencyGet(pNezPlay);
}

Uint NEZLoad(NEZ_PLAY *pNezPlay, Uint8 *pData, Uint uSize)
{
	Uint ret = NESERR_NOERROR;
	ioview_ioread_DEV_2A03   =NULL;
	ioview_ioread_DEV_FDS    =NULL;
	ioview_ioread_DEV_MMC5   =NULL;
	ioview_ioread_DEV_VRC6   =NULL;
	ioview_ioread_DEV_N106   =NULL;
	ioview_ioread_DEV_DMG    =NULL;
	ioview_ioread_DEV_HUC6230=NULL;
	ioview_ioread_DEV_AY8910 =NULL;
	ioview_ioread_DEV_SN76489=NULL;
	ioview_ioread_DEV_SCC    =NULL;
	ioview_ioread_DEV_OPL    =NULL;
	ioview_ioread_DEV_OPLL   =NULL;
	ioview_ioread_DEV_ADPCM  =NULL;
	ioview_ioread_DEV_ADPCM2 =NULL;
	ioview_ioread_DEV_MSX    =NULL;
	memview_memread=NULL;

	songinfodata.title=NULL;
	songinfodata.artist=NULL;
	songinfodata.copyright=NULL;
	songinfodata.detail[0]=0;

	/* NSF-only converter - only support NSF format */
	if (!pNezPlay || !pData) {
		return NESERR_PARAMETER;
	}

	NESTerminate(pNezPlay);
	NESHandlerInitialize(pNezPlay->nrh, pNezPlay->nth);
	NESAudioHandlerInitialize(pNezPlay);

	if (uSize < 8)
	{
		NESTerminate(pNezPlay);
		return NESERR_FORMAT;
	}

	/* Check for NSF format: "NESM" + 0x1A */
	if (GetDwordLE(pData + 0) == GetDwordLEM("NESM") && pData[4] == 0x1A)
	{
		/* NSF */
		ret = NSFLoad(pNezPlay, pData, uSize);
		if (ret) {
			NESTerminate(pNezPlay);
			return ret;
		}
		return NESERR_NOERROR;
	}

	/* Unsupported format */
	NESTerminate(pNezPlay);
	return NESERR_FORMAT;
}


void NEZGetFileInfo(char **p1, char **p2, char **p3, char **p4)
{
	*p1 = songinfodata.title;
	*p2 = songinfodata.artist;
	*p3 = songinfodata.copyright;
	*p4 = songinfodata.detail;
}

