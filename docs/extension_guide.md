# 实体扩展指南

本文档说明如何向游戏中添加新的实体类型。所有改动都只需修改指定文件，不需要改框架代码。

---

## 一、增加升级卡片

**改动文件**：武器类或角色类的 `upgrades` 列表 / `GENERAL_UPGRADES` 列表

### 1.1 武器专属升级

在对应武器文件（如 `weapons/player/rifle.py`）的 `upgrades` 列表中添加：

```python
upgrades = [
    # ...现有升级...
    Upgrade("rifle_new", "新升级", "描述", Color.RED,
            lambda p, w: setattr(w, 'damage', w.damage + 5)),
]
```

**max_count 规则**：
- 可无限叠加：不加参数（默认 `UPGRADE_UNLIMITED`）
- 只能选一次：末尾加 `UPGRADE_ONCE`
- 限制次数：在模块顶部定义常量，末尾引用

```python
# 模块顶部（类定义外）
_UPG_NEW_MAX = 5

# upgrades 列表中
Upgrade("rifle_new", "新升级", "描述", Color.RED,
        lambda p, w: setattr(w, 'damage', w.damage + 5), _UPG_NEW_MAX),
```

> 注意：模块级常量是 Python 类体引用自身常量的标准做法，因为类定义期间类名尚未存在，不能写 `MyClass.CONST`。

### 1.2 通用角色升级

在 `entities/combatants/player/base.py` 的 `GENERAL_UPGRADES` 列表中添加：

```python
GENERAL_UPGRADES = [
    # ...现有升级...
    ("new_id", "名称", "描述", Color.CYAN, lambda p, w: p._apply_new(w)),
]
```

格式为 `(uid, name, desc, color, apply_fn, max_count?)`，`max_count` 可选，默认无限。

如需角色专属升级（如士兵的反伤），在子类的 `GENERAL_UPGRADES` 中追加：

```python
# soldier.py
GENERAL_UPGRADES = Character.GENERAL_UPGRADES + [
    ("thorns", "反伤", "敌人受伤 +5", Color.ORANGE, lambda p, w: p._apply_thorns(w)),
]
```

---

## 二、增加武器

**改动文件**：3处

### 2.1 创建武器类

在 `entities/weapons/player/` 新建文件（如 `shotgun.py`）：

```python
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE
from entities.projectiles import Projectile  # 如果需要投射物
from core.config import Color

class Shotgun(Weapon):
    name = "霰弹枪"
    desc = "散弹 | 近距离爆发"
    color = Color.RED
    damage = 8
    fire_rate = 25

    upgrades = [
        Upgrade("shotgun_spread", "扩散", "散射角增大", Color.YELLOW,
                lambda p, w: setattr(w, 'spread', w.spread + 0.1)),
    ]

    def attack(self, attacker, targets, dt=None):
        """发射投射物，返回 Projectile 列表"""
        projectiles = []
        for i in range(5):  # 5发散弹
            a = attacker.angle - 0.2 + 0.1 * i
            p = Projectile(attacker.x, attacker.y, a, 8,
                          weapon=self, owner=attacker)
            projectiles.append(p)
        return projectiles

    def _deal_damage(self, target, targets, attacker, proj):
        """伤害逻辑，返回 list[DamageResult]"""
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction

    def get_display_stats(self):
        return [f"伤害: {self.damage}", f"射速: {60/self.fire_rate:.1f}/s"]
```

**关键接口**：
| 方法 | 必须 | 说明 |
|------|------|------|
| `attack()` | 是 | 返回 `list[Projectile]`（近战武器返回 `[]`） |
| `_deal_damage()` | 是 | 返回 `list[DamageResult]`，不需要触发 `ON_DEAL_DAMAGE`（基类自动处理） |
| `update()` | 否 | 持续效果（如飞刀旋转），返回 `list[DamageResult]` |
| `draw()` | 否 | 绘制武器效果（如飞刀、枪口） |
| `get_display_stats()` | 否 | HUD 右下角属性显示 |

### 2.2 注册到模块

`entities/weapons/player/__init__.py`：

```python
from .shotgun import Shotgun
__all__ = ['Rifle', 'Blades', 'Missile', 'Shotgun']
```

### 2.3 加入武器池

`entities/weapons/__init__.py`：

```python
from entities.weapons.player import Rifle, Blades, Missile, Shotgun

def get_random_weapons(count=3, level=1):
    weapons = [Rifle, Blades, Missile, Shotgun]
    ...
```

> 不需要改 `roll_upgrades`、`CombatSystem`、UI 等任何其他代码。

---

## 三、增加怪物

**改动文件**：1处（+1处导入）

### 3.1 创建怪物类

在 `entities/combatants/monsters/` 新建文件（如 `poison.py`）：

```python
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.melee import EnemyMeleeWeapon  # 或 EnemyRifle

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
    weapon_class = EnemyMeleeWeapon  # 近战

    def _draw_shape(self, surface, color, sx, sy):
        """自定义外观"""
        pygame.draw.circle(surface, color, (int(sx), int(sy)), self.size)
```

**必须定义的类属性**：

| 属性 | 说明 |
|------|------|
| `TYPE` | 怪物类型标识，用于注册表 |
| `HP_BASE` / `HP_PER_LVL` | 生命值 = HP_BASE + level × HP_PER_LVL |
| `SPEED_BASE` / `SPEED_PER_LVL` | 移动速度 |
| `DAMAGE_BASE` / `DAMAGE_PER_LVL` | 攻击伤害 |
| `SIZE` | 碰撞体型 |
| `COLOR` | 颜色 |
| `XP_BASE` / `XP_PER_LVL` | 击杀经验 |
| `MIN_WAVE` | 最低出现波次 |
| `SPAWN_WEIGHT` | 生成权重（0~1） |
| `ATTACK_COOLDOWN` | 攻击间隔（秒） |
| `weapon_class` | 武器类（`EnemyMeleeWeapon` 或 `EnemyRifle`） |

