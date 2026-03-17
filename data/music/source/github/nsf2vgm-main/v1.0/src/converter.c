#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#endif
#include "converter.h"
#include "../nezplug.h"
#include "../vgmwrite.h"
#include "format/m_nsf.h"

/* Global NEZPlug context */
static NEZ_PLAY* g_nez = NULL;
static Uint8* g_nsf_data = NULL;
static Uint g_nsf_size = 0;
static playback_mode_t g_playback_mode = PLAYBACK_MODE_NTSC;  /* Default to NTSC */

/* External VGM logging enable flag */
extern int vgmlog_enable;

int converter_init(void)
{
    /* Create NEZPlug instance */
    g_nez = NEZNew();
    if (!g_nez) {
        fprintf(stderr, "Error: Failed to create NEZPlug instance\n");
        return -1;
    }

    /* Initialize VGM system */
    vgm_init();

    /* Set default frequency to 44100 Hz (VGM standard) */
    NEZSetFrequency(g_nez, 44100);

    /* Set stereo output */
    NEZSetChannel(g_nez, 2);

    printf("Converter initialized successfully\n");
    return 0;
}

void converter_set_playback_mode(playback_mode_t mode)
{
    g_playback_mode = mode;

    const char* mode_str = "AUTO";
    if (mode == PLAYBACK_MODE_NTSC) mode_str = "NTSC";
    else if (mode == PLAYBACK_MODE_PAL) mode_str = "PAL";

    printf("Playback mode set to: %s\n", mode_str);
}

int converter_load_nsf(const char* filename)
{
    FILE* fp;
    long file_size;

    if (!g_nez) {
        fprintf(stderr, "Error: Converter not initialized\n");
        return -1;
    }

    /* Open NSF file */
#ifdef _WIN32
    /* Windows: Try multiple approaches to open the file */
    wchar_t wpath[4096];
    char full_path[4096];
    int result;

    /* First try: Get full path and convert to wide char */
    if (_fullpath(full_path, filename, sizeof(full_path)) != NULL) {
        result = MultiByteToWideChar(CP_ACP, 0, full_path, -1, wpath, 4096);
        if (result > 0) {
            fp = _wfopen(wpath, L"rb");
            if (fp) goto file_opened;
        }
    }

    /* Second try: Direct conversion */
    result = MultiByteToWideChar(CP_ACP, 0, filename, -1, wpath, 4096);
    if (result > 0) {
        fp = _wfopen(wpath, L"rb");
        if (fp) goto file_opened;
    }

    /* Third try: UTF-8 encoding */
    result = MultiByteToWideChar(CP_UTF8, 0, filename, -1, wpath, 4096);
    if (result > 0) {
        fp = _wfopen(wpath, L"rb");
        if (fp) goto file_opened;
    }

    /* All attempts failed */
    fprintf(stderr, "Error: Cannot open file: %s\n", filename);
    return -1;

file_opened:
    /* File successfully opened */
#else
    fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open file: %s\n", filename);
        return -1;
    }
#endif

    /* Get file size */
    fseek(fp, 0, SEEK_END);
    file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    /* Allocate buffer */
    g_nsf_data = (Uint8*)malloc(file_size);
    if (!g_nsf_data) {
        fprintf(stderr, "Error: Memory allocation failed\n");
        fclose(fp);
        return -1;
    }

    /* Read file */
    g_nsf_size = fread(g_nsf_data, 1, file_size, fp);
    fclose(fp);

    if (g_nsf_size != file_size) {
        fprintf(stderr, "Error: Failed to read file completely\n");
        free(g_nsf_data);
        g_nsf_data = NULL;
        return -1;
    }

    /* Apply PAL/NTSC mode override BEFORE loading if specified */
    if (g_playback_mode != PLAYBACK_MODE_AUTO && g_nsf_size >= 0x7B) {
        /* Helper function to write 16-bit little-endian value */
        #define WriteWordLE(ptr, val) do { (ptr)[0] = (val) & 0xFF; (ptr)[1] = ((val) >> 8) & 0xFF; } while(0)

        /* Byte 0x7A bit 0: 0=NTSC, 1=PAL */
        if (g_playback_mode == PLAYBACK_MODE_PAL) {
            g_nsf_data[0x7A] |= 0x01;  /* Set PAL bit */

            /* Ensure PAL speed is set (0x78-0x79): 20000 us = 50 Hz */
            if (g_nsf_data[0x78] == 0 && g_nsf_data[0x79] == 0) {
                WriteWordLE(g_nsf_data + 0x78, 0x4E20);  /* 20000 microseconds */
            }

            printf("Forcing PAL mode (50Hz)\n");
        } else if (g_playback_mode == PLAYBACK_MODE_NTSC) {
            g_nsf_data[0x7A] &= ~0x01; /* Clear PAL bit */

            /* Ensure NTSC speed is set (0x6E-0x6F): 16666 us ≈ 60.099 Hz */
            if (g_nsf_data[0x6E] == 0 && g_nsf_data[0x6F] == 0) {
                WriteWordLE(g_nsf_data + 0x6E, 0x411A);  /* 16666 microseconds */
            }

            printf("Forcing NTSC mode (60Hz)\n");
        }

        #undef WriteWordLE
    }

    /* Load NSF into NEZPlug */
    if (NEZLoad(g_nez, g_nsf_data, g_nsf_size) != 0) {
        fprintf(stderr, "Error: Failed to load NSF file\n");
        free(g_nsf_data);
        g_nsf_data = NULL;
        return -1;
    }

    printf("NSF file loaded: %s (%u bytes)\n", filename, g_nsf_size);
    printf("Song count: %d\n", NEZGetSongMax(g_nez));

    return 0;
}

