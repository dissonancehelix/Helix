# NSF2VGM Batch Converter - Archive Support

## Introduction

NSF2VGM is a powerful NSF (NES Sound Format) to VGM (Video Game Music) converter. This version features automatic extraction and packaging for 7z and ZIP archives, making batch conversion more convenient than ever.

### Key Features

- ✅ **Automatic Archive Extraction**: Supports 7z and ZIP formats
- ✅ **Batch Conversion**: Convert all tracks based on M3U playlists
- ✅ **Automatic Packaging**: Auto-pack converted files into ZIP
- ✅ **Full Sound Chip Support**: NES APU and all expansion chips (FDS, VRC6, VRC7, MMC5, N106, FME7)
- ✅ **GD3 Tags**: Automatic generation of track information tags
- ✅ **Loop Point Support**: Proper handling of music loop points
- ✅ **Unicode Support**: Perfect support for Japanese, Chinese, and other special characters

## Quick Start

### Using Pre-compiled Version

1. Download `nsf2vgm_batch.exe`
2. Drag and drop a 7z or ZIP archive onto the program, or use command line:

```bash
nsf2vgm_batch.exe "game_music.7z"
```

### Usage Examples

#### Example 1: Convert 7z Archive

```bash
nsf2vgm_batch.exe "Kirby's Adventure [Hoshi no Kirby - Yume no Izumi no Monogatari] (1993-03-23)(HAL Laboratory)(Nintendo)[NES].7z"
```

**Input Structure:**
```
Kirby's Adventure.7z
├── Kirby's Adventure.nsf
└── Kirby's Adventure.m3u
```

**Output:**
```
Kirby's Adventure.zip
├── 01 Green Fields ~Intro~.vgm
├── 02 Green Fields.vgm
├── 03 Hyper.vgm
├── ...
├── 56 Epilogue.vgm
└── playlist.m3u
```

#### Example 2: Convert ZIP Archive

```bash
nsf2vgm_batch.exe "game_music.zip"
```

#### Example 3: Convert M3U Directly

```bash
nsf2vgm_batch.exe "playlist.m3u" "output_folder"
```

## Workflow

### Processing Archives

1. **Detect Archive Type**: Auto-detect 7z or ZIP format
2. **Extract to Temp**: Extract all files to temporary directory
3. **Find M3U File**: Locate playlist in extracted files
4. **Load NSF File**: Read NSF music file
5. **Batch Convert**: Convert all tracks according to M3U
6. **Generate VGM Files**: Create one VGM file per track
7. **Create Playlist**: Generate new playlist.m3u
8. **Pack to ZIP**: Package all VGM files
9. **Cleanup**: Remove temporary files

### Processing M3U Files

1. **Parse M3U**: Read playlist information
2. **Load NSF**: Load corresponding NSF file
3. **Batch Convert**: Convert all tracks
4. **Output to Directory**: Generate VGM files to specified folder

## M3U Playlist Format

M3U files define track information for conversion:

```
game.nsf::NSF,0,Title Screen,120,5
game.nsf::NSF,1,Stage 1,180,10
game.nsf::NSF,2,Boss Battle,150,8
```

**Format Description:**
- `game.nsf` - NSF filename
- `::NSF` - Format identifier
- `0` - Track number
- `Title Screen` - Track title
- `120` - Duration in seconds
- `5` - Intro length before loop (seconds)

## Command Line Arguments

```
nsf2vgm_batch.exe <input_file> [output_dir]
```

### Parameters

- `<input_file>` - Required, can be:
  - `.7z` - 7z archive
  - `.zip` - ZIP archive
  - `.m3u` - M3U playlist

- `[output_dir]` - Optional
  - Auto-generated if not specified: `[filename]_vgm`
  - ZIP file generated for archive input

### Usage Examples

```bash
# Auto-generate output filename
nsf2vgm_batch.exe "music.7z"
# Output: music.zip

# Specify output directory (M3U only)
nsf2vgm_batch.exe "playlist.m3u" "my_vgm_folder"
# Output: my_vgm_folder/ directory

# Handle special characters
nsf2vgm_batch.exe "星のカービィ.7z"
# Output: 星のカービィ.zip
```

## Build Instructions

### Requirements

- **Compiler**: GCC (MinGW-w64 or MSYS2)
- **OS**: Windows / Linux / macOS
- **Dependencies**: Included in source
  - 7z SDK (LZMA)
  - zlib

### Build Steps

#### Windows (MSYS2)

```bash
# 1. Install MSYS2 and GCC
pacman -S mingw-w64-x86_64-gcc make

# 2. Navigate to source directory
cd nsf2vgm

# 3. Build
make clean
make nsf2vgm_batch.exe

# 4. Test
./nsf2vgm_batch.exe
```

#### Linux

```bash
# 1. Install GCC
sudo apt-get install build-essential

# 2. Build
cd nsf2vgm
make clean
make

# 3. Run
./nsf2vgm_batch
```

### Build Options

```makefile
# Optimization level
CFLAGS = -O2

# Debug build
CFLAGS = -g -O0

# Static linking
LDFLAGS = -static -lm
```

## Technical Details

### Supported Archive Formats

#### 7z Format
- **Decompression**: LZMA, LZMA2, PPMd, BCJ2, Delta
- **Implementation**: Based on 7z SDK 24.08
- **Features**: High compression ratio, solid archive support

