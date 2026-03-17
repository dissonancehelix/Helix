/*
 * Archive Utilities - 7z/ZIP extraction and ZIP creation
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "archive_utils.h"
#include "7z/7z.h"
#include "7z/7zAlloc.h"
#include "7z/7zCrc.h"
#include "7z/7zFile.h"
#include "7z/7zBuf.h"
#include "zlib/zlib.h"

#ifdef _WIN32
#include <direct.h>
#include <windows.h>
#define mkdir(path, mode) _mkdir(path)
#else
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

#define kInputBufSize ((size_t)1 << 18)

static const ISzAlloc g_Alloc = { SzAlloc, SzFree };

/* Case-insensitive string compare */
static int stricmp_local(const char *s1, const char *s2)
{
    while (*s1 && *s2)
    {
        int c1 = tolower((unsigned char)*s1);
        int c2 = tolower((unsigned char)*s2);
        if (c1 != c2) return c1 - c2;
        s1++;
        s2++;
    }
    return tolower((unsigned char)*s1) - tolower((unsigned char)*s2);
}

/* Detect archive type from file extension */
ArchiveType archive_detect_type(const char *filename)
{
    const char *ext = strrchr(filename, '.');
    if (!ext) return ARCHIVE_TYPE_UNKNOWN;

    if (stricmp_local(ext, ".7z") == 0)
        return ARCHIVE_TYPE_7Z;
    if (stricmp_local(ext, ".zip") == 0)
        return ARCHIVE_TYPE_ZIP;

    return ARCHIVE_TYPE_UNKNOWN;
}

/* Create directory recursively */
static int create_directory_recursive(const char *path)
{
    char tmp[1024];
    char *p = NULL;
    size_t len;

    snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if (tmp[len - 1] == '/' || tmp[len - 1] == '\\')
        tmp[len - 1] = 0;

    for (p = tmp + 1; *p; p++) {
        if (*p == '/' || *p == '\\') {
            *p = 0;
            mkdir(tmp, 0755);
            *p = '/';
        }
    }
    return mkdir(tmp, 0755);
}

/* Extract all files from 7z archive to directory */
int archive_extract_7z(const char *archive_path, const char *output_dir)
{
    CFileInStream archiveStream;
    CLookToRead2 lookStream;
    CSzArEx db;
    SRes res;
    UInt16 *temp = NULL;
    size_t tempSize = 0;
    int result = -1;

    printf("Extracting 7z archive: %s\n", archive_path);

    /* Create output directory */
    create_directory_recursive(output_dir);

    /* Open archive file */
    if (InFile_Open(&archiveStream.file, archive_path)) {
        fprintf(stderr, "Error: Cannot open 7z archive: %s\n", archive_path);
        return -1;
    }

    FileInStream_CreateVTable(&archiveStream);
    LookToRead2_CreateVTable(&lookStream, False);
    lookStream.buf = NULL;

    res = SZ_OK;

    /* Allocate lookup buffer */
    lookStream.buf = (Byte *)ISzAlloc_Alloc(&g_Alloc, kInputBufSize);
    if (!lookStream.buf)
        res = SZ_ERROR_MEM;
    else
    {
        lookStream.bufSize = kInputBufSize;
        lookStream.realStream = &archiveStream.vt;
        LookToRead2_INIT(&lookStream)
    }

    CrcGenerateTable();
    SzArEx_Init(&db);

    if (res == SZ_OK)
    {
        res = SzArEx_Open(&db, &lookStream.vt, &g_Alloc, &g_Alloc);
    }

    if (res == SZ_OK)
    {
        UInt32 i;
        UInt32 blockIndex = 0xFFFFFFFF;
        Byte *outBuffer = NULL;
        size_t outBufferSize = 0;

        /* Extract all files */
        for (i = 0; i < db.NumFiles; i++)
        {
            size_t offset = 0;
            size_t outSizeProcessed = 0;
            size_t len;
            BoolInt isDir = SzArEx_IsDir(&db, i);

            if (isDir)
                continue;

            len = SzArEx_GetFileNameUtf16(&db, i, NULL);
            if (len > tempSize)
            {
                SzFree(NULL, temp);
                tempSize = len;
                temp = (UInt16 *)SzAlloc(NULL, tempSize * sizeof(temp[0]));
                if (!temp)
                {
                    res = SZ_ERROR_MEM;
                    break;
                }
            }

            SzArEx_GetFileNameUtf16(&db, i, temp);

            /* Convert UTF-16 to ASCII */
            char name[1024];
            size_t j;
            for (j = 0; j < len && j < 1023; j++)
                name[j] = (char)temp[j];
            name[j] = 0;

            /* Build output path */
            char output_path[2048];
            snprintf(output_path, sizeof(output_path), "%s/%s", output_dir, name);

            /* Create subdirectories if needed */
            char *last_slash = strrchr(output_path, '/');
            if (!last_slash) last_slash = strrchr(output_path, '\\');
            if (last_slash) {
                char dir_path[2048];
                size_t dir_len = last_slash - output_path;
                strncpy(dir_path, output_path, dir_len);
                dir_path[dir_len] = 0;
                create_directory_recursive(dir_path);
            }

            /* Extract this file */
            res = SzArEx_Extract(&db, &lookStream.vt, i,
                &blockIndex, &outBuffer, &outBufferSize,
                &offset, &outSizeProcessed,
                &g_Alloc, &g_Alloc);

            if (res == SZ_OK)
            {
                /* Write to file */
                FILE *fp = fopen(output_path, "wb");
                if (fp) {
                    fwrite(outBuffer + offset, 1, outSizeProcessed, fp);
                    fclose(fp);
                    printf("  Extracted: %s (%zu bytes)\n", name, outSizeProcessed);
                } else {
                    fprintf(stderr, "  Error: Cannot create file: %s\n", output_path);
                }
            }
        }

        if (outBuffer)
            ISzAlloc_Free(&g_Alloc, outBuffer);

        result = 0;
    }

    SzArEx_Free(&db, &g_Alloc);
    SzFree(NULL, temp);

    if (lookStream.buf)
        ISzAlloc_Free(&g_Alloc, lookStream.buf);

    File_Close(&archiveStream.file);

    return result;
}

