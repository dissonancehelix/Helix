/*
 * NSF to VGM Batch Converter with M3U support
 * Converts all tracks from an M3U playlist to VGM files
 * Now supports automatic extraction from 7z/ZIP archives
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "converter.h"
#include "m3u_parser.h"
#include "archive_utils.h"
#include "../vgmwrite.h"

#ifdef _WIN32
#include <direct.h>
#include <windows.h>
#define mkdir(path, mode) _mkdir(path)
#else
#include <sys/stat.h>
#include <sys/types.h>
#endif

/* Remove directory recursively */
static void remove_directory_recursive(const char *path)
{
#ifdef _WIN32
    WIN32_FIND_DATAA find_data;
    HANDLE hFind;
    char search_path[2048];
    char file_path[2048];

    snprintf(search_path, sizeof(search_path), "%s\\*", path);
    hFind = FindFirstFileA(search_path, &find_data);

    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            if (strcmp(find_data.cFileName, ".") == 0 || strcmp(find_data.cFileName, "..") == 0)
                continue;

            snprintf(file_path, sizeof(file_path), "%s\\%s", path, find_data.cFileName);

            if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                remove_directory_recursive(file_path);
            } else {
                DeleteFileA(file_path);
            }
        } while (FindNextFileA(hFind, &find_data));

        FindClose(hFind);
    }

    RemoveDirectoryA(path);
#else
    /* Unix/Linux implementation would go here */
#endif
}

/* Sanitize filename by removing problematic characters for file operations */
static void sanitize_path_for_copy(const char *src, char *dst, size_t dst_size)
{
    size_t i, j = 0;

    for (i = 0; src[i] != '\0' && j < dst_size - 1; i++) {
        char c = src[i];
        /* Keep most characters, only remove the most problematic ones for Windows paths */
        if (c != '<' && c != '>' && c != '"' && c != '|' && c != '?' && c != '*') {
            dst[j++] = c;
        }
    }
    dst[j] = '\0';
}

/* Extract directory name from M3U path for output folder */
static void extract_folder_name(const char *m3u_path, char *folder_name, size_t folder_name_size)
{
    const char *last_slash = strrchr(m3u_path, '/');
    const char *last_backslash = strrchr(m3u_path, '\\');
    const char *path_sep = last_slash > last_backslash ? last_slash : last_backslash;
    const char *filename_start;
    const char *dot;
    size_t len;

    if (path_sep) {
        /* M3U is in a subdirectory, extract the directory name */
        const char *prev_slash = path_sep - 1;

        /* Find the previous separator */
        while (prev_slash >= m3u_path && *prev_slash != '/' && *prev_slash != '\\') {
            prev_slash--;
        }
        prev_slash++;

        /* Copy folder name */
        len = path_sep - prev_slash;
        if (len >= folder_name_size) len = folder_name_size - 1;
        strncpy(folder_name, prev_slash, len);
        folder_name[len] = '\0';
    } else {
        /* M3U is in current directory, use filename without extension */
        filename_start = m3u_path;

        /* Skip leading "./" or ".\\" */
        if (filename_start[0] == '.' && (filename_start[1] == '/' || filename_start[1] == '\\')) {
            filename_start += 2;
        }

        /* Find the last dot for extension */
        dot = strrchr(filename_start, '.');

        if (dot && dot > filename_start) {
            len = dot - filename_start;
        } else {
            len = strlen(filename_start);
        }

        if (len >= folder_name_size) len = folder_name_size - 1;
        strncpy(folder_name, filename_start, len);
        folder_name[len] = '\0';
    }

    /* If folder name is empty, use default */
    if (folder_name[0] == '\0') {
        strncpy(folder_name, "output", folder_name_size - 1);
        folder_name[folder_name_size - 1] = '\0';
    }
}

