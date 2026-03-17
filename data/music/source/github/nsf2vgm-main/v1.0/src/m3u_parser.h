#ifndef __M3U_PARSER_H__
#define __M3U_PARSER_H__

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int track_number;
    char title[256];
    int duration_seconds;
    int fade_seconds;
    int intro_seconds;
    char filename[512];
} M3U_Track;

typedef struct {
    M3U_Track *tracks;
    int track_count;
    char nsf_file[512];
} M3U_Playlist;

/* Parse M3U file and return playlist */
M3U_Playlist* m3u_parse(const char *m3u_file);

/* Free playlist memory */
void m3u_free(M3U_Playlist *playlist);

#ifdef __cplusplus
}
#endif

#endif /* __M3U_PARSER_H__ */
