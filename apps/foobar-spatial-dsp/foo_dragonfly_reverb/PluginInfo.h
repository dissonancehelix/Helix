/*
 * Dragonfly Reverb, a hall-style reverb plugin
 * Copyright (c) 2018 Michael Willis, Rob van den Berg
 * GPL v3 — see LICENSE
 *
 * Stripped of DPF plugin framework macros for use as a standalone DSP class.
 */
#ifndef PLUGIN_INFO_H_INCLUDED
#define PLUGIN_INFO_H_INCLUDED

#include <cstdint>
#include "Param.hpp"

enum Parameters
{
    paramDry = 0,
    paramEarly,
    paramLate,
    paramSize,
    paramWidth,
    paramPredelay,
    paramDiffuse,
    paramLowCut,
    paramLowXover,
    paramLowMult,
    paramHighCut,
    paramHighXover,
    paramHighMult,
    paramSpin,
    paramWander,
    paramDecay,
    paramEarlySend,
    paramModulation,
    paramCount
};

static const Param PARAMS[paramCount] = {
  {paramDry,        "Dry Level",   "dry_level",    0.0f,   100.0f,   "%"},
  {paramEarly,      "Early Level", "early_level",  0.0f,   100.0f,   "%"},
  {paramLate,       "Late Level",  "late_level",   0.0f,   100.0f,   "%"},
  {paramSize,       "Size",        "size",        10.0f,    60.0f,   "m"},
  {paramWidth,      "Width",       "width",       50.0f,   150.0f,   "%"},
  {paramPredelay,   "Predelay",    "delay",        0.0f,   100.0f,  "ms"},
  {paramDiffuse,    "Diffuse",     "diffuse",      0.0f,   100.0f,   "%"},
  {paramLowCut,     "Low Cut",     "low_cut",      0.0f,   200.0f,  "Hz"},
  {paramLowXover,   "Low Cross",   "low_xo",     200.0f,  1200.0f,  "Hz"},
  {paramLowMult,    "Low Mult",    "low_mult",     0.5f,     2.5f,   "X"},
  {paramHighCut,    "High Cut",    "high_cut",  1000.0f, 16000.0f,  "Hz"},
  {paramHighXover,  "High Cross",  "high_xo",   1000.0f, 16000.0f,  "Hz"},
  {paramHighMult,   "High Mult",   "high_mult",    0.2f,     1.2f,   "X"},
  {paramSpin,       "Spin",        "spin",         0.0f,    10.0f,  "Hz"},
  {paramWander,     "Wander",      "wander",       0.0f,    40.0f,  "ms"},
  {paramDecay,      "Decay",       "decay",        0.1f,    10.0f,   "s"},
  {paramEarlySend,  "Early Send",  "early_send",   0.0f,   100.0f,   "%"},
  {paramModulation, "Modulation",  "modulation",   0.0f,   100.0f,   "%"}
};

static const int NUM_BANKS = 5;
static const int PRESETS_PER_BANK = 5;

typedef struct {
  const char *name;
  const float params[paramCount];
} Preset;

typedef struct {
  const char *name;
  const Preset presets[PRESETS_PER_BANK];
} Bank;

