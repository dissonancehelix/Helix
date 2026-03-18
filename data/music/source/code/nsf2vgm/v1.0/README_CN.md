# NSF2VGM 批量转换器 - 支持压缩包自动解压

## 简介

NSF2VGM 是一个强大的 NSF (NES Sound Format) 到 VGM (Video Game Music) 格式转换工具。本版本新增了对 7z 和 ZIP 压缩包的自动解压和打包功能，让批量转换更加便捷。

### 主要特性

- ✅ **自动解压压缩包**：支持 7z 和 ZIP 格式
- ✅ **批量转换**：基于 M3U 播放列表批量转换所有曲目
- ✅ **自动打包**：转换完成后自动打包为 ZIP 文件
- ✅ **完整的音源支持**：支持 NES 标准音源及所有扩展音源（FDS, VRC6, VRC7, MMC5, N106, FME7）
- ✅ **GD3 标签**：自动生成包含曲目信息的 GD3 标签
- ✅ **循环点支持**：正确处理音乐循环点
- ✅ **特殊字符支持**：完美支持日文、中文等特殊字符文件名

## 快速开始

### 使用预编译版本

1. 下载 `nsf2vgm_batch.exe`
2. 将 7z 或 ZIP 压缩包拖放到程序上，或使用命令行：

```bash
nsf2vgm_batch.exe "游戏音乐.7z"
```

### 使用示例

#### 示例 1：转换 7z 压缩包

```bash
nsf2vgm_batch.exe "Kirby's Adventure [Hoshi no Kirby - Yume no Izumi no Monogatari] (1993-03-23)(HAL Laboratory)(Nintendo)[NES].7z"
```

**输入文件结构：**
```
Kirby's Adventure.7z
├── Kirby's Adventure.nsf
└── Kirby's Adventure.m3u
```

**输出结果：**
```
Kirby's Adventure.zip
├── 01 Green Fields ~Intro~.vgm
├── 02 Green Fields.vgm
├── 03 Hyper.vgm
├── ...
├── 56 Epilogue.vgm
└── playlist.m3u
```

#### 示例 2：转换 ZIP 压缩包

```bash
nsf2vgm_batch.exe "game_music.zip"
```

#### 示例 3：直接转换 M3U 文件

```bash
nsf2vgm_batch.exe "playlist.m3u" "output_folder"
```

## 工作流程

### 处理压缩包时的流程

1. **检测压缩包类型**：自动识别 7z 或 ZIP 格式
2. **解压到临时目录**：提取所有文件到临时文件夹
3. **查找 M3U 文件**：在解压的文件中查找播放列表
4. **加载 NSF 文件**：读取 NSF 音乐文件
5. **批量转换**：根据 M3U 中的信息转换所有曲目
6. **生成 VGM 文件**：每首曲目生成一个 VGM 文件
7. **创建播放列表**：生成新的 playlist.m3u
8. **打包为 ZIP**：将所有 VGM 文件打包
9. **清理临时文件**：删除临时目录

### 处理 M3U 文件时的流程

1. **解析 M3U**：读取播放列表信息
2. **加载 NSF**：加载对应的 NSF 文件
3. **批量转换**：转换所有曲目
4. **输出到目录**：生成 VGM 文件到指定目录

## M3U 播放列表格式

M3U 文件定义了要转换的曲目信息：

```
game.nsf::NSF,0,Title Screen,120,5
game.nsf::NSF,1,Stage 1,180,10
game.nsf::NSF,2,Boss Battle,150,8
```

**格式说明：**
- `game.nsf` - NSF 文件名
- `::NSF` - 格式标识
- `0` - 曲目编号
- `Title Screen` - 曲目标题
- `120` - 播放时长（秒）
- `5` - 循环前奏时长（秒）

## 命令行参数

```
nsf2vgm_batch.exe <输入文件> [输出目录]
```

### 参数说明

