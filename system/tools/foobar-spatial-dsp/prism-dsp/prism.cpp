/*
  prism.cpp — Prism DSP
  foobar2000 DSP wrapper + MFC config dialog.

  Dialog lifecycle note:
    Prism registers as dsp_entry_v3 so foobar calls show_config_popup_v3() with a
    ref-counted dsp_preset_edit_callback_v2::ptr that remains valid for the entire
    modeless session.  The old v1 dsp_preset_edit_callback& path (show_config_popup_v2)
    is a short-lived stack object that dies the moment g_show_config_popup() returns;
    calling on_preset_changed() on it later causes a null-vtable crash.  By using v3
    we avoid that entirely.  g_show_config_popup (v2 path) is still provided for
    compilation but runs a simple modal DoModal() so the reference remains valid.
*/

#include "stdafx.h"
#include "resource1.h"
#include "../SDK/foobar2000.h"
#include "../SDK/coreDarkMode.h"
#include "../SDK/modeless_dialog.h"
#include "stream_chunker.h"
#include "prism_decoder.h"
#include "prism_params.h"
#include <vector>
#include <functional>
#include <cstring>
#include <cstdio>
#include <algorithm>
#include <cmath>

DECLARE_COMPONENT_VERSION("Prism", "3.0.0",
    "Prism\n\nPersonal stereo-to-7.1 spatial renderer.");

// {A3F12E84-5C70-4B9A-B31D-22E7F9C08D45}
static const GUID prism_guid = {
    0xa3f12e84, 0x5c70, 0x4b9a,
    { 0xb3, 0x1d, 0x22, 0xe7, 0xf9, 0xc0, 0x8d, 0x45 }
};

static const unsigned OUTPUT_CHANNELS = 8;
static const unsigned CHAN_CODE =
    audio_chunk::channel_front_left    | audio_chunk::channel_front_right   |
    audio_chunk::channel_front_center  | audio_chunk::channel_lfe           |
    audio_chunk::channel_back_left     | audio_chunk::channel_back_right    |
    audio_chunk::channel_side_left     | audio_chunk::channel_side_right;

// ---------------------------------------------------------------------------
// Preset I/O helpers using PrismParams built-in binary serializer
// ---------------------------------------------------------------------------
static void params_to_preset(const PrismParams& p, dsp_preset& out) {
    unsigned sz = PrismParams::byte_size();
    std::vector<uint8_t> buf(sz);
    p.to_bytes(buf.data(), sz);
    out.set_data(buf.data(), sz);
    out.set_owner(prism_guid);
}

static PrismParams params_from_preset(const dsp_preset& in) {
    PrismParams p;
    if (!p.from_bytes(in.get_data(), (unsigned)in.get_data_size())) {
        console::warning("Prism: unrecognized preset format; using defaults.");
        p = PrismParams();
    }
    return p;
}

// ---------------------------------------------------------------------------
// DSP implementation
// ---------------------------------------------------------------------------
class prism_dsp : public dsp_impl_base {
    enum { chunk_size = 4096 };
public:
    prism_dsp(const dsp_preset& in)
        : params(params_from_preset(in)),
          rechunker([this](audio_sample* s){ process_chunk(s); }, chunk_size),
          decoder(chunk_size),
          srate(48000)
    {
        decoder.set_params(params);
    }

    bool on_chunk(audio_chunk* chunk, abort_callback&) {
        srate = chunk->get_srate();
        decoder.set_samplerate((float)srate);
        if (chunk->get_channel_config() == audio_chunk::channel_config_stereo) {
            rechunker.append(
                const_cast<audio_sample*>(chunk->get_data()),
                (unsigned)chunk->get_data_length());
            return false;
        }
        console::warning("Prism: non-stereo input -- passing through unmodified.");
        return true;
    }