/* ZIP file structures */
#define ZIP_LOCAL_FILE_HEADER_SIGNATURE 0x04034b50
#define ZIP_CENTRAL_DIR_SIGNATURE 0x02014b50
#define ZIP_END_CENTRAL_DIR_SIGNATURE 0x06054b50

#pragma pack(push, 1)
typedef struct {
    uint32_t signature;
    uint16_t version;
    uint16_t flags;
    uint16_t compression;
    uint16_t mod_time;
    uint16_t mod_date;
    uint32_t crc32;
    uint32_t compressed_size;
    uint32_t uncompressed_size;
    uint16_t filename_length;
    uint16_t extra_length;
} ZipLocalFileHeader;

typedef struct {
    uint32_t signature;
    uint16_t version_made;
    uint16_t version_needed;
    uint16_t flags;
    uint16_t compression;
    uint16_t mod_time;
    uint16_t mod_date;
    uint32_t crc32;
    uint32_t compressed_size;
    uint32_t uncompressed_size;
    uint16_t filename_length;
    uint16_t extra_length;
    uint16_t comment_length;
    uint16_t disk_start;
    uint16_t internal_attr;
    uint32_t external_attr;
    uint32_t local_header_offset;
} ZipCentralDirEntry;

typedef struct {
    uint32_t signature;
    uint16_t disk_number;
    uint16_t central_dir_disk;
    uint16_t num_entries_disk;
    uint16_t num_entries;
    uint32_t central_dir_size;
    uint32_t central_dir_offset;
    uint16_t comment_length;
} ZipEndCentralDir;
#pragma pack(pop)

