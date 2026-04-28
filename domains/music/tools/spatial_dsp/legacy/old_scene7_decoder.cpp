/*
  scene7_decoder.cpp — Scene7 / Music Scene Renderer core
  Direct-vs-diffuse spectral renderer: stereo in → 7.1 out.

  Signal flow (per 4096-sample block, 50% overlap-add):
    stereo in → windowed FFT → per-bin coherence/directness analysis
    → VBAP front-arc routing (direct content)
    → FOA-steered ambient routing with ms-range decorrelation (ambient content)
    → transient-stable soft-object placement
    → optional LFE redirect
    → 8× IFFT → overlap-add → interleaved output

  Spatial improvements over v1:
    1. Real decorrelation: SL/SR/BL/BR use 7/11/17/23 ms fractional-delay phase
       offsets — creates genuine acoustic-path differentiation between channels
    2. Directional ambient steering: ambient energy tracks L/R bias so the
       diffuse field has flow rather than being a static uniform halo
    3. FOA-inspired ambient decode: side/rear gains derived from a simplified
       first-order ambisonics horizontal decode (W + Y*sin(φ)), giving physically
       consistent energy distribution across the speaker ring
    4. VBAP front arc: direct content distributed across FL/FC/FR by per-bin pan
       position using vector-base amplitude panning — centered material locks to
       FC, panned material locks to FL or FR without bleeding into center
    5. Transient-aware object stabilization: per-bin exponential pan MA smooths
       over transient flickers; only sustained stable-pan content gets side
       object placement, preventing one-shot transients from pinging around
*/

#include "scene7_decoder.h"
#include "kiss_fftr.h"
#include <cmath>
#include <cstring>
#include <vector>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
static inline double clamp01(double x)    { return x < 0.0 ? 0.0 : (x > 1.0 ? 1.0 : x); }
static inline double clampN1P1(double x)  { return x < -1.0 ? -1.0 : (x > 1.0 ? 1.0 : x); }
static inline double amplitude(const kiss_fft_cpx& c) {
    return std::sqrt((double)c.r*c.r + (double)c.i*c.i);
}
static inline double phase_of(const kiss_fft_cpx& c)  { return std::atan2((double)c.i, (double)c.r); }
static kiss_fft_cpx make_polar(double amp, double ph) {
    kiss_fft_cpx c;
    c.r = (kiss_fft_scalar)(amp * std::cos(ph));
    c.i = (kiss_fft_scalar)(amp * std::sin(ph));
    return c;
}

// ---------------------------------------------------------------------------
// Output channel indices (WASAPI 7.1)
// ---------------------------------------------------------------------------
enum Ch { FL=0, FR=1, FC=2, LFE=3, BL=4, BR=5, SL=6, SR=7, NCH=8 };

// ---------------------------------------------------------------------------
// Per-bin freq-band routing weights
// ---------------------------------------------------------------------------
struct BinWeights { float frontW, sideW, rearW; };

// ---------------------------------------------------------------------------
// Decorrelation delay table (ms → per-channel)
// These simulate acoustic path-length differences between virtual speaker
// positions, creating perceptually distinct room-like spatial impression.
// All < N/2 samples at any practical sample rate to avoid overlap-add wrap.
// ---------------------------------------------------------------------------
static const double DECORR_DELAYS_MS[4] = {
     7.0,   // SL — nearest side reflection
    11.0,   // SR — opposite side (prime offset from SL)
    17.0,   // BL — rear left reflection
    23.0,   // BR — rear right (prime offset from BL)
};

// ---------------------------------------------------------------------------
// Implementation struct (pimpl)
// ---------------------------------------------------------------------------
struct Scene7Decoder::Impl {
    // --- config ---
    unsigned N;
    float    srate;
    Scene7Params params;

    // --- FFT ---
    kiss_fftr_cfg fwd;
    kiss_fftr_cfg inv[NCH];

    // --- time-domain work buffers ---
    std::vector<kiss_fft_scalar>  lt, rt;
    std::vector<double>           wnd;

    // --- frequency-domain work buffers ---
    std::vector<kiss_fft_cpx>    lf, rf;
    std::vector<kiss_fft_cpx>    sig[NCH];
    std::vector<kiss_fft_scalar> dst;