/* Copy file to a safe temporary location with simple name */
static int copy_to_temp(const char *src_path, char *temp_path, size_t temp_path_size)
{
    FILE *src_fp, *dst_fp;
    unsigned char buffer[8192];
    size_t bytes_read;

    /* Generate temp filename */
    snprintf(temp_path, temp_path_size, ".nsf2vgm_temp.nsf");

#ifdef _WIN32
    /* Windows: Try multiple approaches to open the file */
    wchar_t wsrc[4096], wdst[4096];
    char full_path[4096];
    int result;

    /* Try to open source file with multiple encodings */
    src_fp = NULL;
    if (_fullpath(full_path, src_path, sizeof(full_path)) != NULL) {
        result = MultiByteToWideChar(CP_ACP, 0, full_path, -1, wsrc, 4096);
        if (result > 0) {
            src_fp = _wfopen(wsrc, L"rb");
        }
    }
    if (!src_fp) {
        result = MultiByteToWideChar(CP_ACP, 0, src_path, -1, wsrc, 4096);
        if (result > 0) {
            src_fp = _wfopen(wsrc, L"rb");
        }
    }
    if (!src_fp) {
        result = MultiByteToWideChar(CP_UTF8, 0, src_path, -1, wsrc, 4096);
        if (result > 0) {
            src_fp = _wfopen(wsrc, L"rb");
        }
    }
    if (!src_fp) {
        fprintf(stderr, "Error: Cannot open source file: %s\n", src_path);
        return -1;
    }

    /* Open destination file */
    if (MultiByteToWideChar(CP_ACP, 0, temp_path, -1, wdst, 4096) == 0) {
        fprintf(stderr, "Error: Failed to convert temp path\n");
        fclose(src_fp);
        return -1;
    }

    dst_fp = _wfopen(wdst, L"wb");
    if (!dst_fp) {
        fprintf(stderr, "Error: Cannot create temp file: %s\n", temp_path);
        fclose(src_fp);
        return -1;
    }
#else
    src_fp = fopen(src_path, "rb");
    if (!src_fp) {
        fprintf(stderr, "Error: Cannot open source file: %s\n", src_path);
        return -1;
    }

    dst_fp = fopen(temp_path, "wb");
    if (!dst_fp) {
        fprintf(stderr, "Error: Cannot create temp file: %s\n", temp_path);
        fclose(src_fp);
        return -1;
    }
#endif

    /* Copy file */
    while ((bytes_read = fread(buffer, 1, sizeof(buffer), src_fp)) > 0) {
        if (fwrite(buffer, 1, bytes_read, dst_fp) != bytes_read) {
            fprintf(stderr, "Error: Failed to write to temp file\n");
            fclose(src_fp);
            fclose(dst_fp);
            remove(temp_path);
            return -1;
        }
    }

    fclose(src_fp);
    fclose(dst_fp);

    printf("Created temporary file: %s\n", temp_path);
    return 0;
}

