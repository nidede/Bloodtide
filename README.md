# Monster Slayer - 打怪升级

一款基于 **Pygame** 开发的 Vampire Survivors 风格生存射击游戏。玩家在有限地图中抵御一波波怪物，击杀获取经验升级，选择武器和角色强化，尽可能存活更久。

## 游戏特性

- **波次生存**：抵御一波又一波的怪物攻击，每5波出现 Boss
- **6种怪物类型**：普通、快速、坦克、精英、远程、Boss，各有独特属性与 AI 行为
- **3种武器系统**：
  - 步枪：远程速射，高射速中等伤害，可暴击
  - 飞刀：环绕近战，自动攻击无需瞄准
  - 导弹：追踪 AoE，高伤害范围攻击
- **丰富升级系统**：通用属性升级 + 武器专属升级，每次升级随机3选1，多级升级连续弹出
- **反伤机制**：士兵角色可解锁反伤，被攻击时自动反击
- **小地图系统**：实时显示玩家和敌人位置
- **冲刺技能**：解锁后可快速闪避

## 项目结构

```
game/
├── src/                              # 源代码目录
│   ├── core/                         # 核心基础设施层
│   │   ├── main.py                   # Game 主类（组装根） & 游戏主循环
│   │   ├── config.py                 # 集中配置（屏幕/角色/怪物/波次等参数）
│   │   ├── camera.py                 # 摄像机跟随系统
│   │   └── render.py                 # 渲染工具函数（pygame_draw_circle）
│   ├── entities/                     # 游戏实体（零 UI 依赖）
│   │   ├── combatants/               # 战斗实体
│   │   │   ├── base.py               # CombatEntity 基类（模板方法 take_damage）
│   │   │   ├── player/               # 玩家角色
│   │   │   │   ├── base.py           # Character 基类（升级/无敌帧/吸血）
│   │   │   │   └── soldier.py        # Soldier 职业 + 反伤 + 通用升级列表
│   │   │   └── monsters/             # 怪物系统
│   │   │       ├── base.py           # BaseMonster + MonsterRegistry
│   │   │       ├── normal.py         # 普通怪物
│   │   │       ├── fast.py           # 快速怪物
│   │   │       ├── tank.py           # 坦克怪物
│   │   │       ├── elite.py          # 精英怪物
│   │   │       ├── ranged.py         # 远程怪物（撤退/追击 AI）
│   │   │       └── boss.py           # Boss（每5波）
│   │   ├── weapons/                  # 武器系统（纯数据返回，无 UI）
│   │   │   ├── base.py               # Weapon + DamageResult + Upgrade
│   │   │   ├── player/               # 玩家武器
│   │   │   │   ├── rifle.py          # 步枪（暴击系统）
│   │   │   │   ├── blades.py         # 飞刀（旋转碰撞）
│   │   │   │   └── missile.py        # 导弹（AoE + 追踪）
│   │   │   └── enemy/                # 敌人武器
│   │   │       ├── melee.py          # 近战武器（伤害跟随怪物属性）
│   │   │       └── rifle.py          # 远程武器
│   │   └── projectiles/              # 投射物系统
│   │       ├── base.py               # Projectile 基类
│   │       └── missile.py            # 追踪型导弹投射物
│   ├── systems/                      # 游戏系统（零 UI 导入，通过工厂解耦）
│   │   ├── combat.py                 # CombatSystem（战斗管线编排 + 特效工厂）
│   │   ├── spawner.py                # 波次生成器（按权重/波次筛选怪物）
│   │   └── upgrade.py                # 升级选择系统（通用+武器专属池）
│   ├── ui/                           # 用户界面（只依赖 core，不导入 entities/systems）
│   │   ├── base.py                   # MenuButton 组件
│   │   ├── effects.py                # Particle 粒子 + FloatingText 浮动文字
│   │   ├── game.py                   # HUD / 武器选择 / 升级选择 / 暂停
│   │   └── menu.py                   # 主菜单 / 结算界面
│   └── resources/
│       └── fonts/msyh.ttc           # 微软雅黑字体
├── docs/
│   ├── balance_spec.md               # 数值平衡设计文档
│   └── architecture.md               # 架构设计文档
├── .gitignore
├── BUILD_README.md
├── build.py
├── requirements.txt
└── README.md
```

## 核心架构

### 分层依赖

```
core/     ← 基础层，无内部依赖
  ↑
entities/ ← 只依赖 core，零 UI 导入
  ↑
systems/  ← 依赖 core + entities，通过工厂模式解耦 UI
  ↑
ui/       ← 只依赖 core，不导入 entities/systems
  ↑
main.py   ← 组装根，导入所有层并接线
```

**核心原则**：
- 实体层和武器层 **零 UI 依赖** — 不创建粒子、不创建浮动文字
- 武器返回 `DamageResult` 纯数据，`CombatSystem` 统一创建视觉特效
- `CombatSystem` 通过工厂回调创建 UI 对象，自身不导入任何 UI 类
- 所有计时器基于真实时间（dt 秒），不依赖帧数

### 继承关系

