# 添加玩家武器指南

## 概述

玩家武器放在 `src/entities/weapons/player/` 目录下。新增武器只需创建一个文件并在两处 `__init__.py` 注册。

---

## 第一步：选择武器模式

武器有四种攻击模式，决定你重写哪些方法：

| 模式 | 适用场景 | 重写方法 | 示例 |
|------|----------|----------|------|
| **投射物型** | 发射子弹 | `attack()` + `_deal_damage()` | 步枪、机枪、冰冻枪 |
| **持续效果型** | 旋转飞刀、近战范围 | `update()` + `_deal_damage()` | 飞刀 |
| **内部冷却型** | 定时触发的效果 | `update()` + `_deal_damage()` | 电弧、喷火器 |
| **召唤型** | 生成炮台等独立实体 | `update()` + `draw()` | 召唤台 |

---

## 第二步：创建武器文件

在 `src/entities/weapons/player/` 下新建文件。

### 投射物型示例

```python
"""
冰冻枪 - 发射冰弹，命中减速敌人
"""
import random
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE, EffectType
from entities.projectiles import Projectile
from core.config import Color


class FreezeGun(Weapon):
    name = "冰冻枪"
    desc = "速射 | 命中减速敌人"
    color = Color.CYAN
    damage = 8
    fire_rate = 18  # 约3.3发/秒
    is_ranged = True  # 标记为远程武器（召唤台炮台自动识别）
    # 专属属性
    projectile_speed = 8
    freeze_chance = 0.15

    upgrades = [
        Upgrade("freeze_damage", "冷凝弹", "伤害 +2", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 2)),
    ]

    def attack(self, attacker, targets, dt=None):
        """发射冰弹"""
        proj = Projectile(attacker.x, attacker.y, attacker.angle,
                         self.projectile_speed,
                         weapon=self, owner=attacker)
        proj.color = Color.CYAN   # 自定义颜色
        proj.size = 4             # 自定义大小
        return [proj]

    def _deal_damage(self, target, targets, attacker, proj):
        """命中计算伤害 + 概率触发冰冻"""
        effects = []
        if random.random() < self.freeze_chance:
            effects.append({
                "type": EffectType.FREEZE,
                "duration": 5.0,
                "speed_mult": 0.5,
                "atk_mult": 0.5,
            })
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual, effects=effects)] + reaction
```

### 内部冷却型示例

```python
class Arc(Weapon):
    fire_rate = 25

    def attack(self, attacker, targets, dt=None):
        return []  # 不发射投射物

    def _deal_damage(self, target, targets, attacker, proj):
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        effects = []
        if self.stun_duration > 0:
            effects.append({"type": EffectType.STUN, "duration": self.stun_duration})
        return [DamageResult(target, actual, effects=effects)] + reaction

    def update(self, attacker, targets, dt):
        if not hasattr(self, '_cooldown'):
            self._cooldown = 0
        self._cooldown -= dt
        if self._cooldown > 0:
            return []
        # ... 找目标、造成伤害 ...
        self._cooldown = self.fire_rate / 60
        return results

    def draw(self, surface, cam_x=0, cam_y=0, px=0, py=0):
        # 绘制武器视觉效果
        pass
```

---

## 第三步：注册武器

### 3.1 `src/entities/weapons/player/__init__.py`

```python
from .freeze_gun import FreezeGun
__all__ = ['Rifle', 'Blades', 'Missile', 'MachineGun', 'Arc',
           'Flamethrower', 'Boomerang', 'FreezeGun', ...]
```

### 3.2 `src/entities/weapons/__init__.py`

```python
from entities.weapons.player import Rifle, ..., FreezeGun

def get_random_weapons(count=None, level=1):
    weapons = [Rifle, ..., FreezeGun]
    ...
```

**完成！不需要改 CombatSystem、UI 等其他代码。**

---

## 关键属性

### `is_ranged = True`

标记武器为远程攻击型。用途：
- 召唤台炮台自动识别所有 `is_ranged=True` 的武器来随机生成
- 后续其他系统也可用来区分近战/远程

所有发射投射物的武器都应设为 `is_ranged = True`。

### `pending_projectiles`

`Weapon` 基类的公开属性，默认空列表。如果武器在 `update()` 中产生了投射物（如召唤台炮台），放到这里，CombatSystem 会自动收集加入碰撞系统：

```python
def update(self, attacker, targets, dt):
    # ... 炮台攻击产生投射物 ...
    self.pending_projectiles.extend(projs)
    return results
```

---

## 关键接口详解

### `attack(attacker, targets, dt) → list[Projectile]`

- `attacker`：攻击方实体，有 `x`, `y`, `angle` 属性
- `targets`：对方阵营列表（怪物列表）
- 返回 Projectile 列表，CombatSystem 自动处理碰撞后调用 `deal_damage()`
- 不需要投射物时返回 `[]`

### `_deal_damage(target, targets, attacker, proj) → list[DamageResult]`

- 唯一的伤害计算入口，子类必须重写
- **不要手动触发 `ON_DEAL_DAMAGE`**，基类 `deal_damage()` 会自动处理（吸血等）
- 只有绕过 `deal_damage()` 直接调用 `take_damage()` 时（如电弧链式跳跃），才需手动触发

### `update(attacker, targets, dt) → list[DamageResult]`

- 每帧调用，适合持续效果型武器
- 通过 `self.deal_damage()` 造成伤害（会自动触发 ON_DEAL_DAMAGE）
- 产生的投射物放入 `self.pending_projectiles`

### `draw(surface, cam_x, cam_y, px, py)`