    // --- input overlap buffer ---
    // 50% overlap requires keeping the previous N/2 stereo frames so each
    // decode() call advances by N/2 new frames while the FFT always sees N frames.
    std::vector<float>  inbuf;    // N stereo frames = 2*N floats

    // --- overlap-add output ---
    std::vector<float>  outbuf;   // NCH * (N + N/2)
    std::vector<float>  result;   // NCH * N/2, interleaved
    bool                buffer_empty;

    // --- precomputed LUTs ---
    std::vector<BinWeights> freq_weights;          // [N/2+1]
    std::vector<double>     dph_SL, dph_SR;        // [N/2+1] decorr phase offsets
    std::vector<double>     dph_BL, dph_BR;

    // --- per-bin pan history (Improvement 5) ---
    // Exponential moving average of instantaneous pan position per bin.
    // Smooths over transient pan flickers; controls object placement stability.
    std::vector<double>  pan_ema;                  // [N/2+1]
    // Block rate ≈ srate/hop = srate/(N/2). Target time constant ≈ 200 ms.
    // alpha = exp(-1 / (block_rate * tc_sec)) ≈ 0.80 @ 44.1kHz/4096
    static constexpr double PAN_EMA_ALPHA = 0.80;

    // --- FOA ambient steering strength (Improvements 2 + 3) ---
    // 0 = symmetric (no steering), 1 = full Y-component steering.
    // 0.65 keeps a natural ambient field while tracking the mix's
    // left/right energy bias.
    static constexpr double STEER = 0.65;

    // --- LFE crossover bins ---
    unsigned lo_cut_bin, hi_cut_bin;

    // ---------------------------------------------------------------------------
    explicit Impl(unsigned block_size)
        : N(block_size), srate(44100.0f), buffer_empty(true),
          lo_cut_bin(0), hi_cut_bin(0)
    {
        fwd = kiss_fftr_alloc(N, 0, nullptr, nullptr);
        for (int c = 0; c < NCH; ++c)
            inv[c] = kiss_fftr_alloc(N, 1, nullptr, nullptr);

        lt.resize(N, 0); rt.resize(N, 0); dst.resize(N, 0);
        lf.resize(N/2+1); rf.resize(N/2+1);
        for (int c = 0; c < NCH; ++c) sig[c].resize(N/2+1);

        wnd.resize(N);
        for (unsigned k = 0; k < N; ++k)
            wnd[k] = 0.5 * (1.0 - std::cos(2.0 * M_PI * k / N));

        inbuf.resize(2 * N, 0.0f);   // N stereo frames, zeroed for startup silence
        outbuf.resize(NCH * (N + N/2), 0.0f);
        result.resize(NCH * (N/2), 0.0f);

        freq_weights.resize(N/2+1);
        dph_SL.resize(N/2+1); dph_SR.resize(N/2+1);
        dph_BL.resize(N/2+1); dph_BR.resize(N/2+1);
        pan_ema.assign(N/2+1, 0.0);

        compute_freq_weights();
        compute_decorr_phases();
    }

    ~Impl() {
        kiss_fftr_free(fwd);
        for (int c = 0; c < NCH; ++c) kiss_fftr_free(inv[c]);
    }

