#ifndef __7Z_EXTRACT_H__
#define __7Z_EXTRACT_H__

#ifdef __cplusplus
extern "C" {
#endif

/* Extract first file from 7z archive
 * Returns: size of extracted data, or 0 on error
 * *ppbuf will be allocated and must be freed by caller
 */
unsigned SZ_extractFile(const char *filename, void **ppbuf);

/* Extract first file from 7z archive in memory
 * Returns: size of extracted data, or 0 on error
 * *ppbuf will be allocated and must be freed by caller
 */
unsigned SZ_extractMem(void *data, unsigned len, void **ppbuf);

#ifdef __cplusplus
}
#endif

#endif /* __7Z_EXTRACT_H__ */