/* Copy M3U file to temp location and update NSF path */
static int copy_m3u_to_temp(const char *src_m3u, char *temp_m3u, size_t temp_m3u_size)
{
    FILE *src_fp, *dst_fp;
    char line[2048];

    /* Generate temp M3U filename */
    snprintf(temp_m3u, temp_m3u_size, ".nsf2vgm_temp.m3u");

#ifdef _WIN32
    /* Windows: Try multiple approaches to open the file */
    wchar_t wsrc[4096], wdst[4096];
    char full_path[4096];
    int result;

    /* Try to open source file with multiple encodings */
    src_fp = NULL;
    if (_fullpath(full_path, src_m3u, sizeof(full_path)) != NULL) {
        result = MultiByteToWideChar(CP_ACP, 0, full_path, -1, wsrc, 4096);
        if (result > 0) {
            src_fp = _wfopen(wsrc, L"r");
        }
    }
    if (!src_fp) {
        result = MultiByteToWideChar(CP_ACP, 0, src_m3u, -1, wsrc, 4096);
        if (result > 0) {
            src_fp = _wfopen(wsrc, L"r");
        }
    }
    if (!src_fp) {
        result = MultiByteToWideChar(CP_UTF8, 0, src_m3u, -1, wsrc, 4096);
        if (result > 0) {
            src_fp = _wfopen(wsrc, L"r");
        }
    }
    if (!src_fp) {
        return -1;
    }

    /* Open destination file */
    if (MultiByteToWideChar(CP_ACP, 0, temp_m3u, -1, wdst, 4096) == 0) {
        fclose(src_fp);
        return -1;
    }

    dst_fp = _wfopen(wdst, L"w");
    if (!dst_fp) {
        fclose(src_fp);
        return -1;
    }
#else
    src_fp = fopen(src_m3u, "r");
    if (!src_fp) {
        return -1;
    }

    dst_fp = fopen(temp_m3u, "w");
    if (!dst_fp) {
        fclose(src_fp);
        return -1;
    }
#endif

    /* Copy M3U file, replacing NSF filename with temp name */
    while (fgets(line, sizeof(line), src_fp)) {
        /* Replace NSF filename in the line */
        if (strstr(line, "::NSF,")) {
            char *nsf_marker = strstr(line, "::NSF,");
            /* Write temp NSF filename */
            fprintf(dst_fp, ".nsf2vgm_temp.nsf%s", nsf_marker);
        } else {
            fputs(line, dst_fp);
        }
    }

    fclose(src_fp);
    fclose(dst_fp);

    printf("Created temporary M3U file: %s\n", temp_m3u);
    return 0;
}

static void print_usage(const char *program_name)
{
    printf("NSF to VGM Batch Converter (M3U support + Archive extraction)\n");
    printf("Usage: %s <input> [output_dir]\n", program_name);
    printf("\nInput formats:\n");
    printf("  .m3u         M3U playlist file\n");
    printf("  .7z          7z archive containing NSF and M3U\n");
    printf("  .zip         ZIP archive containing NSF and M3U\n");
    printf("\nOptions:\n");
    printf("  output_dir   Output directory (default: auto-generated)\n");
    printf("\nExamples:\n");
    printf("  %s playlist.m3u kirby_vgm\n", program_name);
    printf("  %s \"Kirby's Adventure.7z\"\n", program_name);
    printf("  %s game.zip output\n", program_name);
    printf("\nNote: When using archives, VGM files will be packed into a ZIP file.\n");
}