    void process_chunk(audio_sample* samples) {
        const unsigned hop = chunk_size / 2;

        std::vector<float> stereo(hop * 2);
        for (unsigned i = 0; i < hop * 2; ++i)
            stereo[i] = (float)samples[i];

        float* src = decoder.decode(stereo.data());

        const unsigned out_frames  = hop;
        const unsigned out_samples = out_frames * OUTPUT_CHANNELS;

        audio_chunk* out_chunk = insert_chunk(out_samples);
        out_chunk->set_data_size(out_samples);
        out_chunk->set_channels(OUTPUT_CHANNELS, CHAN_CODE);
        out_chunk->set_sample_rate(srate);
        out_chunk->set_sample_count(out_frames);

        audio_sample* dst = out_chunk->get_data();
        for (unsigned i = 0; i < out_samples; ++i)
            dst[i] = (audio_sample)src[i];
    }

    void on_endoftrack(abort_callback&) {}
    bool need_track_change_mark() { return false; }
    void on_endofplayback(abort_callback&) {
        std::vector<audio_sample> silence(chunk_size, (audio_sample)0);
        rechunker.append(silence.data(), (unsigned)silence.size());
        rechunker.append(silence.data(), (unsigned)silence.size());
    }

    double get_latency() {
        return srate ? (double)(rechunker.buffered() / 2 + decoder.get_latency()) / (double)srate : 0.0;
    }
    void flush() { rechunker.flush(); decoder.flush(); }

    static void g_get_name(pfc::string_base& n) { n = "Prism"; }
    static void g_get_display_name(const dsp_preset&, pfc::string_base& n) { n = "Prism"; }
    static bool g_get_default_preset(dsp_preset& p) {
        params_to_preset(PrismParams(), p); return true;
    }
    // v2 legacy path — modal, cbf valid for duration of this blocking call
    static void g_show_config_popup(const dsp_preset& p, HWND wnd, dsp_preset_edit_callback& cbf);
    // v3 modeless path — cbf_v2 is ref-counted, lives as long as we hold it
    static service_ptr_t<service_base> g_show_config_popup_v3(HWND parent, dsp_preset_edit_callback_v2::ptr callback);
    static bool g_have_config_popup() { return true; }
    static GUID g_get_guid() { return prism_guid; }

private:
    PrismParams                        params;
    stream_chunker<audio_sample>        rechunker;
    PrismDecoder                       decoder;
    unsigned                            srate;
};

// Register as dsp_entry_v3 so foobar prefers the modeless show_config_popup_v3 path.
static dsp_factory_t<prism_dsp, dsp_entry_v3> g_prism_factory;


// ---------------------------------------------------------------------------
// Config dialog
// ---------------------------------------------------------------------------
class CPrismDialog : public CDialog {
    DECLARE_DYNAMIC(CPrismDialog)
public:
    // Modeless constructor (v3 path): cbf_v2 is ref-counted, lives as long as dialog.
    CPrismDialog(const PrismParams& s0, dsp_preset_edit_callback_v2::ptr cbf_v2, HWND parent);
    // Modal constructor (v2 legacy path): cbf_v1 is a raw ref, valid only during DoModal().
    CPrismDialog(const PrismParams& s0, dsp_preset_edit_callback& cbf_v1, HWND parent);
    virtual ~CPrismDialog() {}
    enum { IDD = IDD_DIALOG1 };

    // Double-open guard. Set in OnInitDialog, cleared in OnDestroy.
    static CPrismDialog* s_active;

protected:
    virtual BOOL OnInitDialog();
    virtual void PostNcDestroy();
    afx_msg void OnDestroy();
    afx_msg void OnHScroll(UINT, UINT, CScrollBar*) { refresh(); }
    afx_msg void OnBnClickedRedir() { refresh(); }
    afx_msg void OnReset();
    virtual void OnCancel();
    virtual void OnOK() {}      // swallow Enter (modeless; no OK semantics)
    afx_msg void OnTimer(UINT_PTR id);
    void refresh();
    void notify_preset_change();
    virtual void DoDataExchange(CDataExchange* pDX);
    DECLARE_MESSAGE_MAP()

    void load_controls_from(const PrismParams& src);

public:
    PrismParams             s;
    PrismParams             m_reset_snapshot;