- `<输入文件>` - 必需，可以是：
  - `.7z` - 7z 压缩包
  - `.zip` - ZIP 压缩包
  - `.m3u` - M3U 播放列表

- `[输出目录]` - 可选
  - 不指定时自动生成：`[文件名]_vgm`
  - 压缩包输入时会生成 ZIP 文件

### 使用示例

```bash
# 自动生成输出文件名
nsf2vgm_batch.exe "music.7z"
# 输出: music.zip

# 指定输出目录（仅对 M3U 有效）
nsf2vgm_batch.exe "playlist.m3u" "my_vgm_folder"
# 输出: my_vgm_folder/ 目录

# 处理包含特殊字符的文件名
nsf2vgm_batch.exe "星のカービィ.7z"
# 输出: 星のカービィ.zip
```

## 编译说明

### 环境要求

- **编译器**：GCC (MinGW-w64 或 MSYS2)
- **操作系统**：Windows / Linux / macOS
- **依赖库**：已包含在源码中
  - 7z SDK (LZMA)
  - zlib

### 编译步骤

#### Windows (MSYS2)

```bash
# 1. 安装 MSYS2 和 GCC
pacman -S mingw-w64-x86_64-gcc make

# 2. 进入源码目录
cd nsf2vgm

# 3. 编译
make clean
make nsf2vgm_batch.exe

# 4. 测试
./nsf2vgm_batch.exe
```

#### Linux

```bash
# 1. 安装 GCC
sudo apt-get install build-essential

# 2. 编译
cd nsf2vgm
make clean
make

# 3. 运行
./nsf2vgm_batch
```

### 编译选项

```makefile
# 优化级别
CFLAGS = -O2

# 调试版本
CFLAGS = -g -O0

# 静态链接
LDFLAGS = -static -lm
```

## 技术细节

### 支持的压缩格式

#### 7z 格式
- **解压算法**：LZMA, LZMA2, PPMd, BCJ2, Delta
- **实现**：基于 7z SDK 24.08
- **特点**：高压缩率，支持固实压缩

#### ZIP 格式
- **解压算法**：Deflate, Store (无压缩)
- **打包算法**：Store (无压缩，保证兼容性)
- **实现**：基于 zlib 1.2.11
- **特点**：通用性强，兼容性好

### 支持的 NSF 扩展音源

| 音源 | 说明 | 芯片 |
|------|------|------|
| 标准 APU | NES 内置音源 | 2A03 |
| FDS | Famicom Disk System | 任天堂 FDS |
| VRC6 | Konami VRC6 | Konami |
| VRC7 | Konami VRC7 | Konami (FM) |
| MMC5 | Nintendo MMC5 | 任天堂 |
| N106 | Namco 163 | Namco |
| FME7 | Sunsoft FME-7 | Sunsoft |

### VGM 格式特性

- **采样率**：44100 Hz
- **版本**：VGM 1.70
- **标签**：GD3 (包含标题、作者等信息)
- **循环**：支持循环点设置
- **压缩**：未压缩（便于编辑）

## 目录结构

```
nsf2vgm/
├── nsf2vgm_batch.exe      # 主程序（预编译）
├── Makefile               # 编译配置
├── README_CN.md           # 中文文档
├── README_EN.md           # 英文文档
├── BUILD.md               # 编译说明
├── vgmwrite.c             # VGM 写入模块
├── vgmwrite.h
├── src/
│   ├── batch_convert.c    # 批量转换主程序
│   ├── converter.c        # 转换核心
│   ├── converter.h
│   ├── m3u_parser.c       # M3U 解析器
│   ├── m3u_parser.h
│   ├── archive_utils.c    # 压缩包处理
│   ├── archive_utils.h
│   ├── format/            # NSF 格式支持
│   │   ├── nezplug.c
│   │   ├── audiosys.c
│   │   ├── m_nsf.c
│   │   └── ...
│   ├── device/            # 音源模拟
│   │   ├── nes/
│   │   │   ├── s_apu.c    # NES APU
│   │   │   ├── s_fds.c    # FDS
│   │   │   ├── s_vrc6.c   # VRC6
│   │   │   ├── s_vrc7.c   # VRC7
│   │   │   └── ...
│   │   └── ...
│   ├── cpu/               # CPU 模拟
│   │   └── kmz80/
│   ├── 7z/                # 7z SDK
│   │   ├── 7z.h
│   │   ├── 7zDec.c
│   │   ├── LzmaDec.c
│   │   └── ...
│   └── zlib/              # zlib 库
│       ├── zlib.h
│       ├── deflate.c
│       ├── inflate.c
│       └── ...
```

