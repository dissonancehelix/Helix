/*
  prism_decoder.h — Prism DSP core
  Direct-vs-diffuse spectral renderer: stereo in → 7.1 PCM out.

  Channel order (WASAPI 7.1):
    [0] FL  [1] FR  [2] FC  [3] LFE  [4] BL  [5] BR  [6] SL  [7] SR
*/
#pragma once
#include "prism_params.h"

class PrismDecoder {
public:
    explicit PrismDecoder(unsigned block_size = 4096);
    ~PrismDecoder();

    // Decode one stereo block.
    // @param  stereo_interleaved  exactly block_size*2 floats [L0,R0,L1,R1,...]
    // @return pointer to internal buffer of block_size*8 interleaved 7.1 floats;
    //         valid until the next call to decode() or flush().
    float* decode(float* stereo_interleaved);

    // Update sample-rate — recomputes frequency-band LUT and decorr phase tables.
    void set_samplerate(float sr);

    // Replace active parameters; takes effect from the next decode() block.
    void set_params(const PrismParams& p);

    // Samples of latency introduced (always block_size / 2).
    unsigned get_latency() const;

    // Samples currently held in the internal overlap buffer (for latency reporting).
    unsigned buffered() const;

    // Drain internal buffers; call before a seek / track-change.
    void flush();

private:
    struct Impl;
    Impl* impl;
};