    int sl_amount, sl_wrap, sl_frontlock, sl_rear, sl_focus;
    int sl_bassanchor, sl_objects;
    int check_redir;

    // Advanced controls
    int check_scenemem, sl_scenemem;
    int check_height,   sl_height;

    fb2k::CCoreDarkModeHooks m_dark_hooks;

private:
    // v3 modeless: ref-counted callback, stays alive as long as we hold it
    dsp_preset_edit_callback_v2::ptr m_cbf;
    // v2 modal: raw pointer valid only during DoModal(); null in modeless mode
    dsp_preset_edit_callback* m_cbf_v2_legacy = nullptr;
    bool m_is_modal = false;
    HWND m_parent_hwnd = nullptr;
};

CPrismDialog* CPrismDialog::s_active = nullptr;

IMPLEMENT_DYNAMIC(CPrismDialog, CDialog)

// Modeless constructor (v3 path)
CPrismDialog::CPrismDialog(const PrismParams& s0, dsp_preset_edit_callback_v2::ptr cbf_v2, HWND parent)
    : CDialog(CPrismDialog::IDD, nullptr),
      s(s0), m_reset_snapshot(s0),
      m_cbf(cbf_v2), m_is_modal(false), m_parent_hwnd(parent)
{
    load_controls_from(s);
}

// Modal constructor (v2 legacy path)
CPrismDialog::CPrismDialog(const PrismParams& s0, dsp_preset_edit_callback& cbf_v1, HWND parent)
    : CDialog(CPrismDialog::IDD, nullptr),
      s(s0), m_reset_snapshot(s0),
      m_cbf_v2_legacy(&cbf_v1), m_is_modal(true), m_parent_hwnd(parent)
{
    load_controls_from(s);
}

void CPrismDialog::load_controls_from(const PrismParams& src) {
    sl_amount     = (int)(src.amount       * 100.0f + 0.5f);
    sl_wrap       = (int)(src.wrap        / 360.0f * 100.0f + 0.5f);
    sl_frontlock  = (int)(src.front_lock   * 100.0f + 0.5f);
    sl_rear       = (int)(src.rear_amount  * 100.0f + 0.5f);
    sl_focus      = (int)((src.focus + 1.0f) / 2.0f * 100.0f + 0.5f);
    sl_bassanchor = (int)(src.bass_anchor  * 100.0f + 0.5f);
    sl_objects    = (int)(src.soft_objects * 100.0f + 0.5f);
    check_redir   = src.use_lfe() ? 1 : 0;
    // Advanced
    check_scenemem = src.enable_scene_memory > 0.5f ? 1 : 0;
    sl_scenemem    = (int)(src.scene_memory_amount * 100.0f + 0.5f);
    check_height   = src.enable_height_synth  > 0.5f ? 1 : 0;
    sl_height      = (int)(src.height_amount  * 100.0f + 0.5f);
}

BOOL CPrismDialog::OnInitDialog() {
    CDialog::OnInitDialog();
    m_dark_hooks.AddDialogWithControls(m_hWnd);
    if (!m_is_modal) {
        // Register with foobar's modeless manager for IsDialogMessage routing.
        try { modeless_dialog_manager::g_add(m_hWnd); } catch (...) {}
        // Poll parent liveness: self-close if DSP preferences page is dismissed.
        SetTimer(1, 500, nullptr);
        s_active = this;
    }
    UpdateData(FALSE);
    return TRUE;
}

void CPrismDialog::OnDestroy() {
    if (!m_is_modal) {
        // Signal foobar the dialog is done before tearing down.
        if (m_cbf.is_valid()) {
            try { m_cbf->dsp_dialog_done(true); } catch (...) {}
        }
        try { modeless_dialog_manager::g_remove(m_hWnd); } catch (...) {}
        if (s_active == this) s_active = nullptr;
    }
    CDialog::OnDestroy();
}

void CPrismDialog::PostNcDestroy() {
    CDialog::PostNcDestroy();
    if (!m_is_modal) delete this;  // self-delete only for heap-allocated modeless
}