## 常见问题

### Q: 支持哪些 NSF 文件？
A: 支持所有标准 NSF 文件，包括使用扩展音源的 NSF。

### Q: 为什么输出的 ZIP 文件比较大？
A: 为了保证兼容性，输出的 ZIP 使用无压缩存储。VGM 文件本身已经是优化过的格式。

### Q: 可以转换单个 NSF 文件吗？
A: 需要先创建一个 M3U 播放列表文件，然后使用程序转换。

### Q: 支持 NSFe 格式吗？
A: 目前仅支持标准 NSF 格式。NSFe 支持计划在未来版本中添加。

### Q: 转换后的 VGM 文件可以在哪里播放？
A: 可以使用以下播放器：
- VGMPlay
- Foobar2000 (with vgmstream plugin)
- Winamp (with in_vgm plugin)
- 在线播放器：vgmrips.net

### Q: 如何处理包含特殊字符的文件名？
A: 程序已经支持 Unicode 文件名，可以直接处理日文、中文等特殊字符。

### Q: 临时文件会自动清理吗？
A: 是的，程序会在转换完成后自动删除所有临时文件和目录。

## 性能优化

### 转换速度

- **单曲转换**：约 1-5 秒（取决于曲目长度）
- **批量转换**：56 首曲目约 2-3 分钟
- **解压速度**：7z 约 1-2 秒，ZIP 约 0.5-1 秒

### 内存使用

- **基础内存**：约 10-20 MB
- **峰值内存**：约 50-100 MB（处理大型 NSF 时）

## 更新日志

### v2.0.0 (2026-02-02)

**新功能**
- ✨ 添加 7z 压缩包自动解压支持
- ✨ 添加 ZIP 压缩包自动解压支持
- ✨ 添加 VGM 文件自动打包为 ZIP 功能
- ✨ 支持特殊字符文件名（Unicode）

**改进**
- 🔧 改进文件名处理逻辑
- 🔧 优化临时文件管理
- 🔧 增强错误处理和提示

**修复**
- 🐛 修复长文件名处理问题
- 🐛 修复特殊字符路径问题

### v1.0.0

**初始版本**
- ✅ NSF 到 VGM 转换
- ✅ M3U 播放列表支持
- ✅ 批量转换功能

## 许可证

本项目基于以下开源项目：

- **NEZplug++**：NSF 播放引擎 (Public Domain)
- **7z SDK**：7z 解压库 (Public Domain)
- **zlib**：ZIP 压缩库 (zlib License)

本程序为自由软件，可以自由使用、修改和分发。

## 致谢

- NEZplug++ 开发团队
- Igor Pavlov (7z SDK)
- Jean-loup Gailly & Mark Adler (zlib)

## 联系方式

- **问题反馈**：请在 GitHub Issues 中提交
- **功能建议**：欢迎提交 Pull Request

## 相关链接

- [VGM 格式规范](https://vgmrips.net/wiki/VGM_Specification)
- [NSF 格式规范](https://wiki.nesdev.com/w/index.php/NSF)
- [7z SDK](https://www.7-zip.org/sdk.html)
- [zlib](https://www.zlib.net/)

---

**享受你的 VGM 音乐收藏！** 🎵
