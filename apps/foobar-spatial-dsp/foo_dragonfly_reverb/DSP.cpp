/*
 * Dragonfly Reverb, a hall-style reverb plugin
 * Copyright (c) 2018 Michael Willis, Rob van den Berg
 * GPL v3
 *
 * Modified for foo_dragonfly_reverb: DPF plugin framework removed.
 * d_isNotEqual() replaced with direct float inequality.
 * ScopedDenormalDisable sourced from local MSVC-compatible header.
 */

#include "ScopedDenormalDisable.hpp"
#include "PluginInfo.h"
#include "DSP.hpp"

DragonflyReverbDSP::DragonflyReverbDSP(double sampleRate) {
  early.loadPresetReflection(FV3_EARLYREF_PRESET_1);
  early.setMuteOnChange(false);
  early.setdryr(0);
  early.setwet(0);
  early.setwidth(0.8f);
  early.setLRDelay(0.3f);
  early.setLRCrossApFreq(750, 4);
  early.setDiffusionApFreq(150, 4);
  early.setSampleRate(sampleRate);
  early_send = 0.20f;

  late.setMuteOnChange(false);
  late.setwet(0);
  late.setdryr(0);
  late.setwidth(1.0f);
  late.setSampleRate(sampleRate);

  for (uint32_t param = 0; param < paramCount; param++) {
    newParams[param] = banks[DEFAULT_BANK].presets[DEFAULT_PRESET].params[param];
    oldParams[param] = -1.0f;  // force initial apply
  }
}

float DragonflyReverbDSP::getParameterValue(uint32_t index) const {
  if (index < paramCount) return newParams[index];
  return 0.0f;
}

void DragonflyReverbDSP::setParameterValue(uint32_t index, float value) {
  if (index < paramCount) newParams[index] = value;
}

void DragonflyReverbDSP::run(const float** inputs, float** outputs, uint32_t frames) {
  const ScopedDenormalDisable sdd;
  for (uint32_t index = 0; index < paramCount; index++) {
    if (oldParams[index] != newParams[index]) {
      oldParams[index] = newParams[index];
      float value = newParams[index];

      switch(index) {
        case           paramDry: dryLevel        = (value / 100.0f); break;
        case         paramEarly: earlyLevel      = (value / 100.0f); break;
        case          paramLate: lateLevel       = (value / 100.0f); break;
        case          paramSize: early.setRSFactor  (value / 10.0f);
                                 late.setRSFactor   (value / 80.0f);  break;
        case         paramWidth: early.setwidth     (value / 100.0f);
                                 late.setwidth      (value / 100.0f); break;
        case      paramPredelay:
          if (value < 0.1f) value = 0.1f;
          late.setPreDelay(value);
          break;
        case       paramDiffuse: late.setidiffusion1(value / 140.0f);
                                 late.setapfeedback (value / 140.0f); break;
        case       paramLowCut:  early.setoutputhpf (value);
                                 late.setoutputhpf  (value);          break;
        case     paramLowXover:  late.setxover_low  (value);          break;
        case      paramLowMult:  late.setrt60_factor_low(value);      break;
        case      paramHighCut:  early.setoutputlpf (value);
                                 late.setoutputlpf  (value);          break;
        case    paramHighXover:  late.setxover_high (value);          break;
        case     paramHighMult:  late.setrt60_factor_high(value);     break;
        case          paramSpin: late.setspin       (value);          break;
        case        paramWander: late.setwander     (value);          break;
        case         paramDecay: late.setrt60       (value);          break;
        case     paramEarlySend: early_send       = (value / 100.0f); break;
        case    paramModulation: {
          float mod = value == 0.0f ? 0.001f : value / 100.0f;
          late.setspinfactor(mod);
          late.setlfofactor (mod);
          break;
        }
      }
    }
  }

  for (uint32_t offset = 0; offset < frames; offset += BUFFER_SIZE) {
    uint32_t buffer_frames = (frames - offset < BUFFER_SIZE) ? (frames - offset) : BUFFER_SIZE;

    early.processreplace(
      const_cast<float*>(inputs[0] + offset),
      const_cast<float*>(inputs[1] + offset),
      early_out_buffer[0],
      early_out_buffer[1],
      buffer_frames);

    for (uint32_t i = 0; i < buffer_frames; i++) {
      late_in_buffer[0][i] = early_send * early_out_buffer[0][i] + inputs[0][offset + i];
      late_in_buffer[1][i] = early_send * early_out_buffer[1][i] + inputs[1][offset + i];
    }

    late.processreplace(
      const_cast<float*>(late_in_buffer[0]),
      const_cast<float*>(late_in_buffer[1]),
      late_out_buffer[0],
      late_out_buffer[1],
      buffer_frames);

    for (uint32_t i = 0; i < buffer_frames; i++) {
      outputs[0][offset + i] = dryLevel * inputs[0][offset + i];
      outputs[1][offset + i] = dryLevel * inputs[1][offset + i];
    }
    if (earlyLevel > 0.0f) {
      for (uint32_t i = 0; i < buffer_frames; i++) {
        outputs[0][offset + i] += earlyLevel * early_out_buffer[0][i];
        outputs[1][offset + i] += earlyLevel * early_out_buffer[1][i];
      }
    }
    if (lateLevel > 0.0f) {
      for (uint32_t i = 0; i < buffer_frames; i++) {
        outputs[0][offset + i] += lateLevel * late_out_buffer[0][i];
        outputs[1][offset + i] += lateLevel * late_out_buffer[1][i];
      }
    }
  }
}

void DragonflyReverbDSP::sampleRateChanged(double newSampleRate) {
  early.setSampleRate(newSampleRate);
  late.setSampleRate(newSampleRate);
}

void DragonflyReverbDSP::mute() {
  early.mute();
  late.mute();
}