static const Bank banks[NUM_BANKS] = {
  {
    "Rooms", {                   // dry, early, late, size, width, delay, diffuse, low cut, low xo, low mult, high cut, high xo, high mult, spin, wander, decay, e. send, modulation
      {"Bright Room",            { 80.0f,  10.0f, 20.0f, 10.0f,  90.0f,   4.0f,    90.0f,     4.0f,    500,     0.80f,    16000,    7900,      0.75f,  1.0f, 25.0f,     0.6f,    20.0f,    30.0f }},
      {"Clear Room",             { 80.0f,  10.0f, 20.0f, 10.0f,  90.0f,   4.0f,    90.0f,     4.0f,    500,     0.90f,    13000,    5800,      0.50f,  1.0f, 25.0f,     0.6f,    20.0f,    30.0f }},
      {"Dark Room",              { 80.0f,  10.0f, 20.0f, 10.0f,  90.0f,   4.0f,    50.0f,     4.0f,    500,     1.20f,     7300,    4900,      0.35f,  1.0f, 25.0f,     0.7f,    20.0f,    30.0f }},
      {"Small Chamber",          { 80.0f,  10.0f, 20.0f, 16.0f,  80.0f,   8.0f,    70.0f,     4.0f,    500,     1.10f,     8200,    5500,      0.35f,  1.2f, 10.0f,     0.8f,    20.0f,    20.0f }},
      {"Large Chamber",          { 80.0f,  10.0f, 20.0f, 20.0f,  80.0f,   8.0f,    90.0f,     4.0f,    500,     1.30f,     7000,    4900,      0.25f,  1.8f, 12.0f,     1.0f,    20.0f,    20.0f }},
    }
  },
  {
    "Studios", {
      {"Acoustic Studio",        { 80.0f,  10.0f, 20.0f, 12.0f,  90.0f,   8.0f,    75.0f,     4.0f,    450,     1.50f,     7600,    4900,      0.80f,  2.5f,  7.0f,     0.8f,    20.0f,    20.0f }},
      {"Electric Studio",        { 80.0f,  10.0f, 20.0f, 12.0f,  90.0f,   6.0f,    45.0f,     4.0f,    250,     1.25f,     7600,    5800,      0.70f,  2.5f,  7.0f,     0.9f,    20.0f,    30.0f }},
      {"Percussion Studio",      { 80.0f,  10.0f, 20.0f, 12.0f,  90.0f,   6.0f,    30.0f,    20.0f,    200,     1.75f,     5800,    5200,      0.45f,  2.5f,  7.0f,     0.7f,    20.0f,    10.0f }},
      {"Piano Studio",           { 80.0f,  10.0f, 20.0f, 12.0f,  80.0f,   8.0f,    40.0f,    20.0f,    600,     1.50f,     8200,    5800,      0.50f,  2.8f, 10.0f,     0.7f,    20.0f,    15.0f }},
      {"Vocal Studio",           { 80.0f,  10.0f, 20.0f, 12.0f,  90.0f,   0.0f,    60.0f,     4.0f,    400,     1.20f,     5800,    5200,      0.40f,  2.5f,  7.0f,     0.8f,    20.0f,    10.0f }},
    }
  },
  {
    "Small Halls", {
      {"Small Bright Hall",      { 80.0f,  10.0f, 20.0f, 24.0f,  80.0f,  12.0f,    90.0f,     4.0f,    400,     1.10f,    11200,    6250,      0.75f,  2.5f, 13.0f,     1.3f,    20.0f,    15.0f }},
      {"Small Clear Hall",       { 80.0f,  10.0f, 20.0f, 24.0f, 100.0f,   4.0f,    90.0f,     4.0f,    500,     1.30f,     7600,    5500,      0.50f,  3.3f, 15.0f,     1.3f,    20.0f,    15.0f }},
      {"Small Dark Hall",        { 80.0f,  10.0f, 20.0f, 24.0f, 100.0f,  12.0f,    60.0f,     4.0f,    500,     1.50f,     5800,    4000,      0.35f,  2.5f, 10.0f,     1.5f,    20.0f,    15.0f }},
      {"Small Percussion Hall",  { 80.0f,  10.0f, 20.0f, 24.0f,  80.0f,  12.0f,    40.0f,    20.0f,    250,     2.00f,     5200,    4000,      0.35f,  2.0f, 13.0f,     1.1f,    20.0f,    10.0f }},
      {"Small Vocal Hall",       { 80.0f,  10.0f, 20.0f, 24.0f,  80.0f,   4.0f,    60.0f,     4.0f,    500,     1.25f,     6250,    5200,      0.35f,  3.1f, 15.0f,     1.2f,    20.0f,    10.0f }},
    }
  },
  {
    "Medium Halls", {
      {"Medium Bright Hall",     { 80.0f,  10.0f, 20.0f, 30.0f, 100.0f,  18.0f,    90.0f,     4.0f,    400,     1.25f,    10000,    6400,      0.60f,  2.9f, 15.0f,     1.6f,    20.0f,    15.0f }},
      {"Medium Clear Hall",      { 80.0f,  10.0f, 20.0f, 30.0f, 100.0f,   8.0f,    90.0f,     4.0f,    500,     1.50f,     7600,    5500,      0.50f,  2.9f, 15.0f,     1.7f,    20.0f,    15.0f }},
      {"Medium Dark Hall",       { 80.0f,  10.0f, 20.0f, 30.0f, 100.0f,  18.0f,    60.0f,     4.0f,    500,     1.75f,     5800,    4000,      0.40f,  2.9f, 15.0f,     1.8f,    20.0f,    15.0f }},
      {"Medium Percussion Hall", { 80.0f,  10.0f, 20.0f, 30.0f,  80.0f,  12.0f,    40.0f,    20.0f,    300,     2.00f,     5200,    4000,      0.35f,  2.0f, 12.0f,     1.2f,    20.0f,    10.0f }},
      {"Medium Vocal Hall",      { 80.0f,  10.0f, 20.0f, 32.0f,  80.0f,   8.0f,    75.0f,     4.0f,    600,     1.50f,     5800,    5200,      0.40f,  2.8f, 16.0f,     1.3f,    20.0f,    10.0f }},
    }
  },
  {
    "Large Halls", {
      {"Large Bright Hall",      { 80.0f,  10.0f, 20.0f, 40.0f, 100.0f,  20.0f,    90.0f,     4.0f,    400,     1.50f,     8200,    5800,      0.50f,  2.1f, 20.0f,     2.5f,    20.0f,    15.0f }},
      {"Large Clear Hall",       { 80.0f,  10.0f, 20.0f, 40.0f, 100.0f,  12.0f,    80.0f,     4.0f,    550,     2.00f,     8200,    5200,      0.40f,  2.1f, 20.0f,     2.8f,    20.0f,    15.0f }},
      {"Large Dark Hall",        { 80.0f,  10.0f, 20.0f, 40.0f, 100.0f,  20.0f,    60.0f,     4.0f,    600,     2.50f,     6250,    2800,      0.20f,  2.1f, 20.0f,     3.0f,    20.0f,    15.0f }},
      {"Large Vocal Hall",       { 80.0f,  10.0f, 20.0f, 40.0f,  80.0f,  12.0f,    80.0f,     4.0f,    700,     2.25f,     6250,    4600,      0.30f,  2.1f, 17.0f,     2.4f,    20.0f,    10.0f }},
      {"Great Hall",             { 80.0f,  10.0f, 20.0f, 50.0f,  90.0f,  20.0f,    95.0f,     4.0f,    750,     2.50f,     5500,    4000,      0.30f,  2.6f, 22.0f,     3.8f,    20.0f,    15.0f }},
    }
  }
};

/* Default: Large Clear Hall */
static const int DEFAULT_BANK   = 4;
static const int DEFAULT_PRESET = 1;

#endif
