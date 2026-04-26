/*
  dragonfly_reverb.cpp
  foobar2000 DSP wrapper for Dragonfly Hall Reverb.
  Stereo-in / stereo-out. Place before Prism in the DSP chain.

  DSP core: Dragonfly Hall Reverb by Michael Willis & Rob van den Berg (GPL v3)
  Freeverb3 library: Copyright (C) 2006-2018 Teru Kamogashira (GPL v2+)
*/

#include "stdafx.h"
#include "dragonfly_resource.h"
#include "../SDK/foobar2000.h"
#include "../SDK/coreDarkMode.h"
#include "../SDK/modeless_dialog.h"
#include "DSP.hpp"
#include <vector>
#include <cstdio>
#include <algorithm>
#include <cmath>

DECLARE_COMPONENT_VERSION("Dragonfly Hall Reverb", "1.0.0",
    "Dragonfly Hall Reverb\n\nHall-style reverb DSP.\n"
    "DSP core by Michael Willis & Rob van den Berg (GPL v3).\n"
    "Freeverb3 by Teru Kamogashira (GPL v2+).");

// {6A4F2B83-1C8E-4D5A-9F3B-7E21D45C8A1F}
static const GUID dragonfly_guid = {
    0x6a4f2b83, 0x1c8e, 0x4d5a,
    { 0x9f, 0x3b, 0x7e, 0x21, 0xd4, 0x5c, 0x8a, 0x1f }
};

// ---------------------------------------------------------------------------
// Preset serialization
// ---------------------------------------------------------------------------
struct DragonflyPreset {
    static const uint32_t MAGIC   = 0x44465256u; // 'DFRV'
    static const uint32_t VERSION = 1u;

    // Exposed parameters (8 floats)
    float dry;       // 0-100 %
    float early;     // 0-100 %
    float late;      // 0-100 %
    float size;      // 10-60 m
    float decay;     // 0.1-10 s
    float diffuse;   // 0-100 %
    float high_cut;  // 1000-16000 Hz
    float predelay;  // 0-100 ms

    DragonflyPreset() {
        // Default: Large Clear Hall
        const float* p = banks[DEFAULT_BANK].presets[DEFAULT_PRESET].params;
        dry      = p[paramDry];
        early    = p[paramEarly];
        late     = p[paramLate];
        size     = p[paramSize];
        decay    = p[paramDecay];
        diffuse  = p[paramDiffuse];
        high_cut = p[paramHighCut];
        predelay = p[paramPredelay];
    }

    static unsigned byte_size() {
        return sizeof(uint32_t) * 2 + sizeof(DragonflyPreset);
    }

    void to_bytes(uint8_t* buf, unsigned sz) const {
        if (sz < byte_size()) return;
        uint32_t* u = reinterpret_cast<uint32_t*>(buf);
        u[0] = MAGIC; u[1] = VERSION;
        memcpy(buf + 8, this, sizeof(DragonflyPreset));
    }

    bool from_bytes(const void* data, unsigned sz) {
        if (!data || sz < byte_size()) return false;
        const uint32_t* u = reinterpret_cast<const uint32_t*>(data);
        if (u[0] != MAGIC || u[1] != VERSION) return false;
        memcpy(this, reinterpret_cast<const uint8_t*>(data) + 8, sizeof(DragonflyPreset));
        return true;
    }

    void apply_to(DragonflyReverbDSP& dsp) const {
        dsp.setParameterValue(paramDry,      dry);
        dsp.setParameterValue(paramEarly,    early);
        dsp.setParameterValue(paramLate,     late);
        dsp.setParameterValue(paramSize,     size);
        dsp.setParameterValue(paramDecay,    decay);
        dsp.setParameterValue(paramDiffuse,  diffuse);
        dsp.setParameterValue(paramHighCut,  high_cut);
        dsp.setParameterValue(paramPredelay, predelay);
    }
};

static void preset_to_fb2k(const DragonflyPreset& p, dsp_preset& out) {
    unsigned sz = DragonflyPreset::byte_size();
    std::vector<uint8_t> buf(sz);
    p.to_bytes(buf.data(), sz);
    out.set_data(buf.data(), sz);
    out.set_owner(dragonfly_guid);
}