/* Extract all files from ZIP archive to directory */
int archive_extract_zip(const char *archive_path, const char *output_dir)
{
    FILE *fp;
    ZipLocalFileHeader header;
    char filename[1024];
    unsigned char *compressed_data = NULL;
    unsigned char *uncompressed_data = NULL;
    int result = -1;

    printf("Extracting ZIP archive: %s\n", archive_path);

    /* Create output directory */
    create_directory_recursive(output_dir);

    fp = fopen(archive_path, "rb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open ZIP archive: %s\n", archive_path);
        return -1;
    }

    /* Read and extract each file */
    while (fread(&header, sizeof(ZipLocalFileHeader), 1, fp) == 1) {
        if (header.signature != ZIP_LOCAL_FILE_HEADER_SIGNATURE)
            break;

        /* Read filename */
        if (header.filename_length >= sizeof(filename)) {
            fprintf(stderr, "Error: Filename too long\n");
            fseek(fp, header.filename_length + header.extra_length + header.compressed_size, SEEK_CUR);
            continue;
        }

        fread(filename, 1, header.filename_length, fp);
        filename[header.filename_length] = 0;

        /* Skip extra field */
        if (header.extra_length > 0)
            fseek(fp, header.extra_length, SEEK_CUR);

        /* Skip directories */
        if (filename[header.filename_length - 1] == '/' || filename[header.filename_length - 1] == '\\') {
            fseek(fp, header.compressed_size, SEEK_CUR);
            continue;
        }

        /* Build output path */
        char output_path[2048];
        snprintf(output_path, sizeof(output_path), "%s/%s", output_dir, filename);

        /* Create subdirectories if needed */
        char *last_slash = strrchr(output_path, '/');
        if (!last_slash) last_slash = strrchr(output_path, '\\');
        if (last_slash) {
            char dir_path[2048];
            size_t dir_len = last_slash - output_path;
            strncpy(dir_path, output_path, dir_len);
            dir_path[dir_len] = 0;
            create_directory_recursive(dir_path);
        }

        /* Read compressed data */
        compressed_data = (unsigned char *)malloc(header.compressed_size);
        if (!compressed_data) {
            fprintf(stderr, "Error: Out of memory\n");
            goto cleanup;
        }

        fread(compressed_data, 1, header.compressed_size, fp);

        /* Decompress if needed */
        if (header.compression == 0) {
            /* Stored (no compression) */
            FILE *out_fp = fopen(output_path, "wb");
            if (out_fp) {
                fwrite(compressed_data, 1, header.compressed_size, out_fp);
                fclose(out_fp);
                printf("  Extracted: %s (%u bytes)\n", filename, header.uncompressed_size);
            } else {
                fprintf(stderr, "  Error: Cannot create file: %s\n", output_path);
            }
        } else if (header.compression == 8) {
            /* Deflate compression */
            uncompressed_data = (unsigned char *)malloc(header.uncompressed_size);
            if (!uncompressed_data) {
                fprintf(stderr, "Error: Out of memory\n");
                free(compressed_data);
                goto cleanup;
            }

            z_stream stream;
            memset(&stream, 0, sizeof(stream));
            stream.next_in = compressed_data;
            stream.avail_in = header.compressed_size;
            stream.next_out = uncompressed_data;
            stream.avail_out = header.uncompressed_size;

            if (inflateInit2(&stream, -MAX_WBITS) == Z_OK) {
                if (inflate(&stream, Z_FINISH) == Z_STREAM_END) {
                    FILE *out_fp = fopen(output_path, "wb");
                    if (out_fp) {
                        fwrite(uncompressed_data, 1, header.uncompressed_size, out_fp);
                        fclose(out_fp);
                        printf("  Extracted: %s (%u bytes)\n", filename, header.uncompressed_size);
                    } else {
                        fprintf(stderr, "  Error: Cannot create file: %s\n", output_path);
                    }
                } else {
                    fprintf(stderr, "  Error: Decompression failed for: %s\n", filename);
                }
                inflateEnd(&stream);
            }

            free(uncompressed_data);
            uncompressed_data = NULL;
        } else {
            fprintf(stderr, "  Warning: Unsupported compression method %d for: %s\n", header.compression, filename);
        }

        free(compressed_data);
        compressed_data = NULL;
    }

    result = 0;

cleanup:
    if (compressed_data) free(compressed_data);
    if (uncompressed_data) free(uncompressed_data);
    fclose(fp);

    return result;
}

/* Calculate CRC32 for a file */
static uint32_t calculate_crc32(const char *filepath)
{
    FILE *fp = fopen(filepath, "rb");
    if (!fp) return 0;

    uint32_t crc = crc32(0L, Z_NULL, 0);
    unsigned char buffer[8192];
    size_t bytes_read;

    while ((bytes_read = fread(buffer, 1, sizeof(buffer), fp)) > 0) {
        crc = crc32(crc, buffer, bytes_read);
    }

    fclose(fp);
    return crc;
}

/* Get file size */
static long get_file_size(const char *filepath)
{
    FILE *fp = fopen(filepath, "rb");
    if (!fp) return 0;

    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fclose(fp);

    return size;
}