void CPrismDialog::OnReset() {
    s = m_reset_snapshot;
    load_controls_from(s);
    UpdateData(FALSE);
    refresh();
}

void CPrismDialog::OnCancel() {
    if (m_is_modal) {
        // Modal: EndDialog so DoModal() returns.
        CDialog::OnCancel();
    } else {
        // Modeless: Esc / Close button / X. No revert — live edits stay committed.
        DestroyWindow();
    }
}

void CPrismDialog::OnTimer(UINT_PTR id) {
    if (id == 1 && !m_is_modal) {
        // If the preferences page that owns the cbf has been destroyed,
        // close ourselves rather than risk a stale pointer.
        if (m_parent_hwnd && !::IsWindow(m_parent_hwnd)) {
            KillTimer(1);
            DestroyWindow();
            return;
        }
    }
    CDialog::OnTimer(id);
}

void CPrismDialog::refresh() {
    // Phase 1: read controls → member vars → recompute s → update labels/enable state
    CDataExchange dx(this, true);
    DoDataExchange(&dx);
    // Phase 2: push updated preset to foobar (outside DoDataExchange to keep DDX pure)
    notify_preset_change();
}

void CPrismDialog::notify_preset_change() {
    dsp_preset_impl tmp;
    params_to_preset(s, tmp);
    if (!m_is_modal) {
        // Modeless (v3): ref-counted callback — always safe to call
        if (m_cbf.is_valid()) {
            try { m_cbf->set_preset(tmp); } catch (...) {}
        }
    } else {
        // Modal (v2 legacy): raw pointer valid only while DoModal() is on the stack
        if (m_cbf_v2_legacy) {
            try { m_cbf_v2_legacy->on_preset_changed(tmp); } catch (...) {}
        }
    }
}

void CPrismDialog::DoDataExchange(CDataExchange* pDX) {
    CDialog::DoDataExchange(pDX);

    DDX_Slider(pDX, IDC_AMOUNT,     sl_amount);
    DDX_Slider(pDX, IDC_WRAP,       sl_wrap);
    DDX_Slider(pDX, IDC_FRONTLOCK,  sl_frontlock);
    DDX_Slider(pDX, IDC_REAR,       sl_rear);
    DDX_Slider(pDX, IDC_FOCUS,      sl_focus);
    DDX_Slider(pDX, IDC_BASSANCHOR, sl_bassanchor);
    DDX_Slider(pDX, IDC_OBJECTS,    sl_objects);
    DDX_Check(pDX, IDC_REDIR,       check_redir);
    // Advanced
    DDX_Check(pDX, IDC_ENABLE_SCENEMEM, check_scenemem);
    DDX_Slider(pDX, IDC_SLIDER_SCENEMEM, sl_scenemem);
    DDX_Check(pDX, IDC_ENABLE_HEIGHT, check_height);
    DDX_Slider(pDX, IDC_SLIDER_HEIGHT, sl_height);

    s.amount       = sl_amount      / 100.0f;
    s.wrap         = sl_wrap        / 100.0f * 360.0f;
    s.front_lock   = sl_frontlock   / 100.0f;
    s.rear_amount  = sl_rear        / 100.0f;
    s.focus        = sl_focus       / 100.0f * 2.0f - 1.0f;
    s.bass_anchor  = sl_bassanchor  / 100.0f;
    s.soft_objects = sl_objects     / 100.0f;
    s.set_use_lfe(check_redir != 0);
    // Advanced
    s.enable_scene_memory  = check_scenemem ? 1.0f : 0.0f;
    s.scene_memory_amount  = sl_scenemem / 100.0f;
    s.enable_height_synth  = check_height  ? 1.0f : 0.0f;
    s.height_amount        = sl_height   / 100.0f;

    // Grey out Advanced sliders when their module is disabled.
    if (CWnd* w = GetDlgItem(IDC_SLIDER_SCENEMEM)) w->EnableWindow(check_scenemem != 0);
    if (CWnd* w = GetDlgItem(IDC_SLIDER_HEIGHT))   w->EnableWindow(check_height   != 0);

    char _buf[32];
#define SFMT(id, fmt, ...) do { std::snprintf(_buf, sizeof(_buf), fmt, __VA_ARGS__); ::uSetDlgItemText(*this, id, _buf); } while(0)
    SFMT(IDC_AMOUNTT,     "(%.0f%%)",  s.amount       * 100.0f);
    SFMT(IDC_WRAPT,       "(%.0f)",    s.wrap);
    SFMT(IDC_FRONTLOCKT,  "(%.2f)",    s.front_lock);
    SFMT(IDC_REART,       "(%.0f%%)",  s.rear_amount  * 100.0f);
    SFMT(IDC_FOCUST,      "(%+.2f)",   s.focus);
    SFMT(IDC_BASSANCHORT, "(%.0f%%)",  s.bass_anchor  * 100.0f);
    SFMT(IDC_OBJECTST,    "(%.0f%%)",  s.soft_objects * 100.0f);
    SFMT(IDC_VAL_SCENEMEM,"(%.0f%%)",  s.scene_memory_amount * 100.0f);
    SFMT(IDC_VAL_HEIGHT,  "(%.0f%%)",  s.height_amount       * 100.0f);
#undef SFMT
    // NOTE: no cbf call here. notify_preset_change() is called by refresh() after this returns.
}

