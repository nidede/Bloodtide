# SurvivorGame

一款基于 Pygame 的生存射击游戏，支持单人模式和多人联机。

## 游戏特性

- **生存模式**：抵御一波又一波的怪物攻击
- **武器系统**：多种武器选择和升级
- **技能升级**：丰富的升级选项
- **多人联机**：支持局域网发现、房间创建、加房游玩
- **小地图**：实时显示玩家、敌人和经验球位置

## 项目结构

```
game/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── core/                     # 核心模块
│   │   ├── main.py              # 游戏入口
│   │   ├── camera.py            # 摄像机系统
│   │   ├── config.py            # 配置（屏幕、游戏参数等）
│   │   └── ...
│   ├── entities/                 # 游戏实体
│   │   ├── player/              # 玩家角色
│   │   │   ├── soldier.py       # 战士职业
│   │   │   └── ...
│   │   ├── monsters/            # 怪物
│   │   ├── weapons/             # 武器
│   │   └── ...
│   ├── systems/                 # 游戏系统
│   │   ├── upgrade.py          # 升级系统
│   │   ├── spawner.py          # 怪物生成器
│   │   ├── combat.py           # 战斗系统
│   │   └── network/            # 网络系统
│   ├── ui/                      # 界面
│   │   ├── effects.py          # 粒子效果
│   │   ├── game.py             # HUD 等
│   │   └── ...
│   └── resources/              # 资源文件
│       └── fonts/              # 字体文件
│           └── msyh.ttc         # 微软雅黑字体
├── dist/                         # 打包输出目录
│   └── SurvivorGame/            # 游戏可执行文件
│       ├── SurvivorGame.exe     # 主程序
│       └── _internal/           # 运行库（dll、pyd、资源等）
└── README.md
```

## 环境要求

- Python 3.8+
- Pygame 2.0+

## 安装依赖

```bash
pip install pygame
```

## 运行游戏（开发模式）

```bash
cd src
python core/main.py
```

## 打包为可执行文件

### 方式一：使用 PyInstaller

1. 安装 PyInstaller：

```bash
pip install pyinstaller
```

2. 打包命令：

```bash
cd d:\projects\game
D:\miniconda3\envs\game\Scripts\pyinstaller.exe --clean --noconfirm --paths=src --add-data "src/resources;resources" src/core/main.py -n SurvivorGame --console
```

> **参数说明**：
> - `--paths=src`：将 src 目录添加到模块搜索路径，解决模块导入问题
> - `--add-data "src/resources;resources"`：将字体等资源文件打包到 exe 中

3. 打包完成后，可执行文件位于：
```
dist\SurvivorGame\SurvivorGame.exe
```

### 方式二：使用提供的打包脚本

```bash
python build.py
```

## 分发游戏

将 `dist\SurvivorGame` 文件夹完整打包（压缩）发送给玩家即可。

**必须包含的文件**：
```
dist\SurvivorGame\
├── SurvivorGame.exe    # 游戏主程序
└── _internal/          # 运行库目录（必须保留）
    ├── *.dll           # 动态链接库
    ├── *.pyd          # Python 扩展模块
    ├── resources/     # 资源目录
    │   └── fonts/     # 字体文件（中文显示依赖）
    └── base_library.zip
```

> **重要**：`_internal` 文件夹包含游戏运行所需的全部依赖，删除后游戏将无法运行。
>
> **字体说明**：游戏已捆绑微软雅黑字体，确保在没有中文字体的电脑上也能正常显示中文。

## 游戏操作

| 按键 | 功能 |
|------|------|
| W/A/S/D | 移动 |
| 鼠标左键 | 射击 |
| 空格 | 冲刺 |
| F11 | 切换全屏 |
| ESC | 暂停/返回菜单 |

## 多人游戏

1. 在主菜单点击"多人游戏"
2. 输入昵称
3. 选择"创建房间"作为房主，或"加入房间"作为玩家
4. 房主可设置最大玩家数，其他玩家会自动发现房间
5. 所有玩家准备后，房主开始游戏

## 打包命令速查

```bash
# 完整打包命令（包含字体）
D:\miniconda3\envs\game\Scripts\pyinstaller.exe --clean --noconfirm --paths=src --add-data "src/resources;resources" src/core/main.py -n SurvivorGame --console
```

## 常见问题

**Q: 打包后运行提示 "No module named 'xxx'"？**
A: 确保使用 `--paths=src` 参数，它会将 src 目录添加到模块搜索路径中。

**Q: 游戏运行一闪而过？**
A: 在命令行中运行 exe 而不是双击，这样可以查看错误信息。

**Q: 他人运行时中文字体显示为方块/乱码？**
A: 确保打包时使用了 `--add-data "src/resources;resources"` 参数，这样字体会被包含在 exe 中。

**Q: 多人游戏无法连接？**
A: 确保所有玩家在同一个局域网内，防火墙允许游戏使用的端口通信。