    // ---------------------------------------------------------------------------
    // Recompute frequency-band routing LUT
    // ---------------------------------------------------------------------------
    void compute_freq_weights() {
        const float ba = params.bass_anchor;
        for (unsigned f = 0; f <= N/2; ++f) {
            float hz = (float)f * srate / (float)N;
            float fW, sW, rW;
            if (hz < 150.0f) {
                fW = 1.00f; sW = 0.05f; rW = 0.00f;
                fW = fW + (1.0f - fW) * ba;
                sW = sW * (1.0f - ba * 0.8f);
            } else if (hz < 500.0f) {
                float t = (hz - 150.0f) / 350.0f;
                fW = 1.00f + t * (0.75f - 1.00f);
                sW = 0.05f + t * (0.30f - 0.05f);
                rW = 0.00f + t * (0.10f - 0.00f);
            } else if (hz < 3000.0f) {
                float t = (hz - 500.0f) / 2500.0f;
                fW = 0.75f + t * (0.60f - 0.75f);
                sW = 0.30f + t * (0.50f - 0.30f);
                rW = 0.10f + t * (0.30f - 0.10f);
            } else {
                fW = 0.45f; sW = 0.65f; rW = 0.50f;
            }
            // Gentle HF rolloff for ambient channels above 8 kHz.
            // FM synthesis, chiptune, and bright instruments have dense harmonic
            // stacks that pile into SL/SR at full sideW — sounds harsh and fizzy.
            // Roll sideW/rearW to ~30% by 14 kHz; fronts are unaffected.
            if (hz > 8000.0f) {
                float hf_t = std::min(1.0f, (hz - 8000.0f) / 6000.0f);
                sW *= 1.0f - hf_t * 0.70f;
                rW *= 1.0f - hf_t * 0.70f;
            }
            freq_weights[f] = { fW, sW, rW };
        }
    }

    // ---------------------------------------------------------------------------
    // Improvement 1: Recompute decorrelation phase tables using ms-range delays.
    // Called on srate change (delays are in seconds, so depend on srate).
    // Phase rotation for delay D samples at bin f: φ = -2π·f·D/N
    // ---------------------------------------------------------------------------
    void compute_decorr_phases() {
        std::vector<double>* tables[4] = { &dph_SL, &dph_SR, &dph_BL, &dph_BR };
        for (int ch = 0; ch < 4; ++ch) {
            double d_samp = DECORR_DELAYS_MS[ch] * (double)srate / 1000.0;
            for (unsigned f = 0; f <= N/2; ++f)
                (*tables[ch])[f] = -2.0 * M_PI * (double)f * d_samp / (double)N;
        }
    }

    // ---------------------------------------------------------------------------
    void update_lfe_bins() {
        // Hardcoded LFE crossover: 20–80 Hz (standard sub-bass redirect range).
        // Range is not exposed in the UI — on/off checkbox only.
        const float lo_hz = 20.0f;
        const float hi_hz = 80.0f;
        lo_cut_bin = (unsigned)(lo_hz / srate * (float)N);
        hi_cut_bin = (unsigned)(hi_hz / srate * (float)N);
        if (lo_cut_bin < 1) lo_cut_bin = 1;
        if (hi_cut_bin >= N/2) hi_cut_bin = N/2 - 1;
        if (hi_cut_bin < lo_cut_bin) hi_cut_bin = lo_cut_bin;
    }

