# 游戏打包指南

## 准备工作

1. 确保已安装 Python 3.8+ (https://www.python.org/downloads/)

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 打包步骤

### 方法一：一键打包

```bash
python build.py
```

这会自动：
1. 清理旧的构建文件
2. 执行 PyInstaller 打包
3. 创建 ZIP 压缩包到 `dist/` 目录

### 方法二：仅打包（不清除）

```bash
pyinstaller survivor.spec --clean
```

## 输出文件

打包完成后：
- `dist/SurvivorGame/` - 游戏文件夹（可直接运行）
- `dist/SurvivorGame_YYYYMMDD_HHMMSS.zip` - 压缩包（可分发给其他人）

## 运行游戏

1. 解压 ZIP 文件
2. 进入 `SurvivorGame` 文件夹
3. 双击 `SurvivorGame.exe` 运行

## 注意事项

1. 首次运行可能会被杀毒软件误报，请添加信任
2. 游戏需要显卡支持（OpenGL）
3. 建议最低配置：
   - Windows 10/11
   - 4GB 内存
   - 集成显卡（性能有限）
   - 独立显卡（推荐）

## 常见问题

**Q: 打包后运行黑屏/崩溃**
A: 检查是否有缺失的资源文件，或尝试重新安装 pygame

**Q: 杀毒软件报警**
A: PyInstaller 打包的程序常被误报，请添加到白名单或信任列表