int converter_get_song_count(void)
{
    if (!g_nez) {
        return 0;
    }
    return NEZGetSongMax(g_nez);
}

const char* converter_get_song_info(int song_number)
{
    static char info_buf[256];
    char *title, *artist, *copyright, *detail;

    if (!g_nez) {
        return "No NSF loaded";
    }

    NEZSetSongNo(g_nez, song_number);
    NEZGetFileInfo(&title, &artist, &copyright, &detail);

    snprintf(info_buf, sizeof(info_buf), "Song %d: %s - %s",
             song_number, title ? title : "Unknown", artist ? artist : "Unknown");

    return info_buf;
}

int converter_convert(int song_number, const char* output_path, int duration_sec)
{
    Uint32 sample_rate;
    Uint32 total_samples;
    Uint32 samples_rendered = 0;
    Int16* audio_buffer;
    Uint32 buffer_size;
    Uint32 samples_per_render;
    int progress_percent = 0;
    int last_progress = -1;

    if (!g_nez) {
        fprintf(stderr, "Error: Converter not initialized\n");
        return -1;
    }

    /* Get sample rate */
    sample_rate = NEZGetFrequency(g_nez);

    /* Calculate total samples to render */
    total_samples = sample_rate * duration_sec;

    /* Set output path for VGM */
    vgm_setpath(output_path);

    /* Enable VGM logging */
    vgmlog_enable = 1;

    /* Set song number */
    NEZSetSongNo(g_nez, song_number);

    /* Reset player (this triggers vgm_start) */
    NEZReset(g_nez);

    printf("Converting song %d to VGM...\n", song_number);
    printf("Output: %s\n", output_path);
    printf("Duration: %d seconds\n", duration_sec);
    printf("Sample rate: %u Hz\n", sample_rate);

    /* Allocate audio buffer (1 second worth of samples) */
    samples_per_render = sample_rate;
    buffer_size = samples_per_render * 2 * sizeof(Int16); /* stereo */
    audio_buffer = (Int16*)malloc(buffer_size);
    if (!audio_buffer) {
        fprintf(stderr, "Error: Memory allocation failed\n");
        vgmlog_enable = 0;
        return -1;
    }

    /* Render loop */
    while (samples_rendered < total_samples) {
        Uint32 samples_to_render = samples_per_render;

        /* Adjust for last chunk */
        if (samples_rendered + samples_to_render > total_samples) {
            samples_to_render = total_samples - samples_rendered;
        }

        /* Render audio (this also records VGM data) */
        NEZRender(g_nez, audio_buffer, samples_to_render);

        samples_rendered += samples_to_render;

        /* Update progress */
        progress_percent = (samples_rendered * 100) / total_samples;
        if (progress_percent != last_progress) {
            printf("\rProgress: %d%%", progress_percent);
            fflush(stdout);
            last_progress = progress_percent;
        }
    }

    printf("\rProgress: 100%%\n");

    /* Stop VGM recording (this finalizes the VGM file) */
    NEZStop(g_nez);

    /* Disable VGM logging */
    vgmlog_enable = 0;

    /* Free audio buffer */
    free(audio_buffer);

    printf("Conversion completed successfully\n");

    return 0;
}

void converter_cleanup(void)
{
    if (g_nsf_data) {
        free(g_nsf_data);
        g_nsf_data = NULL;
    }

    if (g_nez) {
        NEZDelete(g_nez);
        g_nez = NULL;
    }

    printf("Converter cleaned up\n");
}
