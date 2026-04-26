#pragma once
#include <afxwin.h>
#include <afxcmn.h>      // CSliderCtrl and other common controls
// Suppress unused MM subsystems but keep MMSYSTEM_TIME (timeGetTime)
// so that pfc/timers.h can resolve it.
#define MMNODRV
#define MMNOSOUND
#define MMNOWAVE
#define MMNOMIDI
#define MMNOAUX
#define MMNOMIXER
#define MMNOJOYSTICK
#define MMNOSTRETCHDIB
#include <mmsystem.h>
