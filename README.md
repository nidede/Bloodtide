# SurvivorGame

一款基于 Pygame 的 Vampire Survivors 风格生存射击游戏。玩家在有限地图中抵御一波波怪物，击杀获取经验升级，选择武器和角色强化，尽可能存活更久。

## 游戏特性

- **波次生存**：抵御一波又一波的怪物攻击，每5波出现 Boss
- **6种怪物**：普通、快速、坦克、精英、远程、Boss，各有不同属性与行为
- **3种武器**：步枪（速射）、飞刀（环绕近战）、导弹（追踪 AoE），每种有5级专属升级
- **武器委托伤害**：所有伤害流经 `Weapon.deal_damage()`，支持暴击、吸血、穿透、AoE 等机制
- **对称战斗系统**：玩家和敌人的攻击均委托武器处理，代码路径统一
- **丰富升级**：通用属性升级 + 武器专属升级，每次升级随机3选1
- **小地图**：实时显示玩家和敌人位置

## 项目结构

```
game/
├── src/                              # 源代码目录
│   ├── core/                         # 核心模块
│   │   ├── main.py                   # Game 主类 & 游戏主循环
│   │   ├── config.py                 # 集中配置（屏幕/角色/怪物/波次等参数）
│   │   ├── camera.py                 # 摄像机跟随系统
│   │   └── events.py                 # 事件总线（发布/订阅）
│   ├── entities/                     # 游戏实体
│   │   ├── combatants/               # 战斗实体
│   │   │   ├── base.py               # CombatEntity 基类（HP/受击闪白/粒子）
│   │   │   ├── player/               # 玩家角色
│   │   │   │   ├── base.py           # Character 基类（升级/属性/无敌帧）
│   │   │   │   └── soldier.py        # Soldier 职业 + 通用升级列表
│   │   │   └── monsters/             # 怪物
│   │   │       ├── base.py           # BaseMonster（追击/攻击/武器委托）
│   │   │       ├── normal.py         # 普通怪物
│   │   │       ├── fast.py           # 快速怪物
│   │   │       ├── tank.py           # 坦克怪物
│   │   │       ├── elite.py          # 精英怪物
│   │   │       ├── ranged.py         # 远程怪物（发射投射物）
│   │   │       └── boss.py           # Boss（每5波）
│   │   ├── weapons/                  # 武器系统
│   │   │   ├── base.py               # Weapon 基类 + Upgrade 类
│   │   │   ├── rifle.py              # 步枪（远程速射）
│   │   │   ├── blades.py             # 飞刀（环绕近战）
│   │   │   ├── missile.py            # 导弹（追踪 + AoE）
│   │   │   └── enemy.py              # 敌人近战/远程武器
│   │   └── projectiles/             # 投射物
│   │       ├── base.py               # Projectile 基类（移动/碰撞/on_hit）
│   │       └── missile.py            # 追踪型导弹投射物
│   ├── systems/                      # 游戏系统
│   │   ├── combat.py                 # 战斗系统（碰撞检测/伤害委托/死亡处理）
│   │   ├── spawner.py               # 波次生成器（按权重/波次筛选怪物）
│   │   └── upgrade.py               # 升级选择系统（通用+武器专属池）
│   ├── ui/                           # 界面模块
│   │   ├── base.py                   # MenuButton 组件
│   │   ├── effects.py               # Particle 粒子 + FloatingText 浮动文字
│   │   ├── game.py                  # HUD / 武器选择 / 升级选择 / 暂停
│   │   └── menu.py                  # 主菜单 / 结算界面
│   └── resources/                   # 资源文件
│       └── fonts/msyh.ttc           # 微软雅黑字体
├── docs/
│   └── balance_spec.md              # 数值平衡设计文档
├── build.py                          # PyInstaller 打包脚本
└── requirements.txt                  # 依赖（pygame）
```

## 核心架构

### 继承关系

```
CombatEntity
├── Character → Soldier (= Player)
└── BaseMonster
    ├── NormalMonster / FastMonster / TankMonster
    ├── EliteMonster / RangedMonster
    └── BossMonster

Weapon
├── Rifle          # 远程速射
├── Blades         # 环绕近战
├── Missile        # 追踪 AoE
├── EnemyMeleeWeapon   # 敌人近战碰撞
└── EnemyRangedWeapon  # 敌人远程射击

Projectile
└── MissileProjectile   # 追踪型导弹
```

### 伤害委托模式

所有伤害统一流经 `Weapon.deal_damage()`：

```
投射物碰撞 / 飞刀旋转碰撞 / 近战碰撞
  → weapon.deal_damage(target, ...)
    → target.take_damage(damage, particles)   # 纯粹：扣血 + 闪白 + 粒子
    → weapon._create_damage_text(...)          # 武器负责浮动文字（暴击是武器属性）
```

- `take_damage()` 只管减血 + 闪白 + 受击粒子，返回实际伤害
- 暴击/吸血/AoE 等逻辑由各武器 `deal_damage()` 自行实现
- 浮动文字由武器创建，因为暴击是武器属性

### 对称战斗系统

玩家 → 怪物 和 敌人 → 玩家 遵循相同代码路径：

```
# 玩家投射物命中怪物              # 敌方投射物命中玩家
proj.weapon.deal_damage(...)       proj.weapon.deal_damage(...)
proj.on_hit(monster)               proj.on_hit(player)
```

投射物通过 `is_enemy` 标志区分阵营，`on_hit()` 封装命中记录、穿透消耗、存活判断。

### 游戏主循环

```
Game.run()
  ├── handle_event() → UI Screen 处理输入
  ├── update(dt)
  │     ├── Player.update()          # 移动 + 自动瞄准
  │     ├── Weapon.update()          # 飞刀旋转等持续效果
  │     ├── Player.try_shoot()       # Weapon.attack() → 生成 Projectile[]
  │     ├── Spawner.update()         # 波次管理 + 怪物生成
  │     ├── CombatSystem.update_projectiles()  # 碰撞 + 武器伤害委托
  │     ├── CombatSystem.update_monsters()      # 怪物 AI + 攻击
  │     └── CombatSystem.process_dead_monsters() # 死亡处理 + 经验分配
  └── draw()
        ├── 世界背景 + 网格 + 边界
        ├── 实体绘制（怪物/投射物/粒子/玩家）
        └── HUD + 小地图 + 各 Screen 覆盖层
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
pyinstaller --clean --noconfirm --paths=src --add-data "src/resources;resources" src/core/main.py -n SurvivorGame --console
```

> **参数说明**：
> - `--paths=src`：将 src 目录添加到模块搜索路径，解决模块导入问题
> - `--add-data "src/resources;resources"`：将字体等资源文件打包到 exe 中

3. 打包完成后，可执行文件位于：
```
dist\SurvivorGame\SurvivorGame.exe
```

### 方式二：使用打包脚本

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
    ├── *.pyd           # Python 扩展模块
    ├── resources/      # 资源目录
    │   └── fonts/      # 字体文件（中文显示依赖）
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

## 常见问题

**Q: 打包后运行提示 "No module named 'xxx'"？**
A: 确保使用 `--paths=src` 参数，它会将 src 目录添加到模块搜索路径中。

**Q: 游戏运行一闪而过？**
A: 在命令行中运行 exe 而不是双击，这样可以查看错误信息。

**Q: 他人运行时中文字体显示为方块/乱码？**
A: 确保打包时使用了 `--add-data "src/resources;resources"` 参数，这样字体会被包含在 exe 中。