static DragonflyPreset preset_from_fb2k(const dsp_preset& in) {
    DragonflyPreset p;
    if (!p.from_bytes(in.get_data(), (unsigned)in.get_data_size())) {
        console::warning("Dragonfly: unrecognized preset; using defaults.");
    }
    return p;
}

// ---------------------------------------------------------------------------
// DSP implementation
// ---------------------------------------------------------------------------
class dragonfly_dsp : public dsp_impl_base {
public:
    dragonfly_dsp(const dsp_preset& in)
        : params(preset_from_fb2k(in)),
          dsp(48000.0),
          srate(48000)
    {
        params.apply_to(dsp);
    }

    bool on_chunk(audio_chunk* chunk, abort_callback&) {
        const unsigned ch = chunk->get_channel_count();
        if (ch != 2) return true; // pass non-stereo through

        unsigned new_srate = chunk->get_srate();
        if (new_srate != srate) {
            srate = new_srate;
            dsp.sampleRateChanged((double)srate);
        }

        const unsigned frames  = chunk->get_sample_count();
        const audio_sample* src = chunk->get_data();

        // deinterleave
        in_l.resize(frames); in_r.resize(frames);
        out_l.resize(frames); out_r.resize(frames);
        for (unsigned i = 0; i < frames; ++i) {
            in_l[i] = (float)src[i * 2 + 0];
            in_r[i] = (float)src[i * 2 + 1];
        }

        const float* ins[2]  = { in_l.data(),  in_r.data()  };
        float*       outs[2] = { out_l.data(), out_r.data() };
        dsp.run(ins, outs, frames);

        // reinterleave in-place
        chunk->set_data_size(frames * 2);
        audio_sample* dst = chunk->get_data();
        for (unsigned i = 0; i < frames; ++i) {
            dst[i * 2 + 0] = (audio_sample)out_l[i];
            dst[i * 2 + 1] = (audio_sample)out_r[i];
        }
        return true;
    }

    void on_endoftrack(abort_callback&) {}
    bool need_track_change_mark() { return false; }
    void on_endofplayback(abort_callback&) {}
    double get_latency() { return 0.0; }
    void flush() { dsp.mute(); }

    static void g_get_name(pfc::string_base& n) { n = "Dragonfly Hall Reverb"; }
    static void g_get_display_name(const dsp_preset&, pfc::string_base& n) { n = "Dragonfly Hall Reverb"; }
    static bool g_get_default_preset(dsp_preset& p) { preset_to_fb2k(DragonflyPreset(), p); return true; }
    static bool g_have_config_popup() { return true; }
    static GUID g_get_guid() { return dragonfly_guid; }
    static void g_show_config_popup(const dsp_preset& p, HWND wnd, dsp_preset_edit_callback& cbf);
    static service_ptr_t<service_base> g_show_config_popup_v3(HWND parent, dsp_preset_edit_callback_v2::ptr callback);

private:
    DragonflyPreset    params;
    DragonflyReverbDSP dsp;
    unsigned           srate;
    std::vector<float> in_l, in_r, out_l, out_r;
};

static dsp_factory_t<dragonfly_dsp, dsp_entry_v3> g_dragonfly_factory;


// ---------------------------------------------------------------------------
// Config dialog
// ---------------------------------------------------------------------------
class CDragonflyDialog : public CDialog {
    DECLARE_DYNAMIC(CDragonflyDialog)
public:
    // Modeless ctor (v3)
    CDragonflyDialog(const DragonflyPreset& s0, dsp_preset_edit_callback_v2::ptr cbf, HWND parent);
    // Modal ctor (v2 legacy)
    CDragonflyDialog(const DragonflyPreset& s0, dsp_preset_edit_callback& cbf_v1, HWND parent);
    virtual ~CDragonflyDialog() {}
    enum { IDD = IDD_REVERB_DIALOG };

    static CDragonflyDialog* s_active;

protected:
    virtual BOOL OnInitDialog();
    virtual void PostNcDestroy();
    afx_msg void OnDestroy();
    afx_msg void OnHScroll(UINT, UINT, CScrollBar*) { refresh(); }
    afx_msg void OnReset();
    virtual void OnCancel();
    virtual void OnOK() {}
    afx_msg void OnTimer(UINT_PTR id);
    void refresh();
    void notify_preset_change();
    virtual void DoDataExchange(CDataExchange* pDX);
    DECLARE_MESSAGE_MAP()

    void load_controls_from(const DragonflyPreset& src);

