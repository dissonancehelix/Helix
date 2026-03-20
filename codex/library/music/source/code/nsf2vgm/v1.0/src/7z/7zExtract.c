/*
 * 7z Extract - Simple 7z extraction wrapper
 * Based on LZMA SDK
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "7zExtract.h"
#include "7z.h"
#include "7zAlloc.h"
#include "7zCrc.h"
#include "7zFile.h"
#include "7zBuf.h"

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

/* Check if filename has supported extension */
static int IsSupportedFile(const char *name)
{
    const char *ext = strrchr(name, '.');
    if (!ext) return 0;

    /* Check for NSF, M3U, and other music formats */
    if (stricmp_local(ext, ".nsf") == 0) return 1;
    if (stricmp_local(ext, ".m3u") == 0) return 1;
    if (stricmp_local(ext, ".txt") == 0) return 1;

    return 0;
}

unsigned SZ_extractFile(const char *filename, void **ppbuf)
{
    CFileInStream archiveStream;
    CLookToRead2 lookStream;
    CSzArEx db;
    SRes res;
    UInt16 *temp = NULL;
    size_t tempSize = 0;
    unsigned result_size = 0;

    *ppbuf = NULL;

    /* Open archive file */
    if (InFile_Open(&archiveStream.file, filename))
        return 0;

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

        /* Find first supported file */
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

            /* Convert UTF-16 to ASCII for extension check */
            {
                char name[260];
                size_t j;
                for (j = 0; j < len && j < 259; j++)
                    name[j] = (char)temp[j];
                name[j] = 0;

                if (!IsSupportedFile(name))
                    continue;
            }

            /* Extract this file */
            res = SzArEx_Extract(&db, &lookStream.vt, i,
                &blockIndex, &outBuffer, &outBufferSize,
                &offset, &outSizeProcessed,
                &g_Alloc, &g_Alloc);

            if (res == SZ_OK)
            {
                /* Allocate output buffer */
                *ppbuf = malloc(outSizeProcessed);
                if (*ppbuf)
                {
                    memcpy(*ppbuf, outBuffer + offset, outSizeProcessed);
                    result_size = (unsigned)outSizeProcessed;
                }
                ISzAlloc_Free(&g_Alloc, outBuffer);
                break;
            }
        }

        if (outBuffer)
            ISzAlloc_Free(&g_Alloc, outBuffer);
    }

    SzArEx_Free(&db, &g_Alloc);
    SzFree(NULL, temp);

    if (lookStream.buf)
        ISzAlloc_Free(&g_Alloc, lookStream.buf);

    File_Close(&archiveStream.file);

    return result_size;
}

unsigned SZ_extractMem(void *data, unsigned len, void **ppbuf)
{
    /* TODO: Implement memory-based extraction if needed */
    /* For now, we'll write to temp file and use SZ_extractFile */
    *ppbuf = NULL;
    return 0;
}