    // ---------------------------------------------------------------------------
    // Main per-block decode.
    // input = N/2 NEW stereo frames (N floats, interleaved L/R).
    // Internally combines with the previous N/2 frames for a full N-frame FFT
    // window, then advances by N/2 — this is the standard 50% overlap-add hop.
    // Produces N/2 output frames, maintaining a 1:1 input:output time ratio.
    // ---------------------------------------------------------------------------
    void buffered_decode(float* input) {
        const Scene7Params& p = params;
        const float wrap_norm  = std::min(p.wrap / 180.0f, 1.0f);
        const float front_lock = p.front_lock;
        const float amount     = p.amount;
        const float rear_amt   = p.rear_amount;
        const float focus      = p.focus;
        const float soft_obj   = p.soft_objects;

        // ---- 0. Slide in N/2 new stereo frames ---------------------------------
        // inbuf holds N stereo frames (2*N floats).
        // First half: previous N/2 frames. Second half: new N/2 frames.
        // After the shift: [prev N/2 | new N/2] covers a full N-frame window.
        std::memmove(inbuf.data(), inbuf.data() + N, N * sizeof(float));
        std::memcpy( inbuf.data() + N, input,        N * sizeof(float));

        // ---- 1. Window + forward FFT ----------------------------------------
        for (unsigned k = 0; k < N; ++k) {
            lt[k] = (kiss_fft_scalar)(wnd[k] * inbuf[k*2 + 0]);
            rt[k] = (kiss_fft_scalar)(wnd[k] * inbuf[k*2 + 1]);
        }
        kiss_fftr(fwd, lt.data(), lf.data());
        kiss_fftr(fwd, rt.data(), rf.data());

        // ---- 2. Block-mean energy for soft-object gating --------------------
        double block_energy = 0.0;
        for (unsigned f = 1; f < N/2; ++f)
            block_energy += amplitude(lf[f]) + amplitude(rf[f]);
        block_energy /= (double)(N - 2);

        // ---- 3. Per-bin analysis + channel assignment -----------------------
        for (unsigned f = 1; f < N/2; ++f) {
            const double ampL = amplitude(lf[f]);
            const double ampR = amplitude(rf[f]);
            const double phL  = phase_of(lf[f]);
            const double phR  = phase_of(rf[f]);

            // --- Coherence & directness ---
            double phaseDiff = std::abs(phL - phR);
            if (phaseDiff > M_PI) phaseDiff = 2.0*M_PI - phaseDiff;
            const double coherence = std::cos(phaseDiff);  // 1=direct, -1=antiphase

            const double ampSum  = ampL + ampR;
            const double midAmp  = 0.5 * ampSum;
            const double sideAmp = 0.5 * std::abs(ampL - ampR);
            const double midRatio = (ampSum < 1e-12) ? 0.0
                                  : midAmp / (midAmp + sideAmp + 1e-12);

            double directness = coherence * coherence * midRatio;  // [0=diffuse, 1=direct]

            // Focus reshapes the directness curve
            if (focus > 0.0f)
                directness = 1.0 - std::pow(1.0 - directness, 1.0 + (double)focus * 3.0);
            else if (focus < 0.0f)
                directness = std::pow(directness, 1.0 + (double)(-focus) * 3.0);

            const double directFrac  = clamp01((double)front_lock * directness);
            // Softer ambient gate: original (1-directFrac) collapsed surrounds
            // too aggressively for direct content. (1 - directFrac*0.5) ensures
            // ambient channels never drop below 50% even for fully-direct bins.
            const double ambientFrac = (1.0 - directFrac * 0.5) * (double)amount;

            const BinWeights& w = freq_weights[f];
            const double sideGain = ambientFrac * (double)w.sideW * (double)wrap_norm;
            const double rearGain = ambientFrac * (double)w.rearW * (double)rear_amt;

            // M/S difference routing for sides only: sideAmp = |L-R|/2 per bin
            // captures panned instrument content and feeds SL/SR for spaciousness.
            // NOT applied to rears — sustained tonal stereo content in BL/BR with
            // large phase offsets (17–23 ms) creates audible warbling on some songs.
            // Rears receive diffuse/ambient content only via ambientFrac gating.
            const double diffSide = sideAmp * (double)w.sideW * (double)wrap_norm  * (double)amount * 0.30;

            const double ampTotal = std::sqrt(ampL*ampL + ampR*ampR);
            const double phC = std::atan2(lf[f].i + rf[f].i, lf[f].r + rf[f].r);

            // -----------------------------------------------------------------
            // Front channels: full stereo passthrough + additive center.
            //
            // FL/FR = original bins verbatim. No energy is removed from the
            // front image — this preserves punch, transient impact, and the
            // stereo field exactly as mixed.
            //
            // FC = additive center extraction: coherent, front-weighted content
            // proportional to directFrac. Diffuse/ambient content is near-zero
            // on FC and stays in FL/FR. FC adds depth/localization without
            // stealing energy from the stereo bed.
            //
            // pan_inst is still computed here because the soft-object pass
            // below uses it to steer object energy to SL or SR.
            // -----------------------------------------------------------------
            const double pan_inst = (ampSum > 1e-12)
                                  ? clampN1P1((ampR - ampL) / ampSum) : 0.0;

            sig[FL][f] = lf[f];
            sig[FR][f] = rf[f];
            sig[FC][f] = make_polar(midAmp * directFrac * (double)w.frontW, phC);

            // -----------------------------------------------------------------
            // Improvements 2 + 3: FOA-inspired directional ambient steering
            //
            // Y = normalised L/R energy bias of the ambient content.
            // Derived from the horizontal B-format Y component:
            //   Y ≈ (R-L)/(R+L)  (left=-1, center=0, right=+1)
            //
            // Ambient gain per channel:
            //   SL = sideGain * (1 - Y * STEER)    SR = sideGain * (1 + Y * STEER)
            //   BL = rearGain * (1 - Y * STEER*0.6) BR = rearGain * (1 + Y * STEER*0.6)
            //
            // SL+SR = 2*sideGain (energy conserved), BL+BR = 2*rearGain.
            // Rear steered less (×0.6) for a more diffuse rear field.
            // -----------------------------------------------------------------
            const double Y = (ampSum > 1e-12)
                           ? clampN1P1((ampR - ampL) / ampSum) : 0.0;

            // -----------------------------------------------------------------
            // Improvement 1: Real ms-range decorrelation
            // Phase offsets simulate distinct acoustic reflection paths.
            // SL uses left-channel phase base; SR uses right-channel phase base
            // so each side tracks its native stereo side independently.
            //
            // NOTE: sideGain is a dimensionless gain applied to ampTotal.
            //       diffSide is an amplitude (in FFT bin units), derived from
            //       sideAmp which is already proportional to ampTotal.
            //       They must NOT be added together and then scaled by ampTotal —
            //       that would multiply diffSide by ampTotal a second time,
            //       causing massive over-amplification on loud wide-stereo songs.
            //       Compute the two contributions separately.
            // -----------------------------------------------------------------
            const double sl_amp = ampTotal * sideGain * (1.0 - Y * STEER)
                                +            diffSide * (1.0 - Y * STEER);
            const double sr_amp = ampTotal * sideGain * (1.0 + Y * STEER)
                                +            diffSide * (1.0 + Y * STEER);
            const double bl_amp = ampTotal * rearGain * (1.0 - Y * STEER * 0.6);
            const double br_amp = ampTotal * rearGain * (1.0 + Y * STEER * 0.6);

            sig[SL][f] = make_polar(sl_amp, phL + dph_SL[f]);
            sig[SR][f] = make_polar(sr_amp, phR - dph_SR[f]);
            sig[BL][f] = make_polar(bl_amp, phL + dph_BL[f]);
            sig[BR][f] = make_polar(br_amp, phR - dph_BR[f]);

            // LFE zeroed here; filled below if enabled
            sig[LFE][f].r = sig[LFE][f].i = 0;

            // -----------------------------------------------------------------
            // Improvement 5: Transient-aware object stabilization
            //
            // Track per-bin pan position with an exponential MA (~200 ms TC).
            // An "object" is placed in the side channel only when:
            //   a) the EMA pan magnitude is strong (|pan_ema| > 0.5)
            //   b) the instantaneous pan is close to the EMA (stable, not a
            //      one-shot transient) — stability = 1 - |pan - pan_ema| * 4
            //   c) the bin's energy is above the block mean
            // This prevents cymbal hits, drum transients, etc. from pinging.
            // -----------------------------------------------------------------
            if (soft_obj > 0.0f && ampSum > 1e-12) {
                pan_ema[f] = pan_ema[f] * PAN_EMA_ALPHA
                           + pan_inst * (1.0 - PAN_EMA_ALPHA);

                const double emaPan   = pan_ema[f];
                const double panDev   = std::abs(pan_inst - emaPan);
                const double stability = std::max(0.0, 1.0 - panDev * 4.0);
                const double absEma   = std::abs(emaPan);

                if (absEma > 0.5 && stability > 0.5 && (ampL+ampR) > block_energy) {
                    // Cap objE to the current channel amplitude to prevent loud
                    // panned transients from spiking and causing crackling.
                    const double objRaw = (ampL+ampR)
                                        * (double)soft_obj
                                        * (absEma - 0.5) * 2.0
                                        * stability;
                    if (emaPan > 0.0) {
                        double cur = amplitude(sig[SR][f]);
                        const double objE = std::min(objRaw * emaPan, cur);
                        sig[SR][f] = make_polar(cur + objE, phase_of(sig[SR][f]));
                    } else {
                        double cur = amplitude(sig[SL][f]);
                        const double objE = std::min(objRaw * (-emaPan), cur);
                        sig[SL][f] = make_polar(cur + objE, phase_of(sig[SL][f]));
                    }
                }
            }

            // -----------------------------------------------------------------
            // LFE bass redirect
            // -----------------------------------------------------------------
            if (p.use_lfe() && f < hi_cut_bin) {
                const double lfe_level = (f < lo_cut_bin) ? 1.0
                    : 0.5 * (1.0 + std::cos(M_PI
                        * (double)(f - lo_cut_bin)
                        / (double)(hi_cut_bin - lo_cut_bin)));
                sig[LFE][f] = make_polar(ampTotal * lfe_level, phC);
                for (int c = 0; c < NCH; ++c) {
                    if (c == LFE) continue;
                    sig[c][f] = make_polar(amplitude(sig[c][f]) * (1.0 - lfe_level),
                                           phase_of(sig[c][f]));
                }
            }
        } // end per-bin loop

        // DC and Nyquist bins: zero all channels, pass-through L→FL, R→FR.
        // The per-bin loop covers f=1..N/2-1 only, so both endpoints must be
        // written explicitly — otherwise stale values from the previous block
        // remain in sig[c][N/2] and corrupt the IFFT output.
        for (int c = 0; c < NCH; ++c) {
            sig[c][0].r   = sig[c][0].i   = 0;
            sig[c][N/2].r = sig[c][N/2].i = 0;
        }
        sig[FL][0]   = lf[0];    sig[FR][0]   = rf[0];
        sig[FL][N/2] = lf[N/2];  sig[FR][N/2] = rf[N/2];

        // ---- 4. Overlap-add output ------------------------------------------
        for (int c = 0; c < NCH; ++c) {
            float* ob = outbuf.data() + c * (N + N/2);
            std::memmove(ob, ob + N/2, N * sizeof(float));
            std::memset(ob + N, 0, (N/2) * sizeof(float));
        }
        for (int c = 0; c < NCH; ++c) {
            kiss_fftri(inv[c], sig[c].data(), dst.data());
            float* ob = outbuf.data() + c * (N + N/2);
            // NO synthesis window — Hann analysis + rectangular synthesis + 50%
            // overlap satisfies COLA: w[k] + w[k+N/2] = 1.0 for all k.
            // Applying wnd[k] here would create Hann² OLA sum oscillating
            // 0.5..1.0 at the block rate (~22 Hz) — audible tremolo/waviness.
            const double scale = 1.0 / (double)N;
            for (unsigned k = 0; k < N; ++k)
                ob[N/2 + k] += (float)(dst[k] * scale);
        }

        // ---- 5. Interleave first N/2 output samples -------------------------
        for (unsigned s = 0; s < N/2; ++s)
            for (int c = 0; c < NCH; ++c)
                result[s * NCH + c] = outbuf[c * (N + N/2) + s];
    }