    // Slider int members (all 0-100)
    int sl_dry, sl_early, sl_late;
    int sl_size;      // maps to 10-60m
    int sl_decay;     // maps to 0.1-10s
    int sl_diffuse;
    int sl_highcut;   // maps to 1000-16000 Hz
    int sl_predelay;  // maps to 0-100ms

    DragonflyPreset             s;
    DragonflyPreset             m_reset_snapshot;
    dsp_preset_edit_callback_v2::ptr m_cbf;
    dsp_preset_edit_callback*        m_cbf_v2_legacy = nullptr;
    bool                        m_is_modal = false;
    HWND                        m_parent_hwnd = nullptr;
    fb2k::CCoreDarkModeHooks    m_dark_hooks;
};

CDragonflyDialog* CDragonflyDialog::s_active = nullptr;
IMPLEMENT_DYNAMIC(CDragonflyDialog, CDialog)

CDragonflyDialog::CDragonflyDialog(const DragonflyPreset& s0, dsp_preset_edit_callback_v2::ptr cbf, HWND parent)
    : CDialog(IDD, nullptr), s(s0), m_reset_snapshot(s0),
      m_cbf(cbf), m_is_modal(false), m_parent_hwnd(parent)
{
    load_controls_from(s);
}

CDragonflyDialog::CDragonflyDialog(const DragonflyPreset& s0, dsp_preset_edit_callback& cbf_v1, HWND parent)
    : CDialog(IDD, nullptr), s(s0), m_reset_snapshot(s0),
      m_cbf_v2_legacy(&cbf_v1), m_is_modal(true), m_parent_hwnd(parent)
{
    load_controls_from(s);
}

void CDragonflyDialog::load_controls_from(const DragonflyPreset& src) {
    sl_dry      = (int)(src.dry + 0.5f);
    sl_early    = (int)(src.early + 0.5f);
    sl_late     = (int)(src.late + 0.5f);
    sl_size     = (int)((src.size - 10.0f) / 0.5f + 0.5f);   // 10-60m → 0-100
    sl_decay    = (int)((src.decay - 0.1f) / 0.099f + 0.5f); // 0.1-10s → 0-100
    sl_diffuse  = (int)(src.diffuse + 0.5f);
    sl_highcut  = (int)((src.high_cut - 1000.0f) / 150.0f + 0.5f); // 1k-16kHz → 0-100
    sl_predelay = (int)(src.predelay + 0.5f);

    // Clamp
    sl_size     = std::max(0, std::min(100, sl_size));
    sl_decay    = std::max(0, std::min(100, sl_decay));
    sl_highcut  = std::max(0, std::min(100, sl_highcut));
}

BOOL CDragonflyDialog::OnInitDialog() {
    CDialog::OnInitDialog();
    m_dark_hooks.AddDialogWithControls(m_hWnd);
    if (!m_is_modal) {
        try { modeless_dialog_manager::g_add(m_hWnd); } catch (...) {}
        SetTimer(1, 500, nullptr);
        s_active = this;
    }
    UpdateData(FALSE);
    return TRUE;
}

void CDragonflyDialog::OnDestroy() {
    if (!m_is_modal) {
        if (m_cbf.is_valid()) try { m_cbf->dsp_dialog_done(true); } catch (...) {}
        try { modeless_dialog_manager::g_remove(m_hWnd); } catch (...) {}
        if (s_active == this) s_active = nullptr;
    }
    CDialog::OnDestroy();
}

void CDragonflyDialog::PostNcDestroy() {
    CDialog::PostNcDestroy();
    if (!m_is_modal) delete this;
}

void CDragonflyDialog::OnReset() {
    s = m_reset_snapshot;
    load_controls_from(s);
    UpdateData(FALSE);
    refresh();
}

void CDragonflyDialog::OnCancel() {
    if (m_is_modal) CDialog::OnCancel();
    else DestroyWindow();
}

void CDragonflyDialog::OnTimer(UINT_PTR id) {
    if (id == 1 && !m_is_modal) {
        if (m_parent_hwnd && !::IsWindow(m_parent_hwnd)) {
            KillTimer(1);
            DestroyWindow();
            return;
        }
    }
    CDialog::OnTimer(id);
}

void CDragonflyDialog::refresh() {
    CDataExchange dx(this, true);
    DoDataExchange(&dx);
    notify_preset_change();
}

