/*
 * Archive Utilities - 7z/ZIP extraction and ZIP creation
 */

#ifndef __ARCHIVE_UTILS_H__
#define __ARCHIVE_UTILS_H__

#ifdef __cplusplus
extern "C" {
#endif

/* Archive types */
typedef enum {
    ARCHIVE_TYPE_UNKNOWN = 0,
    ARCHIVE_TYPE_7Z,
    ARCHIVE_TYPE_ZIP
} ArchiveType;

/* Detect archive type from file extension */
ArchiveType archive_detect_type(const char *filename);

/* Extract all files from 7z archive to directory
 * Returns: 0 on success, -1 on error
 */
int archive_extract_7z(const char *archive_path, const char *output_dir);

/* Extract all files from ZIP archive to directory
 * Returns: 0 on success, -1 on error
 */
int archive_extract_zip(const char *archive_path, const char *output_dir);

/* Create ZIP archive from directory
 * Returns: 0 on success, -1 on error
 */
int archive_create_zip(const char *source_dir, const char *zip_path);

/* High-level function: extract archive (auto-detect type)
 * Returns: 0 on success, -1 on error
 */
int archive_extract(const char *archive_path, const char *output_dir);

#ifdef __cplusplus
}
#endif

#endif /* __ARCHIVE_UTILS_H__ */
