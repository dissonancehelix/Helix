# NSF to VGM Converter Makefile

CC = gcc
CFLAGS = -O2 -fcommon -Wall -Wno-unused-variable -Wno-unused-function -Wno-pointer-sign -Wno-discarded-qualifiers -I. -Isrc -Isrc/format -Isrc/device -Isrc/cpu -Isrc/common -Isrc/7z -Isrc/zlib
LDFLAGS = -lm

TARGET = nsf2vgm.exe
BATCH_TARGET = nsf2vgm_batch.exe

MAIN_SRCS = src/main.c src/converter.c
BATCH_SRCS = src/batch_convert.c src/converter.c src/m3u_parser.c src/archive_utils.c
VGM_SRCS = vgmwrite.c

NEZPLUG_SRCS = \
	src/format/nezplug.c \
	src/format/audiosys.c \
	src/format/songinfo.c \
	src/format/nsf6502.c \
	src/format/handler.c \
	src/format/m_nsf.c

CPU_SRCS = \
	src/cpu/kmz80/kmevent.c \
	src/cpu/kmz80/kmz80.c \
	src/cpu/kmz80/kmz80c.c \
	src/cpu/kmz80/kmz80t.c

DEVICE_SRCS = \
	src/device/nes/s_apu.c \
	src/device/nes/s_fds.c \
	src/device/nes/s_fds1.c \
	src/device/nes/s_fds2.c \
	src/device/nes/s_fds3.c \
	src/device/nes/s_fme7.c \
	src/device/nes/s_mmc5.c \
	src/device/nes/s_n106.c \
	src/device/nes/s_vrc6.c \
	src/device/nes/s_vrc7.c \
	src/device/nes/logtable.c \
	src/device/s_psg.c \
	src/device/s_logtbl.c \
	src/device/opl/s_opl.c \
	src/device/opl/s_opltbl.c \
	src/device/opl/s_deltat.c

UTIL_SRCS = \
	src/zlib/nez.c \
	src/zlib/memzip.c \
	src/zlib/inflate.c \
	src/zlib/inffast.c \
	src/zlib/inftrees.c \
	src/zlib/adler32.c \
	src/zlib/crc32.c \
	src/zlib/zutil.c \
	src/zlib/deflate.c \
	src/zlib/trees.c \
	src/zlib/compress.c

7Z_SRCS = \
	src/7z/7zAlloc.c \
	src/7z/7zArcIn.c \
	src/7z/7zBuf.c \
	src/7z/7zCrc.c \
	src/7z/7zCrcOpt.c \
	src/7z/7zDec.c \
	src/7z/7zFile.c \
	src/7z/7zStream.c \
	src/7z/7zExtract.c \
	src/7z/Bcj2.c \
	src/7z/Bra.c \
	src/7z/Bra86.c \
	src/7z/Delta.c \
	src/7z/LzmaDec.c \
	src/7z/Lzma2Dec.c \
	src/7z/Ppmd7.c \
	src/7z/Ppmd7Dec.c

SRCS = $(MAIN_SRCS) $(VGM_SRCS) $(NEZPLUG_SRCS) $(CPU_SRCS) $(DEVICE_SRCS) $(UTIL_SRCS)
OBJS = $(SRCS:.c=.o)

BATCH_OBJS = $(BATCH_SRCS:.c=.o) $(VGM_SRCS:.c=.o) $(NEZPLUG_SRCS:.c=.o) $(CPU_SRCS:.c=.o) $(DEVICE_SRCS:.c=.o) $(UTIL_SRCS:.c=.o) $(7Z_SRCS:.c=.o)

all: $(TARGET) $(BATCH_TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)
	@echo "Build complete: $(TARGET)"

$(BATCH_TARGET): $(BATCH_OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)
	@echo "Build complete: $(BATCH_TARGET)"

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(BATCH_OBJS) $(TARGET) $(BATCH_TARGET)

test: $(TARGET)
	./$(TARGET) test/battle_in_city.nsf output/battle_in_city.vgm -s 0 -l 120

.PHONY: all clean test