**可选重写**：
- `update(player, dt)`：自定义 AI（如 RangedMonster 的撤退/追击）
- `_draw_shape(surface, color, sx, sy)`：自定义外观
- `attack(targets, dt)`：自定义攻击逻辑

### 3.2 注册到模块

`entities/combatants/monsters/__init__.py`：

```python
from entities.combatants.monsters.poison import PoisonMonster
```

> `@MonsterRegistry.register` 装饰器会自动注册到生成池，Spawner 根据波次和权重自动筛选。

---

## 四、增加角色

**改动文件**：1处（+1处导入）

### 4.1 创建角色类

在 `entities/combatants/player/` 新建文件（如 `mage.py`）：

```python
from core.config import Color, PlayerConfig, WORLD_WIDTH, WORLD_HEIGHT
from core.render import pygame_draw_circle
from .base import Character

class Mage(Character):
    speed = 160
    max_hp = 70

    def on_level_up(self):
        """法师升级奖励"""
        self.max_hp += 5
        self.hp = min(self.max_hp, self.hp + 5)
        self.crit_chance += 0.02

    def _on_hit_by(self, attacker, damage):
        """法师被击中时的反击效果"""
        return []  # 无反击

    GENERAL_UPGRADES = Character.GENERAL_UPGRADES + [
        # 法师专属升级
    ]

    def handle_input(self, keys):
        import pygame
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
```

**必须重写**：

| 方法 | 说明 |
|------|------|
| `on_level_up()` | 升级时自动增加的属性 |
| `handle_input(keys)` | 输入处理（不同角色可不同操作） |
| `draw(surface, cam_x, cam_y)` | 角色外观 |

**可选重写**：

| 方法 | 说明 |
|------|------|
| `_calc_actual_damage(damage)` | 自定义减伤/无敌帧逻辑 |
| `_on_hit_by(attacker, damage)` | 被击中后的反击，返回 `list[DamageResult]` |
| `GENERAL_UPGRADES` | 追加角色专属升级 |

### 4.2 注册到模块

`entities/combatants/player/__init__.py`：

```python
from .mage import Mage
```

### 4.3 使用角色

在 `main.py` 中将 `Player = Soldier` 改为 `Player = Mage`，或添加角色选择界面。

---

## 五、增加投射物类型

**改动文件**：1处（+1处导入）

### 5.1 创建投射物类

在 `entities/projectiles/` 新建文件（如 `laser.py`）：

```python
from .base import Projectile

class LaserProjectile(Projectile):
    """激光投射物 - 穿透所有敌人，不消失"""

    def on_hit(self, target):
        """激光穿透，不消失"""
        self.hit_set.add(id(target))
        # 不设 self.alive = False
```

### 5.2 注册到模块

`entities/projectiles/__init__.py`：

```python
from .laser import LaserProjectile
__all__ = ["Projectile", "MissileProjectile", "LaserProjectile"]
```

> 投射物被武器 `attack()` 方法创建，在 `CombatSystem.update_projectiles()` 中自动处理碰撞。

**Projectile 基类关键属性/方法**：

| 属性/方法 | 说明 |
|-----------|------|
| `x, y` | 当前位置 |
| `angle, speed` | 方向和速度 |
| `weapon` | 所属武器（用于 `deal_damage`） |
| `owner` | 攻击者（玩家/怪物） |
| `alive` | 是否存活，`False` 则被清理 |
| `hit_set` | 已命中目标 ID 集合（防重复命中） |
| `is_enemy` | 是否敌方投射物 |
| `update(dt)` | 移动逻辑，出界时设 `alive=False` |
| `on_hit(target)` | 命中后逻辑，默认加入 hit_set + 设 `alive=False` |
| `draw(surface, cam_x, cam_y)` | 外观绘制 |

---

## 六、增加敌人武器

**改动文件**：1处（在对应怪物中设置 `weapon_class`）

### 6.1 创建敌人武器

在 `entities/weapons/enemy/` 新建文件（如 `homing.py`）：

```python
from ..base import Weapon, DamageResult

class EnemyHomingWeapon(Weapon):
    name = "敌人追踪弹"

    def attack(self, attacker, targets, dt=None):
        from entities.projectiles import HomingProjectile  # 按需导入
        p = HomingProjectile(attacker.x, attacker.y, attacker.angle, 3,
                            weapon=self, owner=attacker, targets=targets)
        return [p]

    def _deal_damage(self, target, targets, attacker, proj):
        damage = getattr(attacker, 'damage', self.damage)
        actual, reaction = target.take_damage(damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction
```

### 6.2 在怪物中使用

```python
from entities.weapons.enemy.homing import EnemyHomingWeapon

class BossMonster(BaseMonster):
    weapon_class = EnemyHomingWeapon
```

> 敌人武器的伤害从 `attacker.damage` 动态读取（`getattr(attacker, 'damage', self.damage)`），随怪物等级自动变强。

---

## 改动清单汇总

| 新增实体 | 需改文件 |
|----------|---------|
| 升级卡片 | 武器 `upgrades` 列表 或 角色 `GENERAL_UPGRADES` 列表 |
| 玩家武器 | 新建武器文件 + `weapons/player/__init__.py` + `weapons/__init__.py` |
| 怪物 | 新建怪物文件 + `monsters/__init__.py` |
| 角色 | 新建角色文件 + `player/__init__.py` |
| 投射物 | 新建投射物文件 + `projectiles/__init__.py` |
| 敌人武器 | 新建武器文件 + 怪物 `weapon_class` 引用 |