```
CombatEntity                    # 基类：take_damage 模板方法
├── Character → Soldier         # 玩家：无敌帧 + 减伤 + 反伤
└── BaseMonster                 # 怪物：追击 AI + 武器委托
    ├── NormalMonster / FastMonster / TankMonster
    ├── EliteMonster / RangedMonster
    └── BossMonster

Weapon                          # 基类：deal_damage 模板方法
├── Rifle                       # 步枪：暴击
├── Blades                      # 飞刀：旋转碰撞
├── Missile                     # 导弹：AoE
├── EnemyMeleeWeapon            # 敌人近战
└── EnemyRifle                  # 敌人远程

Projectile
└── MissileProjectile           # 追踪型导弹
```

### DamageResult 数据管线

所有伤害结果通过 `DamageResult` 纯数据对象传递，实现实体层与 UI 层解耦：

```
武器命中 → _deal_damage() 返回 list[DamageResult]
            ↓
        deal_damage() 模板方法：触发 ON_DEAL_DAMAGE（吸血等）
            ↓
        CombatSystem._process_damage_results()
            ├── DamageResult.damage > 0 → 创建伤害浮动文字
            └── DamageResult.effects    → 创建粒子/爆炸等特效
```

`DamageResult` 结构：
- `target`：命中目标（反伤时为攻击者，None 表示纯特效）
- `damage`：实际伤害值
- `is_crit`：是否暴击
- `effects`：武器专属特效列表（`particle` / `explosion` / `hit_particles`）

### 模板方法模式

**take_damage**（CombatEntity）：
```
_calc_actual_damage()  → 子类重写（无敌帧/减伤）
_hp -= actual
_flash_timer = flash_duration
_on_take_damage()      → 子类重写（设置无敌帧计时）
_on_hit_by()           → 子类重写（反伤，返回 list[DamageResult]）
return (actual, reaction_results)
```

**deal_damage**（Weapon）：
```
_deal_damage()         → 子类重写（暴击/AoE/直伤），返回 list[DamageResult]
触发 ON_DEAL_DAMAGE    → 基类统一处理，子类无需重复
return results
```

### 战斗管线

`CombatSystem.update()` 统一编排：

```
1. 玩家武器持续效果（飞刀旋转）
2. 投射物碰撞检测 → weapon.deal_damage()
3. 怪物 AI / 移动 / 攻击
4. 死亡处理 → 经验分配 + 死亡粒子
5. 清理死亡实体和过期投射物
```

返回 `(raw_damage_to_player, total_levels)` 供 Game 层处理震屏和升级。

## 快速开始

### 环境要求

- Python 3.8+
- Pygame 2.5+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行游戏

```bash
cd src
python core/main.py
```

### 打包为可执行文件

```bash
python build.py
```

## 游戏操作

| 按键 | 功能 |
|------|------|
| W/A/S/D | 移动 |
| 空格 | 冲刺（需要解锁升级） |
| F11 | 切换全屏 |
| ESC | 暂停 / 跳过升级 / 返回菜单 |
| Enter | 开始游戏 |

武器自动瞄准最近敌人并射击，无需手动瞄准。

## 扩展指南

### 添加新武器

1. 在 `entities/weapons/player/` 创建新类，继承 `Weapon`
2. 实现 `attack()`（生成投射物）和 `_deal_damage()`（伤害逻辑）
3. `_deal_damage()` 只需返回 `list[DamageResult]`，`ON_DEAL_DAMAGE` 由基类自动触发
4. 在 `entities/weapons/__init__.py` 的 `get_random_weapons()` 中添加

### 添加新怪物

1. 在 `entities/combatants/monsters/` 创建新类，继承 `BaseMonster`
2. 用 `@MonsterRegistry.register` 装饰器注册
3. 设置 `weapon_class`（`EnemyMeleeWeapon` 或 `EnemyRifle`）
4. 定义生成权重和最低波次

### 添加新升级

- 通用升级：在 `Character.GENERAL_UPGRADES` 列表中添加
- 武器升级：在对应武器的 `upgrades` 列表中添加 `Upgrade` 对象

### 添加新角色

1. 在 `entities/combatants/player/` 创建新类，继承 `Character`
2. 重写 `on_level_up()`、`handle_input()`、`draw()`
3. 可重写 `_on_hit_by()` 实现角色特有反击（返回 `list[DamageResult]`）

## 配置说明

所有游戏参数集中在 `src/core/config.py`：

| 配置类 | 说明 |
|--------|------|
| `GameConfig` | 游戏基础配置（帧率、标题） |
| `ScreenConfig` | 窗口配置（分辨率、全屏） |
| `WorldConfig` | 世界地图配置（尺寸） |
| `PlayerConfig` | 玩家参数（无敌帧、冲刺等） |
| `MonsterConfig` | 怪物参数 |
| `WaveConfig` | 波次参数 |
| `CombatConfig` | 战斗系统参数（命中粒子、检测范围等） |
| `ParticleConfig` | 粒子参数（速度衰减、生命周期等） |
| `MissileConfig` | 导弹参数（爆炸粒子等） |

## 常见问题

**Q: 打包后运行提示 "No module named 'xxx"？**
A: 确保使用 `--paths=src` 参数。

**Q: 游戏运行一闪而过？**
A: 在命令行中运行 exe 查看错误信息。

**Q: 中文字体显示为方块/乱码？**
A: 确保打包时使用了 `--add-data "src/resources;resources"` 参数。

**Q: 如何修改游戏参数？**
A: 所有参数都在 `src/core/config.py` 中，修改后重启游戏即可生效。

## 许可证

MIT License