- 绘制武器视觉效果
- `px`, `py` 是玩家的世界坐标
- 使用 `cam_x`, `cam_y` 做视口偏移

---

## 伤害附带效果

在 `_deal_damage()` 中通过 `DamageResult.effects` 传递效果数据，CombatSystem 负责执行：

**可用效果类型**（定义在 `entities/weapons/base.py` 的 `EffectType`）：

| 常量 | 说明 | 所需参数 |
|------|------|----------|
| `EffectType.EXPLOSION` | 爆炸视觉 | `x`, `y`, `radius` |
| `EffectType.PARTICLE` | 单个粒子 | `x`, `y`, `color`, `speed`, `lifetime` |
| `EffectType.HIT_PARTICLES` | 命中粒子（CombatSystem自动添加） | 无 |
| `EffectType.STUN` | 眩晕状态 | `duration`（秒） |
| `EffectType.BURN` | 燃烧状态 | `dps`（每层每秒伤害） |
| `EffectType.FREEZE` | 冰冻状态 | `duration`, `speed_mult`, `atk_mult` |

新增效果类型：在 `EffectType` 类中添加常量，并在 `systems/combat.py` 的 `_process_damage_results()` 中添加处理逻辑。

### 效果分类

| 分类 | 时机 | 处理方式 | 示例 |
|------|------|----------|------|
| **伤害修正** | 命中前 | 武器自己算 | 暴击（改入参damage） |
| **状态附加** | 命中后 | 武器下指令 → CombatSystem执行 | 眩晕、燃烧、冰冻 |

**暴击**必须在 `take_damage()` 前应用倍率，所以武器自己算。状态效果在命中后附加，由 CombatSystem 统一创建 StatusEffect 对象。

---

## 升级卡片

### 基本格式

```python
upgrades = [
    Upgrade("uid", "名称", "描述", 颜色, apply_fn, max_count),
]
```

### 颜色标准

| 颜色 | 类型 | 示例 |
|------|------|------|
| `Color.RED` | 伤害 | 强化枪管 |
| `Color.BLUE` | 射速/机动 | 轻量化 |
| `Color.YELLOW` | 弹幕/数量 | 三连发 |
| `Color.PURPLE` | 穿透/强化 | 穿透弹、极寒 |
| `Color.ORANGE` | 范围/爆炸 | 扩大爆炸 |
| `Color.GREEN` | 特效/状态 | 追踪弹、燃烧 |
| `Color.GOLD` | 暴击 | 精准暴击 |
| `Color.CYAN` | 冰冻/减速 | 深寒 |

### 次数限制

```python
_UPG_MY_MAX = 5  # 模块顶部定义常量

Upgrade("my_upg", "名称", "描述", Color.RED,
        lambda p, w: ..., _UPG_MY_MAX),

Upgrade("my_once", "名称", "描述", Color.RED,
        lambda p, w: ..., UPGRADE_ONCE),  # 只能选一次
```

> 模块级常量是 Python 标准做法，类定义期间类名尚未存在。

### apply_fn 签名

```python
lambda player, weapon: ...
```

---

## 攻速计算

`fire_rate` 单位是"帧"（60帧=1秒），冷却计时器用真实时间（秒）：

```python
self.cooldown_timer = self.weapon.fire_rate / 60
```

**射速升级推荐方式**（固定加攻速）：

```python
# 每次加 N 发/秒
fire_rate = max(下限, 60 / (60 / fire_rate + N))
```

---

## 投射物

### 普通 Projectile

```python
from entities.projectiles import Projectile

p = Projectile(x, y, angle, speed, weapon=self, owner=attacker, piercing=0)
p.color = Color.ORANGE   # 自定义颜色
p.size = 6               # 自定义大小
p.tag = "freeze"         # 自定义标签（用于 _deal_damage 区分子弹类型）
```

### 追踪弹 MissileProjectile

```python
from entities.projectiles import MissileProjectile

p = MissileProjectile(x, y, angle, speed, weapon=self, owner=attacker,
                      homing=True, targets=targets,
                      turn_rate=2.0)         # 渐进转向弧度/秒，0=瞬间转向
p.max_lifetime = 4.0   # 存活时间（秒），超时自动消失
```

### 回旋镖 BoomerangProjectile

```python
from entities.projectiles import BoomerangProjectile

p = BoomerangProjectile(x, y, angle, speed,
                        weapon=self, owner=attacker,
                        max_distance=200)     # 飞行最远距离
p.return_target = turret  # 可选：返回目标（默认=owner=玩家）
```

- 飞到 `max_distance` 后自动返回
- 返回时清空 `hit_set`，同一条线上的敌人会被打两次
- 炮台发射时设 `return_target = turret`，让回旋镖飞回炮台

---

## 现有武器一览

| 武器 | 模式 | 核心特点 | is_ranged |
|------|------|----------|-----------|
| 步枪 | 投射物 | 暴击流 | True |
| 机枪 | 投射物 | 高射速散射 | True |
| 导弹 | 投射物 | AOE爆炸 | True |
| 飞刀 | 持续效果 | 旋转环绕 | False |
| 电弧 | 内部冷却 | 链式跳跃+眩晕 | False |
| 喷火器 | 内部冷却 | 扇形范围+燃烧 | False |
| 回旋镖 | 投射物 | 飞出返回双重命中 | True |
| 冰冻枪 | 投射物 | 命中冰冻减速 | True |
| 火焰枪 | 投射物 | 命中燃烧叠加 | True |
| 召唤台 | 召唤 | 自动生成炮台 | False |
| 彩虹机枪 | 投射物 | 随机属性子弹 | True |