BEGIN_MESSAGE_MAP(CPrismDialog, CDialog)
    ON_WM_HSCROLL()
    ON_WM_TIMER()
    ON_WM_DESTROY()
    ON_BN_CLICKED(IDC_REDIR,           &CPrismDialog::OnBnClickedRedir)
    ON_BN_CLICKED(IDC_ENABLE_SCENEMEM, &CPrismDialog::OnBnClickedRedir)
    ON_BN_CLICKED(IDC_ENABLE_HEIGHT,   &CPrismDialog::OnBnClickedRedir)
    ON_BN_CLICKED(IDC_RESET,           &CPrismDialog::OnReset)
END_MESSAGE_MAP()

// ---------------------------------------------------------------------------
// g_show_config_popup  — v2 legacy modal path
// cbf is a stack-local in foobar's DSP preferences code; it's valid only while
// this call is on the stack, so we use DoModal() (blocking) to stay safe.
// ---------------------------------------------------------------------------
void prism_dsp::g_show_config_popup(const dsp_preset& p, HWND wnd, dsp_preset_edit_callback& cbf) {
    AFX_MANAGE_STATE(AfxGetStaticModuleState());
    PrismParams params = params_from_preset(p);
    CPrismDialog dlg(params, cbf, wnd);   // stack-allocated; modal constructor
    dlg.DoModal();
    // cbf.on_preset_changed() was called live during DoModal; nothing more to do.
}

// ---------------------------------------------------------------------------
// g_show_config_popup_v3  — v3 modeless path (used by modern foobar2000 v2.x)
// callback is ref-counted; we hold a copy, keeping it alive for the dialog's life.
// ---------------------------------------------------------------------------
service_ptr_t<service_base> prism_dsp::g_show_config_popup_v3(HWND parent, dsp_preset_edit_callback_v2::ptr callback) {
    AFX_MANAGE_STATE(AfxGetStaticModuleState());

    // Double-open guard: bring existing dialog to front.
    if (CPrismDialog::s_active && ::IsWindow(CPrismDialog::s_active->m_hWnd)) {
        ::SetForegroundWindow(CPrismDialog::s_active->m_hWnd);
        return nullptr;
    }

    dsp_preset_impl preset;
    callback->get_preset(preset);
    PrismParams params = params_from_preset(preset);

    // Heap-allocated; self-deletes via PostNcDestroy after window teardown.
    CPrismDialog* dlg = new CPrismDialog(params, callback, parent);
    if (!dlg->Create(CPrismDialog::IDD, nullptr)) {
        delete dlg;
        return nullptr;
    }
    dlg->ShowWindow(SW_SHOW);
    // Return nullptr: dialog manages its own lifetime. Foobar keeps callback alive
    // via the dsp_preset_edit_callback_v2::ptr we stored in the dialog.
    return nullptr;
}
