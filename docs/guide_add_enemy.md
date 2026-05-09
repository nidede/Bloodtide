# 添加敌人指南

## 概述

敌人（怪物）放在 `src/entities/combatants/monsters/` 目录下，继承 `BaseMonster`。使用 `@MonsterRegistry.register` 装饰器自动注册到生成池，Spawner 根据波次和权重自动筛选。

继承链：`BaseMonster` → `CombatEntity` → 位置/生命/受伤/状态效果。

---

## 第一步：创建怪物文件

在 `src/entities/combatants/monsters/` 下新建文件，如 `poison.py`。

### 近战怪物示例

```python
"""毒素怪物 - 近战攻击"""
import pygame
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.melee import EnemyMeleeWeapon


@MonsterRegistry.register
class PoisonMonster(BaseMonster):
    TYPE = "poison"
    HP_BASE = 25
    HP_PER_LVL = 12
    SPEED_BASE = 80
    SPEED_PER_LVL = 3
    DAMAGE_BASE = 6
    DAMAGE_PER_LVL = 2
    SIZE = 16
    COLOR = Color.GREEN
    XP_BASE = 12
    XP_PER_LVL = 4
    MIN_WAVE = 2
    SPAWN_WEIGHT = 0.10
    ATTACK_COOLDOWN = 1.0
    weapon_class = EnemyMeleeWeapon

    def _draw_shape(self, surface, color, sx, sy):
        """自定义外观"""
        pygame.draw.circle(surface, color, (int(sx), int(sy)), self.size)
        pygame.draw.circle(surface, Color.WHITE, (int(sx), int(sy)), self.size, 1)
```

近战怪物不需要重写 `update()` 和 `attack()`，默认行为是追击玩家 + 碰撞伤害。

### 远程怪物示例

远程怪物需要重写 `update()`（保持距离 AI）和 `attack()`（发射子弹）：

```python
"""散弹怪物 - 远程散射"""
import math
import pygame
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.shotgun import EnemyShotgun


@MonsterRegistry.register
class ShotgunMonster(BaseMonster):
    TYPE = "shotgun"
    HP_BASE = 15
    HP_PER_LVL = 8
    SPEED_BASE = 55
    SPEED_PER_LVL = 2
    DAMAGE_BASE = 6
    DAMAGE_PER_LVL = 2
    SIZE = 18
    COLOR = Color.PINK
    XP_BASE = 18
    XP_PER_LVL = 5
    MIN_WAVE = 3
    SPAWN_WEIGHT = 0.08
    ATTACK_COOLDOWN = 1.5
    weapon_class = EnemyShotgun

    MELEE_RANGE = 200    # 太近，撤退
    OPTIMAL_RANGE = 350  # 最佳射击距离

    def update(self, player, dt):
        """远程 AI - 保持距离"""
        self.update_status(dt)

        if self.is_movement_blocked():
            self.flash_timer = max(0, self.flash_timer - dt)
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            nx, ny = dx / dist, dy / dist
            if dist < self.MELEE_RANGE:
                # 撤退
                self.x -= nx * self.speed * dt
                self.y -= ny * self.speed * dt
            elif dist > self.OPTIMAL_RANGE:
                # 靠近
                speed = self.speed * self.get_speed_multiplier()
                self.x += nx * speed * dt
                self.y += ny * speed * dt

        self.attack_cooldown = max(0, self.attack_cooldown - dt * self.get_attack_speed_multiplier())
        self.flash_timer = max(0, self.flash_timer - dt)

    def attack(self, targets, dt):
        """远程攻击"""
        if self.is_attack_blocked():
            return [], []
        if not self.can_attack() or not targets:
            return [], []

        target = min(targets, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
        self.angle = math.atan2(target.y - self.y, target.x - self.x)
        self.attack_cooldown = self.ATTACK_COOLDOWN

        projs = self.weapon.attack(self, targets, dt)
        return projs, []

    def _draw_shape(self, surface, color, sx, sy):
        """菱形外观"""
        points = [(sx, sy - self.size), (sx + self.size, sy),
                  (sx, sy + self.size), (sx - self.size, sy)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, Color.WHITE, points, 1)
```

---

## 第二步：注册到模块

`src/entities/combatants/monsters/__init__.py`：

```python
from entities.combatants.monsters.poison import PoisonMonster
```

同时添加到 `__all__` 列表。

**仅此一处！** `@MonsterRegistry.register` 装饰器会自动注册到生成池。

---

## 必须定义的类属性

| 属性 | 说明 | 公式 |
|------|------|------|
| `TYPE` | 唯一类型标识，用于注册表 | - |
| `HP_BASE` / `HP_PER_LVL` | 生命值 | `HP_BASE + level × HP_PER_LVL` |
| `SPEED_BASE` / `SPEED_PER_LVL` | 移动速度（像素/秒） | `SPEED_BASE + level × SPEED_PER_LVL` |
| `DAMAGE_BASE` / `DAMAGE_PER_LVL` | 攻击伤害 | `DAMAGE_BASE + level × DAMAGE_PER_LVL` |
| `SIZE` | 碰撞体型 | 固定值 |
| `COLOR` | 颜色 | - |
| `XP_BASE` / `XP_PER_LVL` | 击杀经验 | `XP_BASE + level × XP_PER_LVL` |
| `MIN_WAVE` | 最低出现波次 | Spawner 自动过滤 |
| `SPAWN_WEIGHT` | 生成权重（0~1） | 与其他怪物按比例分配 |
| `ATTACK_COOLDOWN` | 攻击间隔（秒） | - |
| `weapon_class` | 武器类 | 必须显式指定，不可为 None |

---

## 可选重写方法

### `update(player, dt)` — AI 行为

