/*
 * M3U Parser for NSF playlists
 * Parses M3U format: filename::NSF,track,title,duration,fade,intro
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#ifdef _WIN32
#include <windows.h>
#endif
#include "m3u_parser.h"

/* Parse time string (HH:MM:SS or MM:SS.ms) to seconds */
static int parse_time(const char *time_str)
{
    int hours = 0, minutes = 0;
    float seconds = 0;
    int parts = sscanf(time_str, "%d:%d:%f", &hours, &minutes, &seconds);

    if (parts == 3) {
        return hours * 3600 + minutes * 60 + (int)seconds + 10;  /* Add 10s for loop/fade */
    } else if (parts == 2) {
        return hours * 60 + (int)minutes + 10;  /* hours is actually minutes here */
    }
    return 120;  /* Default 2 minutes */
}

/* Parse intro time without adding extra seconds */
static int parse_intro_time(const char *time_str)
{
    int hours = 0, minutes = 0;
    float seconds = 0;
    int parts = sscanf(time_str, "%d:%d:%f", &hours, &minutes, &seconds);

    if (parts == 3) {
        return hours * 3600 + minutes * 60 + (int)seconds;
    } else if (parts == 2) {
        return hours * 60 + (int)minutes;  /* hours is actually minutes here */
    }
    return 0;  /* Default no intro */
}

/* Remove invalid filename characters */
static void sanitize_filename(char *name)
{
    const char *invalid = "<>:\"/\\|?*";
    char *p = name;

    while (*p) {
        if (strchr(invalid, *p)) {
            *p = '_';
        }
        p++;
    }

    /* Remove trailing dots and spaces */
    p = name + strlen(name) - 1;
    while (p >= name && (*p == '.' || *p == ' ')) {
        *p = '\0';
        p--;
    }
}

M3U_Playlist* m3u_parse(const char *m3u_file)
{
    FILE *fp;
    char line[2048];
    M3U_Playlist *playlist;
    int capacity = 100;

#ifdef _WIN32
    /* Windows: Try multiple approaches to open the file */
    wchar_t wpath[4096];
    char full_path[4096];
    int result;

    /* First try: Get full path and convert to wide char */
    if (_fullpath(full_path, m3u_file, sizeof(full_path)) != NULL) {
        result = MultiByteToWideChar(CP_ACP, 0, full_path, -1, wpath, 4096);
        if (result > 0) {
            fp = _wfopen(wpath, L"r");
            if (fp) goto file_opened;
        }
    }

    /* Second try: Direct conversion */
    result = MultiByteToWideChar(CP_ACP, 0, m3u_file, -1, wpath, 4096);
    if (result > 0) {
        fp = _wfopen(wpath, L"r");
        if (fp) goto file_opened;
    }

    /* Third try: UTF-8 encoding */
    result = MultiByteToWideChar(CP_UTF8, 0, m3u_file, -1, wpath, 4096);
    if (result > 0) {
        fp = _wfopen(wpath, L"r");
        if (fp) goto file_opened;
    }

    /* All attempts failed */
    fprintf(stderr, "Error: Cannot open M3U file: %s\n", m3u_file);
    return NULL;

file_opened:
    /* File successfully opened */
#else
    fp = fopen(m3u_file, "r");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open M3U file: %s\n", m3u_file);
        return NULL;
    }