void CDragonflyDialog::notify_preset_change() {
    dsp_preset_impl tmp;
    preset_to_fb2k(s, tmp);
    if (!m_is_modal) {
        if (m_cbf.is_valid()) try { m_cbf->set_preset(tmp); } catch (...) {}
    } else {
        if (m_cbf_v2_legacy) try { m_cbf_v2_legacy->on_preset_changed(tmp); } catch (...) {}
    }
}

void CDragonflyDialog::DoDataExchange(CDataExchange* pDX) {
    CDialog::DoDataExchange(pDX);

    DDX_Slider(pDX, IDC_DRY,      sl_dry);
    DDX_Slider(pDX, IDC_EARLY,    sl_early);
    DDX_Slider(pDX, IDC_LATE,     sl_late);
    DDX_Slider(pDX, IDC_SIZE,     sl_size);
    DDX_Slider(pDX, IDC_DECAY,    sl_decay);
    DDX_Slider(pDX, IDC_DIFFUSE,  sl_diffuse);
    DDX_Slider(pDX, IDC_HIGHCUT,  sl_highcut);
    DDX_Slider(pDX, IDC_PREDELAY, sl_predelay);

    // Map slider ints back to float params
    s.dry      = (float)sl_dry;
    s.early    = (float)sl_early;
    s.late     = (float)sl_late;
    s.size     = 10.0f + sl_size     * 0.5f;
    s.decay    = 0.1f  + sl_decay    * 0.099f;
    s.diffuse  = (float)sl_diffuse;
    s.high_cut = 1000.0f + sl_highcut * 150.0f;
    s.predelay = (float)sl_predelay;

    // Value labels
    char b[32];
#define SV(id, fmt, ...) std::snprintf(b, sizeof(b), fmt, __VA_ARGS__); ::uSetDlgItemText(*this, id, b)
    SV(IDC_DRYT,       "(%.0f%%)", s.dry);
    SV(IDC_EARLYT,     "(%.0f%%)", s.early);
    SV(IDC_LATET,      "(%.0f%%)", s.late);
    SV(IDC_SIZET,      "(%.0fm)", s.size);
    SV(IDC_DECAYT,     "(%.1fs)", s.decay);
    SV(IDC_DIFFUSET,   "(%.0f%%)", s.diffuse);
    SV(IDC_HIGHCUTT,   "(%.0f)", s.high_cut);
    SV(IDC_PREDELAYT,  "(%.0fms)", s.predelay);
#undef SV
}

BEGIN_MESSAGE_MAP(CDragonflyDialog, CDialog)
    ON_WM_HSCROLL()
    ON_WM_TIMER()
    ON_WM_DESTROY()
    ON_BN_CLICKED(IDC_RESET, &CDragonflyDialog::OnReset)
END_MESSAGE_MAP()

// ---------------------------------------------------------------------------
// g_show_config_popup — v2 legacy modal path
// ---------------------------------------------------------------------------
void dragonfly_dsp::g_show_config_popup(const dsp_preset& p, HWND wnd, dsp_preset_edit_callback& cbf) {
    AFX_MANAGE_STATE(AfxGetStaticModuleState());
    DragonflyPreset params = preset_from_fb2k(p);
    CDragonflyDialog dlg(params, cbf, wnd);
    dlg.DoModal();
}

// ---------------------------------------------------------------------------
// g_show_config_popup_v3 — v3 modeless path (ref-counted callback)
// ---------------------------------------------------------------------------
service_ptr_t<service_base> dragonfly_dsp::g_show_config_popup_v3(HWND parent, dsp_preset_edit_callback_v2::ptr callback) {
    AFX_MANAGE_STATE(AfxGetStaticModuleState());
    if (CDragonflyDialog::s_active && ::IsWindow(CDragonflyDialog::s_active->m_hWnd)) {
        ::SetForegroundWindow(CDragonflyDialog::s_active->m_hWnd);
        return nullptr;
    }
    dsp_preset_impl preset;
    callback->get_preset(preset);
    DragonflyPreset params = preset_from_fb2k(preset);
    auto* dlg = new CDragonflyDialog(params, callback, parent);
    if (!dlg->Create(CDragonflyDialog::IDD, nullptr)) { delete dlg; return nullptr; }
    dlg->ShowWindow(SW_SHOW);
    return nullptr;
}