/* Create ZIP archive from directory */
int archive_create_zip(const char *source_dir, const char *zip_path)
{
    FILE *zip_fp;
    uint32_t central_dir_offset = 0;
    uint32_t central_dir_size = 0;
    uint16_t num_entries = 0;

    printf("Creating ZIP archive: %s\n", zip_path);

    zip_fp = fopen(zip_path, "wb");
    if (!zip_fp) {
        fprintf(stderr, "Error: Cannot create ZIP file: %s\n", zip_path);
        return -1;
    }

    /* Temporary storage for central directory entries */
    typedef struct {
        char filename[512];
        uint32_t crc32;
        uint32_t compressed_size;
        uint32_t uncompressed_size;
        uint32_t local_header_offset;
    } FileEntry;

    FileEntry *entries = NULL;
    int entries_capacity = 100;
    entries = (FileEntry *)malloc(sizeof(FileEntry) * entries_capacity);
    if (!entries) {
        fclose(zip_fp);
        return -1;
    }

    /* Scan directory for files */
#ifdef _WIN32
    WIN32_FIND_DATAA find_data;
    HANDLE hFind;
    char search_path[2048];

    snprintf(search_path, sizeof(search_path), "%s\\*", source_dir);
    hFind = FindFirstFileA(search_path, &find_data);

    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            if (strcmp(find_data.cFileName, ".") == 0 || strcmp(find_data.cFileName, "..") == 0)
                continue;

            if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)
                continue;

            char filepath[2048];
            snprintf(filepath, sizeof(filepath), "%s\\%s", source_dir, find_data.cFileName);

            /* Expand entries array if needed */
            if (num_entries >= entries_capacity) {
                entries_capacity *= 2;
                entries = (FileEntry *)realloc(entries, sizeof(FileEntry) * entries_capacity);
                if (!entries) {
                    FindClose(hFind);
                    fclose(zip_fp);
                    return -1;
                }
            }

            /* Store entry info */
            strncpy(entries[num_entries].filename, find_data.cFileName, sizeof(entries[num_entries].filename) - 1);
            entries[num_entries].filename[sizeof(entries[num_entries].filename) - 1] = 0;
            entries[num_entries].uncompressed_size = get_file_size(filepath);
            entries[num_entries].crc32 = calculate_crc32(filepath);
            entries[num_entries].local_header_offset = ftell(zip_fp);

            /* Write local file header */
            ZipLocalFileHeader header;
            memset(&header, 0, sizeof(header));
            header.signature = ZIP_LOCAL_FILE_HEADER_SIGNATURE;
            header.version = 20;
            header.flags = 0;
            header.compression = 0; /* Store (no compression) */
            header.crc32 = entries[num_entries].crc32;
            header.compressed_size = entries[num_entries].uncompressed_size;
            header.uncompressed_size = entries[num_entries].uncompressed_size;
            header.filename_length = strlen(entries[num_entries].filename);
            header.extra_length = 0;

            fwrite(&header, sizeof(header), 1, zip_fp);
            fwrite(entries[num_entries].filename, 1, header.filename_length, zip_fp);

            /* Write file data */
            FILE *file_fp = fopen(filepath, "rb");
            if (file_fp) {
                unsigned char buffer[8192];
                size_t bytes_read;
                while ((bytes_read = fread(buffer, 1, sizeof(buffer), file_fp)) > 0) {
                    fwrite(buffer, 1, bytes_read, zip_fp);
                }
                fclose(file_fp);
                printf("  Added: %s (%u bytes)\n", entries[num_entries].filename, entries[num_entries].uncompressed_size);
            }

            entries[num_entries].compressed_size = entries[num_entries].uncompressed_size;
            num_entries++;

        } while (FindNextFileA(hFind, &find_data));

        FindClose(hFind);
    }
#else
    /* Unix/Linux directory scanning would go here */
    fprintf(stderr, "Error: Directory scanning not implemented for this platform\n");
    free(entries);
    fclose(zip_fp);
    return -1;
#endif

    /* Write central directory */
    central_dir_offset = ftell(zip_fp);

    for (int i = 0; i < num_entries; i++) {
        ZipCentralDirEntry entry;
        memset(&entry, 0, sizeof(entry));
        entry.signature = ZIP_CENTRAL_DIR_SIGNATURE;
        entry.version_made = 20;
        entry.version_needed = 20;
        entry.flags = 0;
        entry.compression = 0;
        entry.crc32 = entries[i].crc32;
        entry.compressed_size = entries[i].compressed_size;
        entry.uncompressed_size = entries[i].uncompressed_size;
        entry.filename_length = strlen(entries[i].filename);
        entry.extra_length = 0;
        entry.comment_length = 0;
        entry.disk_start = 0;
        entry.internal_attr = 0;
        entry.external_attr = 0;
        entry.local_header_offset = entries[i].local_header_offset;

        fwrite(&entry, sizeof(entry), 1, zip_fp);
        fwrite(entries[i].filename, 1, entry.filename_length, zip_fp);
    }

    central_dir_size = ftell(zip_fp) - central_dir_offset;

    /* Write end of central directory */
    ZipEndCentralDir end;
    memset(&end, 0, sizeof(end));
    end.signature = ZIP_END_CENTRAL_DIR_SIGNATURE;
    end.disk_number = 0;
    end.central_dir_disk = 0;
    end.num_entries_disk = num_entries;
    end.num_entries = num_entries;
    end.central_dir_size = central_dir_size;
    end.central_dir_offset = central_dir_offset;
    end.comment_length = 0;

    fwrite(&end, sizeof(end), 1, zip_fp);

    free(entries);
    fclose(zip_fp);

    printf("ZIP archive created successfully with %d files\n", num_entries);
    return 0;
}

/* High-level function: extract archive (auto-detect type) */
int archive_extract(const char *archive_path, const char *output_dir)
{
    ArchiveType type = archive_detect_type(archive_path);

    switch (type) {
        case ARCHIVE_TYPE_7Z:
            return archive_extract_7z(archive_path, output_dir);
        case ARCHIVE_TYPE_ZIP:
            return archive_extract_zip(archive_path, output_dir);
        default:
            fprintf(stderr, "Error: Unknown archive type: %s\n", archive_path);
            return -1;
    }
}
