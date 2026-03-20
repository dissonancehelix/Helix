#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "converter.h"

void print_usage(const char* program_name)
{
    printf("NSF to VGM Converter\n");
    printf("Usage: %s <input.nsf> [output.vgm] [options]\n", program_name);
    printf("\nOptions:\n");
    printf("  -s <number>    Song number to convert (default: 0)\n");
    printf("  -l <seconds>   Recording length in seconds (default: 120)\n");
    printf("  -f <seconds>   Fade out time in seconds (default: 5)\n");
    printf("  -r <rate>      Sample rate in Hz (default: 48000)\n");
    printf("  -ntsc          Force NTSC playback mode (60Hz, default)\n");
    printf("  -pal           Force PAL playback mode (50Hz)\n");
    printf("  -a             Convert all songs\n");
    printf("  -h             Show this help message\n");
    printf("\nExamples:\n");
    printf("  %s input.nsf output.vgm\n", program_name);
    printf("  %s input.nsf output.vgm -s 1 -l 180\n", program_name);
    printf("  %s input.nsf -a -pal\n", program_name);
}

int main(int argc, char* argv[])
{
    const char* input_file = NULL;
    const char* output_file = NULL;
    int song_number = 0;
    int duration_sec = 120;
    int fade_sec = 5;
    int sample_rate = 48000;
    int convert_all = 0;
    playback_mode_t playback_mode = PLAYBACK_MODE_NTSC;  /* Default to NTSC */
    int i;
    int result;

    /* Parse command line arguments */
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    /* Check for help flag first */
    if (strcmp(argv[1], "-h") == 0) {
        print_usage(argv[0]);
        return 0;
    }

    input_file = argv[1];

    /* Check if second argument is an option or output file */
    if (argc > 2 && argv[2][0] != '-') {
        output_file = argv[2];
        i = 3;
    } else {
        i = 2;
    }

    /* Parse options */
    while (i < argc) {
        if (strcmp(argv[i], "-s") == 0 && i + 1 < argc) {
            song_number = atoi(argv[i + 1]);
            i += 2;
        } else if (strcmp(argv[i], "-l") == 0 && i + 1 < argc) {
            duration_sec = atoi(argv[i + 1]);
            i += 2;
        } else if (strcmp(argv[i], "-f") == 0 && i + 1 < argc) {
            fade_sec = atoi(argv[i + 1]);
            i += 2;
        } else if (strcmp(argv[i], "-r") == 0 && i + 1 < argc) {
            sample_rate = atoi(argv[i + 1]);
            i += 2;
        } else if (strcmp(argv[i], "-ntsc") == 0) {
            playback_mode = PLAYBACK_MODE_NTSC;
            i++;
        } else if (strcmp(argv[i], "-pal") == 0) {
            playback_mode = PLAYBACK_MODE_PAL;
            i++;
        } else if (strcmp(argv[i], "-a") == 0) {
            convert_all = 1;
            i++;
        } else if (strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }

    /* Initialize converter */
    if (converter_init() != 0) {
        fprintf(stderr, "Failed to initialize converter\n");
        return 1;
    }

    /* Set playback mode */
    converter_set_playback_mode(playback_mode);

    /* Load NSF file */
    if (converter_load_nsf(input_file) != 0) {
        fprintf(stderr, "Failed to load NSF file: %s\n", input_file);
        converter_cleanup();
        return 1;
    }

    /* Convert songs */
    if (convert_all) {
        int song_count = converter_get_song_count();
        int song;
        char output_path[512];

        printf("Converting all %d songs...\n", song_count);

        for (song = 0; song < song_count; song++) {
            /* Generate output filename */
            if (output_file) {
                /* Use provided output file as base */
                const char* ext = strrchr(output_file, '.');
                if (ext) {
                    snprintf(output_path, sizeof(output_path), "%.*s_%02d%s",
                             (int)(ext - output_file), output_file, song, ext);
                } else {
                    snprintf(output_path, sizeof(output_path), "%s_%02d.vgm",
                             output_file, song);
                }
            } else {
                /* Generate from input filename */
                const char* base = strrchr(input_file, '/');
                if (!base) base = strrchr(input_file, '\\');
                if (!base) base = input_file;
                else base++;

                const char* ext = strrchr(base, '.');
                if (ext) {
                    snprintf(output_path, sizeof(output_path), "output/%.*s_%02d.vgm",
                             (int)(ext - base), base, song);
                } else {
                    snprintf(output_path, sizeof(output_path), "output/%s_%02d.vgm",
                             base, song);
                }
            }

            printf("\n=== Song %d/%d ===\n", song + 1, song_count);
            printf("%s\n", converter_get_song_info(song));

            result = converter_convert(song, output_path, duration_sec);
            if (result != 0) {
                fprintf(stderr, "Failed to convert song %d\n", song);
            }
        }
    } else {
        char output_path[512];

        /* Single song conversion */
        if (output_file) {
            strncpy(output_path, output_file, sizeof(output_path) - 1);
            output_path[sizeof(output_path) - 1] = '\0';
        } else {
            /* Generate output filename from input */
            const char* base = strrchr(input_file, '/');
            if (!base) base = strrchr(input_file, '\\');
            if (!base) base = input_file;
            else base++;

            const char* ext = strrchr(base, '.');
            if (ext) {
                snprintf(output_path, sizeof(output_path), "output/%.*s_%02d.vgm",
                         (int)(ext - base), base, song_number);
            } else {
                snprintf(output_path, sizeof(output_path), "output/%s_%02d.vgm",
                         base, song_number);
            }
        }

        printf("\n%s\n", converter_get_song_info(song_number));

        result = converter_convert(song_number, output_path, duration_sec);
        if (result != 0) {
            fprintf(stderr, "Conversion failed\n");
            converter_cleanup();
            return 1;
        }
    }

    /* Cleanup */
    converter_cleanup();

    printf("\nAll conversions completed successfully!\n");
    return 0;
}