#### ZIP Format
- **Decompression**: Deflate, Store (uncompressed)
- **Compression**: Store (uncompressed for compatibility)
- **Implementation**: Based on zlib 1.2.11
- **Features**: Universal compatibility

### Supported NSF Expansion Chips

| Chip | Description | Hardware |
|------|-------------|----------|
| Standard APU | NES built-in sound | 2A03 |
| FDS | Famicom Disk System | Nintendo FDS |
| VRC6 | Konami VRC6 | Konami |
| VRC7 | Konami VRC7 | Konami (FM) |
| MMC5 | Nintendo MMC5 | Nintendo |
| N106 | Namco 163 | Namco |
| FME7 | Sunsoft FME-7 | Sunsoft |

### VGM Format Features

- **Sample Rate**: 44100 Hz
- **Version**: VGM 1.70
- **Tags**: GD3 (includes title, author, etc.)
- **Looping**: Loop point support
- **Compression**: Uncompressed (easy to edit)

## Directory Structure

```
nsf2vgm/
├── nsf2vgm_batch.exe      # Main program (pre-compiled)
├── Makefile               # Build configuration
├── README_CN.md           # Chinese documentation
├── README_EN.md           # English documentation
├── BUILD.md               # Build instructions
├── vgmwrite.c             # VGM writer module
├── vgmwrite.h
├── src/
│   ├── batch_convert.c    # Batch converter main
│   ├── converter.c        # Conversion core
│   ├── converter.h
│   ├── m3u_parser.c       # M3U parser
│   ├── m3u_parser.h
│   ├── archive_utils.c    # Archive handling
│   ├── archive_utils.h
│   ├── format/            # NSF format support
│   │   ├── nezplug.c
│   │   ├── audiosys.c
│   │   ├── m_nsf.c
│   │   └── ...
│   ├── device/            # Sound chip emulation
│   │   ├── nes/
│   │   │   ├── s_apu.c    # NES APU
│   │   │   ├── s_fds.c    # FDS
│   │   │   ├── s_vrc6.c   # VRC6
│   │   │   ├── s_vrc7.c   # VRC7
│   │   │   └── ...
│   │   └── ...
│   ├── cpu/               # CPU emulation
│   │   └── kmz80/
│   ├── 7z/                # 7z SDK
│   │   ├── 7z.h
│   │   ├── 7zDec.c
│   │   ├── LzmaDec.c
│   │   └── ...
│   └── zlib/              # zlib library
│       ├── zlib.h
│       ├── deflate.c
│       ├── inflate.c
│       └── ...
```

## FAQ

### Q: Which NSF files are supported?
A: All standard NSF files, including those using expansion chips.

### Q: Why is the output ZIP file large?
A: For compatibility, output ZIP uses uncompressed storage. VGM files are already optimized.

### Q: Can I convert a single NSF file?
A: You need to create an M3U playlist file first, then use the program to convert.

### Q: Is NSFe format supported?
A: Currently only standard NSF format is supported. NSFe support is planned for future versions.

### Q: Where can I play the converted VGM files?
A: You can use these players:
- VGMPlay
- Foobar2000 (with vgmstream plugin)
- Winamp (with in_vgm plugin)
- Online player: vgmrips.net

### Q: How to handle filenames with special characters?
A: The program supports Unicode filenames and can handle Japanese, Chinese, and other special characters directly.

### Q: Are temporary files cleaned up automatically?
A: Yes, the program automatically deletes all temporary files and directories after conversion.

## Performance

### Conversion Speed

- **Single Track**: ~1-5 seconds (depends on track length)
- **Batch Conversion**: ~2-3 minutes for 56 tracks
- **Extraction Speed**: 7z ~1-2 seconds, ZIP ~0.5-1 second

### Memory Usage

- **Base Memory**: ~10-20 MB
- **Peak Memory**: ~50-100 MB (when processing large NSF files)

## Changelog

### v2.0.0 (2026-02-02)

**New Features**
- ✨ Added 7z archive auto-extraction support
- ✨ Added ZIP archive auto-extraction support
- ✨ Added automatic VGM packaging to ZIP
- ✨ Unicode filename support

**Improvements**
- 🔧 Improved filename handling logic
- 🔧 Optimized temporary file management
- 🔧 Enhanced error handling and messages

**Bug Fixes**
- 🐛 Fixed long filename handling issues
- 🐛 Fixed special character path problems

### v1.0.0

**Initial Release**
- ✅ NSF to VGM conversion
- ✅ M3U playlist support
- ✅ Batch conversion feature

## License

This project is based on the following open source projects:

- **NEZplug++**: NSF playback engine (Public Domain)
- **7z SDK**: 7z decompression library (Public Domain)
- **zlib**: ZIP compression library (zlib License)

This program is free software and can be freely used, modified, and distributed.

## Credits

- NEZplug++ Development Team
- Igor Pavlov (7z SDK)
- Jean-loup Gailly & Mark Adler (zlib)

## Contact

- **Bug Reports**: Please submit on GitHub Issues
- **Feature Requests**: Pull requests are welcome

## Related Links

- [VGM Format Specification](https://vgmrips.net/wiki/VGM_Specification)
- [NSF Format Specification](https://wiki.nesdev.com/w/index.php/NSF)
- [7z SDK](https://www.7-zip.org/sdk.html)
- [zlib](https://www.zlib.net/)

---

**Enjoy your VGM music collection!** 🎵
