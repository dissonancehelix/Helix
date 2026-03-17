# NSF2VGM 编译指南 / Build Guide

[中文](#中文) | [English](#english)

---

## 中文

### 系统要求

#### Windows
- **操作系统**: Windows 7 或更高版本
- **编译器**: MinGW-w64 或 MSYS2
- **工具**: make, gcc

#### Linux
- **操作系统**: Ubuntu 18.04+ / Debian 10+ / Fedora 30+
- **编译器**: GCC 7.0+
- **工具**: make, gcc

#### macOS
- **操作系统**: macOS 10.13+
- **编译器**: Clang (Xcode Command Line Tools)
- **工具**: make

### 依赖库

所有依赖库已包含在源码中，无需额外安装：

- **7z SDK 24.08** - 7z 解压支持
- **zlib 1.2.11** - ZIP 压缩/解压支持
- **NEZplug++** - NSF 播放引擎

### Windows 编译步骤

#### 方法 1: 使用 MSYS2 (推荐)

1. **安装 MSYS2**

   下载并安装 MSYS2: https://www.msys2.org/

2. **安装编译工具**

   打开 MSYS2 MinGW 64-bit 终端，执行：
   ```bash
   pacman -Syu
   pacman -S mingw-w64-x86_64-gcc make
   ```

3. **编译程序**
   ```bash
   cd nsf2vgm
   make clean
   make nsf2vgm_batch.exe
   ```

4. **测试程序**
   ```bash
   ./nsf2vgm_batch.exe
   ```

#### 方法 2: 使用 MinGW-w64

1. **安装 MinGW-w64**

   下载 MinGW-w64: https://mingw-w64.org/

2. **设置环境变量**

   将 MinGW-w64 的 bin 目录添加到 PATH

3. **编译程序**
   ```bash
   cd nsf2vgm
   mingw32-make clean
   mingw32-make nsf2vgm_batch.exe
   ```

### Linux 编译步骤

#### Ubuntu / Debian

1. **安装编译工具**
   ```bash
   sudo apt-get update
   sudo apt-get install build-essential
   ```

2. **编译程序**
   ```bash
   cd nsf2vgm
   make clean
   make
   ```

3. **测试程序**
   ```bash
   ./nsf2vgm_batch
   ```

#### Fedora / CentOS

1. **安装编译工具**
   ```bash
   sudo dnf install gcc make
   # 或 CentOS
   sudo yum install gcc make
   ```

2. **编译程序**
   ```bash
   cd nsf2vgm
   make clean
   make
   ```

### macOS 编译步骤

1. **安装 Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

2. **编译程序**
   ```bash
   cd nsf2vgm
   make clean
   make
   ```

3. **测试程序**
   ```bash
   ./nsf2vgm_batch
   ```

### 编译选项

#### 优化编译

```bash
# 最大优化
make CFLAGS="-O3 -march=native"

# 体积优化
make CFLAGS="-Os"
```

#### 调试编译

```bash
# 包含调试信息
make CFLAGS="-g -O0"

# 启用所有警告
make CFLAGS="-Wall -Wextra -g"
```

#### 静态链接

```bash
# 静态链接（生成独立可执行文件）
make LDFLAGS="-static -lm"
```

### 编译目标

```bash
# 编译所有程序
make all

# 仅编译批量转换器
make nsf2vgm_batch.exe

# 仅编译单文件转换器
make nsf2vgm.exe

# 清理编译文件
make clean
```

### 常见编译问题

#### 问题 1: 找不到 gcc

**解决方案**:
- Windows: 确保 MinGW-w64 或 MSYS2 已正确安装并添加到 PATH
- Linux: 运行 `sudo apt-get install gcc`
- macOS: 运行 `xcode-select --install`

#### 问题 2: 找不到 make

**解决方案**:
- Windows: 使用 MSYS2 或安装 MinGW-w64 完整版
- Linux: 运行 `sudo apt-get install make`
- macOS: 包含在 Xcode Command Line Tools 中

#### 问题 3: 编译错误 "undefined reference"

**解决方案**:
```bash
# 清理后重新编译
make clean
make
```

#### 问题 4: 权限错误

**解决方案**:
```bash
# Linux/macOS
chmod +x nsf2vgm_batch

# Windows: 以管理员身份运行终端
```

### 交叉编译

#### 在 Linux 上编译 Windows 版本

1. **安装交叉编译工具**
   ```bash
   sudo apt-get install mingw-w64
   ```

2. **编译**
   ```bash
   make CC=x86_64-w64-mingw32-gcc TARGET=nsf2vgm_batch.exe
   ```

#### 在 macOS 上编译 Linux 版本

需要安装交叉编译工具链（较复杂，不推荐）

### 验证编译结果

```bash
# 检查可执行文件
ls -lh nsf2vgm_batch.exe  # Windows
ls -lh nsf2vgm_batch      # Linux/macOS

# 运行测试
./nsf2vgm_batch.exe --help  # Windows
./nsf2vgm_batch --help      # Linux/macOS
```

### 性能优化建议

1. **使用 -O3 优化**
   ```bash
   make CFLAGS="-O3"
   ```

2. **启用本地架构优化**
   ```bash
   make CFLAGS="-O3 -march=native"
   ```

3. **链接时优化 (LTO)**
   ```bash
   make CFLAGS="-O3 -flto" LDFLAGS="-flto"
   ```

---

## English

### System Requirements

#### Windows
- **OS**: Windows 7 or higher
- **Compiler**: MinGW-w64 or MSYS2
- **Tools**: make, gcc

#### Linux
- **OS**: Ubuntu 18.04+ / Debian 10+ / Fedora 30+
- **Compiler**: GCC 7.0+
- **Tools**: make, gcc

#### macOS
- **OS**: macOS 10.13+
- **Compiler**: Clang (Xcode Command Line Tools)
- **Tools**: make

### Dependencies

All dependencies are included in the source code:

- **7z SDK 24.08** - 7z extraction support
- **zlib 1.2.11** - ZIP compression/decompression
- **NEZplug++** - NSF playback engine

### Windows Build Steps

#### Method 1: Using MSYS2 (Recommended)

1. **Install MSYS2**

   Download and install MSYS2: https://www.msys2.org/

2. **Install Build Tools**

   Open MSYS2 MinGW 64-bit terminal and run:
   ```bash
   pacman -Syu
   pacman -S mingw-w64-x86_64-gcc make
   ```

3. **Build**
   ```bash
   cd nsf2vgm
   make clean
   make nsf2vgm_batch.exe
   ```

4. **Test**
   ```bash
   ./nsf2vgm_batch.exe
   ```

#### Method 2: Using MinGW-w64

1. **Install MinGW-w64**

   Download MinGW-w64: https://mingw-w64.org/

2. **Set Environment Variables**

   Add MinGW-w64 bin directory to PATH

3. **Build**
   ```bash
   cd nsf2vgm
   mingw32-make clean
   mingw32-make nsf2vgm_batch.exe
   ```

### Linux Build Steps

#### Ubuntu / Debian

1. **Install Build Tools**
   ```bash
   sudo apt-get update
   sudo apt-get install build-essential
   ```

2. **Build**
   ```bash
   cd nsf2vgm
   make clean
   make
   ```

3. **Test**
   ```bash
   ./nsf2vgm_batch
   ```

#### Fedora / CentOS

1. **Install Build Tools**
   ```bash
   sudo dnf install gcc make
   # or CentOS
   sudo yum install gcc make
   ```

2. **Build**
   ```bash
   cd nsf2vgm
   make clean
   make
   ```

### macOS Build Steps

1. **Install Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

2. **Build**
   ```bash
   cd nsf2vgm
   make clean
   make
   ```

3. **Test**
   ```bash
   ./nsf2vgm_batch
   ```

### Build Options

#### Optimized Build

```bash
# Maximum optimization
make CFLAGS="-O3 -march=native"

# Size optimization
make CFLAGS="-Os"
```

#### Debug Build

```bash
# Include debug info
make CFLAGS="-g -O0"

# Enable all warnings
make CFLAGS="-Wall -Wextra -g"
```

#### Static Linking

```bash
# Static linking (standalone executable)
make LDFLAGS="-static -lm"
```

### Build Targets

```bash
# Build all programs
make all

# Build batch converter only
make nsf2vgm_batch.exe

# Build single file converter only
make nsf2vgm.exe

# Clean build files
make clean
```

### Common Build Issues

#### Issue 1: gcc not found

**Solution**:
- Windows: Ensure MinGW-w64 or MSYS2 is installed and in PATH
- Linux: Run `sudo apt-get install gcc`
- macOS: Run `xcode-select --install`

#### Issue 2: make not found

**Solution**:
- Windows: Use MSYS2 or install full MinGW-w64
- Linux: Run `sudo apt-get install make`
- macOS: Included in Xcode Command Line Tools

#### Issue 3: "undefined reference" errors

**Solution**:
```bash
# Clean and rebuild
make clean
make
```

#### Issue 4: Permission errors

**Solution**:
```bash
# Linux/macOS
chmod +x nsf2vgm_batch

# Windows: Run terminal as administrator
```

### Cross Compilation

#### Build Windows Version on Linux

1. **Install Cross Compiler**
   ```bash
   sudo apt-get install mingw-w64
   ```

2. **Build**
   ```bash
   make CC=x86_64-w64-mingw32-gcc TARGET=nsf2vgm_batch.exe
   ```

#### Build Linux Version on macOS

Requires cross-compilation toolchain (complex, not recommended)

### Verify Build

```bash
# Check executable
ls -lh nsf2vgm_batch.exe  # Windows
ls -lh nsf2vgm_batch      # Linux/macOS

# Run test
./nsf2vgm_batch.exe --help  # Windows
./nsf2vgm_batch --help      # Linux/macOS
```

### Performance Optimization Tips

1. **Use -O3 optimization**
   ```bash
   make CFLAGS="-O3"
   ```

2. **Enable native architecture optimization**
   ```bash
   make CFLAGS="-O3 -march=native"
   ```

3. **Link-time optimization (LTO)**
   ```bash
   make CFLAGS="-O3 -flto" LDFLAGS="-flto"
   ```

---

## 技术支持 / Technical Support

如有编译问题，请提交 Issue 并包含以下信息：
For build issues, please submit an Issue with:

- 操作系统和版本 / OS and version
- 编译器版本 / Compiler version
- 完整错误信息 / Complete error message
- 编译命令 / Build command used
