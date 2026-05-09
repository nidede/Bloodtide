# 添加玩家角色指南

## 概述

玩家角色放在 `src/entities/combatants/player/` 目录下，继承 `Character` 基类。

继承链：`Character` → `CombatEntity` → 位置/生命/受伤/状态效果。

当前默认角色为 `Soldier`（士兵），在 `__init__.py` 中通过 `Player = Soldier` 设置。

---

## 第一步：创建角色文件

在 `src/entities/combatants/player/` 下新建文件，如 `mage.py`。

```python
"""法师 - 高攻低血"""
import math
import pygame
from core.config import Color, WORLD_WIDTH, WORLD_HEIGHT
from core.render import pygame_draw_circle
from .base import Character


class Mage(Character):
    speed = 160        # 像素/秒
    max_hp = 70

    # 可选：角色专属属性
    # mana_regen = 0

    def __init__(self):
        super().__init__(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        # 可选：角色专属初始化
        # self.mana_regen = 0

    def on_level_up(self):
        """升级奖励"""
        self.max_hp += 5
        self.hp = min(self.max_hp, self.hp + 5)
        self.crit_chance += 0.02

    def handle_input(self, keys):
        """输入处理"""
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    def draw(self, surface, cam_x=0, cam_y=0):
        if self.invincible_timer > 0 and int(self.invincible_timer * 15) % 2 == 0:
            return
        sx, sy = self.x - cam_x, self.y - cam_y
        pygame_draw_circle(surface, Color.PURPLE, sx, sy, self.size)
        pygame_draw_circle(surface, (140, 80, 220), sx, sy, self.size - 4)
        # 状态效果绘制（必须）
        for eff in self.status_effects:
            eff.draw(surface, int(sx), int(sy), self.size)

    # 通用升级常量覆盖
    UPG_SPEED = 8
    UPG_MAX_HP = 20
    UPG_DEFENSE = 2

    # 角色专属升级
    GENERAL_UPGRADES = Character.GENERAL_UPGRADES + [
        # ("mage_mana", "法力回复", "每秒回复 +1", Color.BLUE, lambda p, w: p._apply_mana(w)),
    ]
```

---

## 第二步：注册到模块

`src/entities/combatants/player/__init__.py`：

```python
from .mage import Mage

# 设为默认角色
Player = Mage
```

---

## 必须重写的方法

| 方法 | 说明 |
|------|------|
| `on_level_up()` | 升级时自动增加的属性（如血量、防御） |
| `handle_input(keys)` | 输入处理，返回 `(dx, dy)` 方向向量 |
| `draw(surface, cam_x, cam_y)` | 角色外观绘制 |

---

## 可选重写的方法

| 方法 | 说明 | 默认行为 |
|------|------|----------|
| `_calc_actual_damage(damage)` | 自定义减伤/无敌帧逻辑 | 无敌帧 + 防御减伤 |
| `_on_take_damage(actual, attacker)` | 受伤后的额外逻辑 | 设置无敌帧计时器 |
| `_on_hit_by(attacker, damage)` | 被击中后的反击，返回 `list[DamageResult]` | 无反击 |

---

## 可选覆盖的常量

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `speed` | 200 | 基础移动速度（像素/秒） |
| `max_hp` | 100 | 最大生命值 |
| `defense` | 0 | 防御力 |
| `crit_chance` | 0.05 | 暴击率 |
| `crit_damage` | 1.5 | 暴击伤害倍率 |
| `life_steal` | 0 | 生命偷取 |
| `regen` | 0 | 每秒生命恢复 |
| `xp_multiplier` | 1.0 | 经验获取倍率 |
| `UPG_SPEED` | 10 | 每次升级移速增量 |
| `UPG_MAX_HP` | 30 | 每次升级生命增量 |
| `UPG_DEFENSE` | 3 | 每次升级防御增量 |
| `UPG_LIFE_STEAL` | 0.05 | 每次升级吸血增量 |
| `UPG_REGEN` | 2 | 每次升级回复增量 |
| `UPG_XP` | 0.2 | 每次升级经验加成增量 |