    void flush() {
        std::fill(inbuf.begin(),  inbuf.end(),  0.0f);
        std::fill(outbuf.begin(), outbuf.end(), 0.0f);
        std::fill(result.begin(), result.end(), 0.0f);
        std::fill(pan_ema.begin(), pan_ema.end(), 0.0);
        buffer_empty = true;
    }
};

// ---------------------------------------------------------------------------
// Public shell
// ---------------------------------------------------------------------------
Scene7Decoder::Scene7Decoder(unsigned block_size) : impl(new Impl(block_size)) {}
Scene7Decoder::~Scene7Decoder() { delete impl; }

float* Scene7Decoder::decode(float* stereo_interleaved) {
    impl->update_lfe_bins();
    impl->buffered_decode(stereo_interleaved);
    impl->buffer_empty = false;
    return impl->result.data();
}

void Scene7Decoder::set_samplerate(float sr) {
    if (sr != impl->srate) {
        impl->srate = sr;
        impl->compute_freq_weights();
        impl->compute_decorr_phases();  // ms-range delays now depend on srate
    }
}

void Scene7Decoder::set_params(const Scene7Params& p) {
    impl->params = p;
    impl->compute_freq_weights();
    impl->update_lfe_bins();
}

unsigned Scene7Decoder::get_latency() const { return impl->N / 2; }

unsigned Scene7Decoder::buffered() const {
    return impl->buffer_empty ? 0 : impl->N / 2;
}

void Scene7Decoder::flush() { impl->flush(); }