默认实现：追击玩家（近战 AI）。

**重写时必须包含**：
```python
def update(self, player, dt):
    self.update_status(dt)           # 必须调用！更新状态效果
    if self.is_movement_blocked():   # 检查是否被眩晕等
        self.flash_timer = max(0, self.flash_timer - dt)
        return
    # ... 自定义 AI ...
    self.attack_cooldown = max(0, self.attack_cooldown - dt * self.get_attack_speed_multiplier())
    self.flash_timer = max(0, self.flash_timer - dt)
```

**注意**：移动速度要乘 `self.get_speed_multiplier()`，攻击冷却要乘 `self.get_attack_speed_multiplier()`，这样冰冻/减速等状态效果才能生效。

### `attack(targets, dt)` — 攻击逻辑

默认实现：近战碰撞伤害。

**近战怪物**：通常不需要重写，默认碰撞检测 + `weapon.deal_damage()` 即可。

**远程怪物**：必须重写，返回 `(projectiles, damage_results)`：
```python
def attack(self, targets, dt):
    if self.is_attack_blocked():   # 必须检查！眩晕时不能攻击
        return [], []
    if not self.can_attack() or not targets:
        return [], []
    # ... 瞄准、发射 ...
    projs = self.weapon.attack(self, targets, dt)
    return projs, []
```

### `_draw_shape(surface, color, sx, sy)` — 外观

默认实现：圆形。重写以自定义形状，参考现有怪物：

| 怪物 | 形状 |
|------|------|
| Normal | 圆形 |
| Fast | 椭圆 |
| Tank | 方形 |
| Elite | 六边形 |
| Ranged | 菱形+眼睛 |
| Boss | 菱形+发光+皇冠 |

---

## 状态效果与怪物

怪物和玩家共享同一套状态效果系统。当武器命中怪物时，CombatSystem 自动处理以下效果：

| 效果 | 对怪物的影响 | 来源 |
|------|-------------|------|
| 眩晕 (StunEffect) | 阻止移动和攻击 | 电弧升级 |
| 燃烧 (BurnEffect) | 每秒扣血，可叠加 | 火焰枪、彩虹机枪 |
| 冰冻 (FreezeEffect) | 移动速度 ×50%、攻速 ×50% | 冰冻枪、彩虹机枪 |

这些效果在 `BaseMonster.update()` 中通过以下机制自动生效：

- `self.update_status(dt)` — 更新所有状态效果持续时间，移除过期的
- `self.is_movement_blocked()` — 眩晕时阻止移动
- `self.is_attack_blocked()` — 眩晕时阻止攻击
- `self.get_speed_multiplier()` — 所有状态的速度倍率累乘
- `self.get_attack_speed_multiplier()` — 所有状态的攻速倍率累乘

**重写 `update()` 时必须调用这些方法**，否则状态效果不会生效。

---

## 敌人武器

敌人武器放在 `src/entities/weapons/enemy/` 下。

### 现有武器

| 武器 | 文件 | 说明 |
|------|------|------|
| `EnemyMeleeWeapon` | `melee.py` | 碰撞伤害，从 `attacker.damage` 读取 |
| `EnemyRifle` | `rifle.py` | 发射红色子弹，1秒1发 |
| `BossHomingRifle` | `homing.py` | 发射紫色追踪弹，4秒后消失 |

### 创建新敌人武器

```python
"""
敌人散弹 - 近距离多发
"""
from ..base import Weapon, DamageResult
from entities.projectiles import Projectile


class EnemyShotgun(Weapon):
    name = "敌人散弹"
    damage = 5
    fire_rate = 90
    projectile_speed = 4

    def attack(self, attacker, targets, dt=None):
        projectiles = []
        for i in range(3):
            a = attacker.angle - 0.15 + 0.15 * i
            p = Projectile(attacker.x, attacker.y, a, self.projectile_speed,
                          weapon=self, owner=attacker)
            p.size = 5
            p.color = (255, 80, 80)  # 敌方子弹红色
            projectiles.append(p)
        return projectiles

    def _deal_damage(self, target, targets, attacker, proj):
        damage = getattr(attacker, 'damage', self.damage)
        actual, reaction = target.take_damage(damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction
```

**关键**：敌人武器的伤害从 `attacker.damage` 动态读取（`getattr(attacker, 'damage', self.damage)`），随怪物等级自动变强。这是因为怪物的 `damage` 属性根据等级计算，武器只是触发器。

注册到 `src/entities/weapons/enemy/__init__.py`：
```python
from .shotgun import EnemyShotgun
__all__ = ['EnemyMeleeWeapon', 'EnemyRifle', 'BossHomingRifle', 'EnemyShotgun']
```

---

## 数值参考

参考 `docs/balance_spec.md` 中的敌人规范：

| 类型 | 生命 | 速度 | 伤害 | 体型 | 经验 | 权重 | 最低波次 |
|------|------|------|------|------|------|------|----------|
| 普通 | 20+10/lv | 72+3/lv | 5+2/lv | 15 | 10+3/lv | 45% | 1 |
| 快速 | 12+6/lv | 150+5/lv | 4+1.5/lv | 12 | 12+3/lv | 25% | 1 |
| 坦克 | 50+20/lv | 42+2/lv | 8+3/lv | 22 | 18+5/lv | 15% | 1 |
| 远程 | 15+8/lv | 60+2/lv | 8+2/lv | 18 | 15+4/lv | 15% | 2 |
| 精英 | 80+25/lv | 90+3/lv | 12+4/lv | 25 | 40+8/lv | 10% | 3 |
| Boss | 500+100/lv | 48+1/lv | 25+8/lv | 45 | 300+50/lv | 固定 | 5 |