---

## 角色专属升级

在角色类中追加 `GENERAL_UPGRADES`：

```python
class Mage(Character):
    GENERAL_UPGRADES = Character.GENERAL_UPGRADES + [
        ("mage_mana", "法力回复", "每秒回复 +1", Color.BLUE,
         lambda p, w: setattr(p, 'mana_regen', p.mana_regen + 1)),
    ]
```

升级格式：`(uid, name, desc, color, apply_fn)` 或 `(uid, name, desc, color, apply_fn, max_count)`

- `uid`: 唯一标识，用于去重
- `name`: 升级名称
- `desc`: 升级描述
- `color`: 卡片颜色
- `apply_fn`: `lambda player, weapon: ...`，应用升级效果
- `max_count`: 可选次数上限，`UPGRADE_ONCE` 表示仅1次

---

## 反伤示例（参考 Soldier）

```python
class Soldier(Character):
    def __init__(self):
        super().__init__(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.thorns = 0

    def _on_hit_by(self, attacker, damage):
        """反伤 - 对攻击者造成 thorns 点伤害"""
        if attacker and self.thorns > 0:
            from entities.weapons.base import DamageResult
            actual, _ = attacker.take_damage(self.thorns, attacker=self)
            if actual > 0:
                return [DamageResult(attacker, actual)]
        return []

    GENERAL_UPGRADES = Character.GENERAL_UPGRADES + [
        ("thorns", "反伤", "敌人受伤 +5", Color.ORANGE,
         lambda p, w: setattr(p, 'thorns', p.thorns + 5)),
    ]
```

注意：反伤不走武器系统，不触发 `ON_DEAL_DAMAGE`（不会吸血）。

---

## draw() 中必须包含的

角色 `draw()` 方法中必须包含无敌帧闪烁和状态效果绘制：

```python
def draw(self, surface, cam_x=0, cam_y=0):
    # 无敌帧闪烁
    if self.invincible_timer > 0 and int(self.invincible_timer * 15) % 2 == 0:
        return
    sx, sy = self.x - cam_x, self.y - cam_y
    # ... 角色外观 ...
    # 状态效果绘制（必须）
    for eff in self.status_effects:
        eff.draw(surface, int(sx), int(sy), self.size)
```

---

## 状态效果与角色

角色和怪物共享同一套状态效果系统。当前玩家可受以下效果影响：

| 效果 | 对角色的影响 | 来源 |
|------|-------------|------|
| 冰冻 (FreezeEffect) | 移动速度 ×50%、攻速 ×50% | 敌方远程怪物子弹 |

`Character` 基类已自动处理：

- `self.get_speed_multiplier()` — 移动时乘以速度倍率（`soldier.py:64`）
- `self.get_attack_speed_multiplier()` — 冷却计时乘以攻速倍率（`base.py:146`）
- `self.update_status(dt)` — 在 `_update_timers()` 中调用，更新所有状态效果

**不需要额外代码**，只要 `update()` 调用了 `_update_timers(dt)`，所有状态效果自动生效。

---

## 角色属性参考

参考 `docs/balance_spec.md` 中的角色规范：

| 属性 | 士兵初始值 | 合理范围 |
|------|-----------|----------|
| 移动速度 | 200 | 180-250 |
| 生命上限 | 100 | 80-150 |
| 防御力 | 0 | 0-10 |
| 暴击率 | 5% | 0-10% |
| 暴击伤害 | 1.5x | 1.5-2.0x |
| 生命偷取 | 0% | 0-20% |
| 生命恢复 | 0 | 0-10 |
| 经验加成 | 1.0x | 1.0-1.5x |
| 体型大小 | 20 | 15-25 |
