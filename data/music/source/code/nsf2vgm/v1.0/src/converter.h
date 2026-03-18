#ifndef __CONVERTER_H__
#define __CONVERTER_H__

#ifdef __cplusplus
extern "C" {
#endif

/* PAL/NTSC mode */
typedef enum {
    PLAYBACK_MODE_AUTO = 0,   /* Use NSF file's setting */
    PLAYBACK_MODE_NTSC = 1,   /* Force NTSC (60Hz) */
    PLAYBACK_MODE_PAL = 2     /* Force PAL (50Hz) */
} playback_mode_t;

/* Converter configuration */
typedef struct {
    int song_number;        /* Song number to convert (0-based) */
    int duration_sec;       /* Recording duration in seconds */
    int fade_sec;           /* Fade out duration in seconds */
    int sample_rate;        /* Sample rate (default 48000) */
    int convert_all;        /* Convert all songs flag */
    playback_mode_t mode;   /* Playback mode (NTSC/PAL) */
} converter_config_t;

/* Initialize converter */
int converter_init(void);

/* Set playback mode (PAL/NTSC) */
void converter_set_playback_mode(playback_mode_t mode);

/* Load NSF file */
int converter_load_nsf(const char* filename);

/* Get song count */
int converter_get_song_count(void);

/* Get song information */
const char* converter_get_song_info(int song_number);

/* Convert NSF to VGM */
int converter_convert(int song_number, const char* output_path, int duration_sec);

/* Cleanup converter */
void converter_cleanup(void);

#ifdef __cplusplus
}
#endif

#endif /* __CONVERTER_H__ */