#endif

    playlist = (M3U_Playlist*)malloc(sizeof(M3U_Playlist));
    if (!playlist) {
        fclose(fp);
        return NULL;
    }

    playlist->tracks = (M3U_Track*)malloc(capacity * sizeof(M3U_Track));
    if (!playlist->tracks) {
        free(playlist);
        fclose(fp);
        return NULL;
    }

    playlist->track_count = 0;
    playlist->nsf_file[0] = '\0';

    /* Parse M3U file */
    while (fgets(line, sizeof(line), fp)) {
        char *p = line;
        char filename[512], title[256], duration_str[32];
        int track_num;

        /* Skip comments and empty lines */
        while (*p && isspace(*p)) p++;
        if (*p == '#' || *p == '\0') continue;

        /* Parse format: filename::NSF,track,title,duration,fade,intro */
        if (strstr(p, "::NSF,")) {
            char *nsf_marker = strstr(p, "::NSF,");
            size_t filename_len = nsf_marker - p;

            if (filename_len >= sizeof(filename)) filename_len = sizeof(filename) - 1;
            strncpy(filename, p, filename_len);
            filename[filename_len] = '\0';

            /* Parse track number, title, duration, fade, intro */
            p = nsf_marker + 6;  /* Skip "::NSF," */

            if (sscanf(p, "%d,", &track_num) == 1) {
                /* Find title */
                p = strchr(p, ',');
                if (p) {
                    p++;  /* Skip comma */
                    char *title_end = strchr(p, ',');
                    if (title_end) {
                        size_t title_len = title_end - p;
                        if (title_len >= sizeof(title)) title_len = sizeof(title) - 1;
                        strncpy(title, p, title_len);
                        title[title_len] = '\0';

                        /* Find duration */
                        p = title_end + 1;
                        char *duration_end = strchr(p, ',');
                        if (duration_end) {
                            size_t dur_len = duration_end - p;
                            if (dur_len >= sizeof(duration_str)) dur_len = sizeof(duration_str) - 1;
                            strncpy(duration_str, p, dur_len);
                            duration_str[dur_len] = '\0';

                            /* Parse fade time */
                            p = duration_end + 1;
                            char fade_str[32] = {0};
                            char intro_str[32] = {0};
                            char *fade_end = strchr(p, ',');
                            if (fade_end) {
                                size_t fade_len = fade_end - p;
                                if (fade_len >= sizeof(fade_str)) fade_len = sizeof(fade_str) - 1;
                                strncpy(fade_str, p, fade_len);
                                fade_str[fade_len] = '\0';

                                /* Parse intro time */
                                p = fade_end + 1;
                                /* intro might be at end of line, find newline or end */
                                char *intro_end = p;
                                while (*intro_end && *intro_end != '\r' && *intro_end != '\n') {
                                    intro_end++;
                                }
                                size_t intro_len = intro_end - p;
                                if (intro_len >= sizeof(intro_str)) intro_len = sizeof(intro_str) - 1;
                                strncpy(intro_str, p, intro_len);
                                intro_str[intro_len] = '\0';
                            }

                            /* Add track to playlist */
                            if (playlist->track_count >= capacity) {
                                capacity *= 2;
                                M3U_Track *new_tracks = (M3U_Track*)realloc(playlist->tracks, capacity * sizeof(M3U_Track));
                                if (!new_tracks) {
                                    m3u_free(playlist);
                                    fclose(fp);
                                    return NULL;
                                }
                                playlist->tracks = new_tracks;
                            }

                            M3U_Track *track = &playlist->tracks[playlist->track_count];
                            track->track_number = track_num;
                            strncpy(track->title, title, sizeof(track->title) - 1);
                            track->title[sizeof(track->title) - 1] = '\0';
                            sanitize_filename(track->title);
                            track->duration_seconds = parse_time(duration_str);
                            track->fade_seconds = parse_time(fade_str);
                            track->intro_seconds = parse_intro_time(intro_str);
                            strncpy(track->filename, filename, sizeof(track->filename) - 1);
                            track->filename[sizeof(track->filename) - 1] = '\0';

                            /* Store NSF filename from first track */
                            if (playlist->nsf_file[0] == '\0') {
                                strncpy(playlist->nsf_file, filename, sizeof(playlist->nsf_file) - 1);
                                playlist->nsf_file[sizeof(playlist->nsf_file) - 1] = '\0';
                            }

                            playlist->track_count++;
                        }
                    }
                }
            }
        }
    }

    fclose(fp);

    if (playlist->track_count == 0) {
        m3u_free(playlist);
        return NULL;
    }

    return playlist;
}

void m3u_free(M3U_Playlist *playlist)
{
    if (playlist) {
        if (playlist->tracks) {
            free(playlist->tracks);
        }
        free(playlist);
    }
}
