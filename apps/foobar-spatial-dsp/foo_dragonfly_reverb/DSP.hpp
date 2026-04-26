/*
 * Dragonfly Reverb, a hall-style reverb plugin
 * Copyright (c) 2018 Michael Willis, Rob van den Berg
 * GPL v3
 *
 * Modified for foo_dragonfly_reverb: DPF plugin framework removed.
 */
#ifndef DRAGONFLY_REVERB_DSP_HPP_INCLUDED
#define DRAGONFLY_REVERB_DSP_HPP_INCLUDED

#include "AbstractDSP.hpp"
#include "PluginInfo.h"
#include "freeverb/earlyref.hpp"
#include "freeverb/zrev2.hpp"

class DragonflyReverbDSP : public AbstractDSP {
public:
  DragonflyReverbDSP(double sampleRate);
  float getParameterValue(uint32_t index) const;
  void  setParameterValue(uint32_t index, float value);
  void run(const float** inputs, float** outputs, uint32_t frames);
  void sampleRateChanged(double newSampleRate);
  void mute();

private:
  float oldParams[paramCount];
  float newParams[paramCount];

  float dryLevel   = 0.0f;
  float earlyLevel = 0.0f;
  float early_send = 0.0f;
  float lateLevel  = 0.0f;

  fv3::earlyref_f early;
  fv3::zrev2_f    late;

  static const uint32_t BUFFER_SIZE = 256;
  float early_out_buffer[2][BUFFER_SIZE];
  float late_in_buffer[2][BUFFER_SIZE];
  float late_out_buffer[2][BUFFER_SIZE];
};

#endif