int main(int argc, char *argv[])
{
    const char *input_file;
    char output_dir[1024];
    char folder_name[512];
    M3U_Playlist *playlist;
    char nsf_path[2048];
    char temp_nsf_path[1024];
    char temp_m3u_path[1024];
    char output_path[2048];
    char m3u_dir[1024];
    char temp_extract_dir[1024];
    char m3u_file[2048];
    int i;
    int success_count = 0;
    int use_temp_files = 0;
    int is_archive = 0;
    int should_create_zip = 0;
    const char *m3u_to_parse;
    ArchiveType archive_type;

    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    input_file = argv[1];

    /* Detect if input is an archive */
    archive_type = archive_detect_type(input_file);
    is_archive = (archive_type != ARCHIVE_TYPE_UNKNOWN);

    if (is_archive) {
        /* Extract archive to temporary directory */
        printf("Detected archive file: %s\n", input_file);

        snprintf(temp_extract_dir, sizeof(temp_extract_dir), ".nsf2vgm_extract_%d", (int)time(NULL));

        if (archive_extract(input_file, temp_extract_dir) != 0) {
            fprintf(stderr, "Error: Failed to extract archive\n");
            return 1;
        }

        /* Find M3U file in extracted directory */
#ifdef _WIN32
        WIN32_FIND_DATAA find_data;
        HANDLE hFind;
        char search_path[2048];
        int found_m3u = 0;

        snprintf(search_path, sizeof(search_path), "%s\\*.m3u", temp_extract_dir);
        hFind = FindFirstFileA(search_path, &find_data);

        if (hFind != INVALID_HANDLE_VALUE) {
            snprintf(m3u_file, sizeof(m3u_file), "%s\\%s", temp_extract_dir, find_data.cFileName);
            found_m3u = 1;
            FindClose(hFind);
        }

        if (!found_m3u) {
            fprintf(stderr, "Error: No M3U file found in archive\n");
            remove_directory_recursive(temp_extract_dir);
            return 1;
        }
#else
        fprintf(stderr, "Error: Archive extraction not fully implemented for this platform\n");
        return 1;
#endif

        should_create_zip = 1;
    } else {
        /* Input is M3U file directly */
        strncpy(m3u_file, input_file, sizeof(m3u_file) - 1);
        m3u_file[sizeof(m3u_file) - 1] = '\0';
    }

    /* Extract folder name from input path and create output directory name */
    extract_folder_name(input_file, folder_name, sizeof(folder_name));
    if (argc > 2) {
        /* User specified output directory */
        strncpy(output_dir, argv[2], sizeof(output_dir) - 1);
        output_dir[sizeof(output_dir) - 1] = '\0';
    } else {
        /* Auto-generate output directory: folder_name + "_vgm" */
        snprintf(output_dir, sizeof(output_dir), "%s_vgm", folder_name);
    }

    /* Get M3U directory for NSF file path */
    strncpy(m3u_dir, m3u_file, sizeof(m3u_dir) - 1);
    m3u_dir[sizeof(m3u_dir) - 1] = '\0';
    char *last_slash = strrchr(m3u_dir, '/');
    if (!last_slash) last_slash = strrchr(m3u_dir, '\\');
    if (last_slash) {
        *(last_slash + 1) = '\0';
    } else {
        m3u_dir[0] = '\0';
    }

    /* Try to copy M3U and NSF to temp locations if paths are problematic */
    printf("Preparing files...\n");

    /* First, try to parse M3U directly to get NSF filename */
    M3U_Playlist *temp_playlist = m3u_parse(m3u_file);
    if (temp_playlist) {
        /* M3U opened successfully, use it directly */
        m3u_to_parse = m3u_file;
        snprintf(nsf_path, sizeof(nsf_path), "%s%s", m3u_dir, temp_playlist->nsf_file);
        m3u_free(temp_playlist);
        printf("Using original files directly\n");
    } else {
        /* M3U failed to open, try temp file approach */
        printf("Direct access failed, creating temporary files...\n");

        if (copy_m3u_to_temp(m3u_file, temp_m3u_path, sizeof(temp_m3u_path)) != 0) {
            fprintf(stderr, "Error: Failed to create temporary M3U file\n");
            return 1;
        }

        /* Parse temp M3U to get NSF filename */
        temp_playlist = m3u_parse(temp_m3u_path);
        if (!temp_playlist) {
            fprintf(stderr, "Error: Failed to parse temporary M3U file\n");
            remove(temp_m3u_path);
            return 1;
        }

        /* Build original NSF path */
        snprintf(nsf_path, sizeof(nsf_path), "%s%s", m3u_dir, temp_playlist->nsf_file);
        m3u_free(temp_playlist);

        /* Copy NSF to temp location */
        if (copy_to_temp(nsf_path, temp_nsf_path, sizeof(temp_nsf_path)) != 0) {
            fprintf(stderr, "Error: Failed to create temporary NSF file\n");
            remove(temp_m3u_path);
            return 1;
        }

        m3u_to_parse = temp_m3u_path;
        use_temp_files = 1;
    }

    /* Parse M3U file */
    printf("Parsing M3U file: %s\n", m3u_to_parse);
    playlist = m3u_parse(m3u_to_parse);
    if (!playlist) {
        fprintf(stderr, "Error: Failed to parse M3U file\n");
        if (use_temp_files) {
            remove(temp_m3u_path);
            remove(temp_nsf_path);
        }
        return 1;
    }

    printf("Found %d tracks\n", playlist->track_count);
    printf("NSF file: %s\n", nsf_path);

    /* Create output directory */
    mkdir(output_dir, 0755);
    printf("Output directory: %s\n\n", output_dir);

    /* Initialize converter */
    if (converter_init() != 0) {
        fprintf(stderr, "Error: Failed to initialize converter\n");
        if (use_temp_files) {
            remove(temp_m3u_path);
            remove(temp_nsf_path);
        }
        m3u_free(playlist);
        return 1;
    }

    /* Set NTSC mode */
    converter_set_playback_mode(PLAYBACK_MODE_NTSC);

    /* Load NSF file */
    const char *nsf_to_load = use_temp_files ? temp_nsf_path : nsf_path;
    if (converter_load_nsf(nsf_to_load) != 0) {
        fprintf(stderr, "Error: Failed to load NSF file\n");
        converter_cleanup();
        if (use_temp_files) {
            remove(temp_m3u_path);
            remove(temp_nsf_path);
        }
        m3u_free(playlist);
        return 1;
    }

    /* Convert all tracks */
    for (i = 0; i < playlist->track_count; i++) {
        M3U_Track *track = &playlist->tracks[i];

        printf("[%d/%d] Track %d: %s (%ds, intro: %ds)\n",
               i + 1, playlist->track_count,
               track->track_number, track->title, track->duration_seconds, track->intro_seconds);

        /* Build output filename: "01 Name.vgm" */
        snprintf(output_path, sizeof(output_path), "%s/%02d %s.vgm",
                 output_dir, track->track_number, track->title);

        /* Set track info for GD3 tag */
        vgm_set_track_info(track->title, "Denjhang");

        /* Set loop point (intro length in samples at 44100 Hz) */
        if (track->intro_seconds > 0) {
            vgm_set_loop_point(track->intro_seconds * 44100);
        }

        /* Convert track */
        if (converter_convert(track->track_number, output_path, track->duration_seconds) == 0) {
            printf("  ✓ Success: %s\n", output_path);
            success_count++;
        } else {
            printf("  ✗ Failed\n");
        }
        printf("\n");
    }

    /* Cleanup */
    converter_cleanup();

    /* Remove temp files if created */
    if (use_temp_files) {
        remove(temp_m3u_path);
        remove(temp_nsf_path);
        printf("Removed temporary files\n");
    }

    printf("Conversion complete: %d/%d tracks successful\n", success_count, playlist->track_count);

    /* Generate M3U playlist for VGM files */
    if (success_count > 0) {
        char m3u_path[1024];
        FILE *m3u_fp;

        /* Use simple "playlist.m3u" filename */
        snprintf(m3u_path, sizeof(m3u_path), "%s/playlist.m3u", output_dir);
        m3u_fp = fopen(m3u_path, "w");
        if (m3u_fp) {
            printf("\nGenerating M3U playlist: %s\n", m3u_path);

            for (i = 0; i < playlist->track_count; i++) {
                M3U_Track *track = &playlist->tracks[i];
                fprintf(m3u_fp, "%02d %s.vgm\n", track->track_number, track->title);
            }

            fclose(m3u_fp);
            printf("M3U playlist created successfully\n");
        } else {
            fprintf(stderr, "Warning: Failed to create M3U playlist\n");
        }
    }

    m3u_free(playlist);

    /* If input was an archive, create ZIP of output and cleanup */
    if (is_archive && should_create_zip && success_count > 0) {
        char zip_path[1024];
        snprintf(zip_path, sizeof(zip_path), "%s.zip", folder_name);

        printf("\nCreating output ZIP archive: %s\n", zip_path);
        if (archive_create_zip(output_dir, zip_path) == 0) {
            printf("Output ZIP created successfully\n");

            /* Remove output directory after successful ZIP creation */
            printf("Cleaning up output directory...\n");
            remove_directory_recursive(output_dir);
        } else {
            fprintf(stderr, "Warning: Failed to create output ZIP\n");
        }

        /* Remove temporary extraction directory */
        printf("Cleaning up temporary files...\n");
        remove_directory_recursive(temp_extract_dir);
    }

    return (success_count == playlist->track_count) ? 0 : 1;
}
