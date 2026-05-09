# 添加状态效果指南

## 概述

状态效果系统定义在 `src/entities/combatants/base.py`，是 `StatusEffect` 类的继承体系。玩家和怪物都继承 `CombatEntity`，共享同一套状态效果机制。

---

## 系统架构

状态效果系统有两套独立机制：

| 机制 | 存储位置 | 用途 | 特点 |
|------|----------|------|------|
| **事件回调** | `self._effects` 字典 | 永久性触发效果（吸血） | 无持续时间，事件驱动 |
| **状态效果** | `self.status_effects` 列表 | 临时持续状态（眩晕、冰冻、燃烧） | 有持续时间，到期自动移除 |

### 事件回调

```python
# 注册
self.add_effect(TriggerType.ON_DEAL_DAMAGE, self._lifesteal_effect)

# 触发
attacker.trigger(TriggerType.ON_DEAL_DAMAGE, target=..., damage=...)
```

**可用触发时机**（定义在 `TriggerType`）：

| 常量 | 触发时机 |
|------|----------|
| `TriggerType.ON_DEAL_DAMAGE` | 造成伤害时（吸血等） |
| `TriggerType.ON_TAKE_DAMAGE` | 被造成伤害时 |
| `TriggerType.ON_KILL` | 击杀时（预留） |

---

## 现有状态效果

| 效果类 | 行为 | 视觉 | 叠加规则 |
|--------|------|------|----------|
| `StunEffect` | 阻止移动+攻击 | 头顶旋转黄色星星 | 刷新时长 |
| `BurnEffect` | 每秒扣血 | 身体上方火焰 | 叠加层数（1秒冷却） |
| `FreezeEffect` | 减速移动+攻速 | 四周蓝色冰晶 | 刷新时长 |

三种效果形成完整的状态三角：**眩晕=不动，冰冻=慢，燃烧=掉血**。

---

## 添加新的状态效果

### 第一步：创建 StatusEffect 子类

在 `src/entities/combatants/base.py` 的现有效果类后面添加：

```python
class PoisonEffect(StatusEffect):
    """中毒效果 - 每秒扣血，可叠加"""

    def __init__(self, duration=5.0, dps=2):
        super().__init__(duration)
        self.dps = dps
        self.stacks = 1
        self._tick_timer = 0.0

    def try_stack(self):
        """尝试叠加"""
        self.stacks += 1
        return True

    def on_update(self, entity, dt):
        """每帧更新：每秒扣血"""
        super().on_update(entity, dt)  # 递减 duration
        self._tick_timer += dt
        if self._tick_timer >= 1.0:
            self._tick_timer -= 1.0
            damage = self.stacks * self.dps
            entity.take_damage(damage, attacker=None)
            entity._pending_texts.append((str(damage), Color.GREEN, 16))

    def draw(self, surface, sx, sy, size):
        """绘制中毒效果 - 绿色气泡"""
        import random
        for i in range(min(self.stacks, 3)):
            bx = sx + random.randint(-size//2, size//2)
            by = sy - size - 5 - i * 4 + random.randint(-2, 2)
            pygame.draw.circle(surface, Color.GREEN, (int(bx), int(by)), 3)
```

### 第二步：添加效果类型常量

在 `src/entities/weapons/base.py` 的 `EffectType` 类中添加：

```python
class EffectType:
    ...
    POISON = "poison"  # 新增
```

### 第三步：在 CombatSystem 中处理

在 `src/systems/combat.py` 的 `_process_damage_results()` 中添加：

```python
elif eff["type"] == EffectType.POISON and r.target is not None:
    if hasattr(r.target, 'add_status'):
        from entities.combatants.base import PoisonEffect
        existing = None
        for se in r.target.status_effects:
            if isinstance(se, PoisonEffect):
                existing = se
                break
        if existing:
            existing.try_stack()
        else:
            r.target.add_status(PoisonEffect(
                duration=eff.get("duration", 5.0),
                dps=eff.get("dps", 2),
            ))
```

### 第四步：武器中使用

```python
from ..base import EffectType

def _deal_damage(self, target, targets, attacker, proj):
    actual, reaction = target.take_damage(self.damage, attacker=attacker)
    effects = [
        {"type": EffectType.POISON, "duration": 5.0, "dps": 2}
    ]
    return [DamageResult(target, actual, effects=effects)] + reaction
```

---

## StatusEffect 接口详解

### 可重写方法

| 方法 | 默认返回 | 说明 |
|------|----------|------|
| `blocks_movement()` | `False` | 是否阻止移动（StunEffect 返回 `True`） |
| `blocks_attack()` | `False` | 是否阻止攻击（StunEffect 返回 `True`） |
| `speed_multiplier()` | `1.0` | 移动速度倍率（FreezeEffect 返回 `0.5`） |
| `attack_speed_multiplier()` | `1.0` | 攻击速度倍率（FreezeEffect 返回 `0.5`） |
| `draw(surface, sx, sy, size)` | 无 | 绘制状态图标 |
| `on_update(entity, dt)` | 递减 duration | 每帧更新逻辑 |
| `on_remove(entity)` | 无 | 效果移除时的回调 |

### 查询接口（在 CombatEntity 上）

| 方法 | 说明 |
|------|------|
| `is_movement_blocked()` | 是否有任何效果阻止移动 |
| `is_attack_blocked()` | 是否有任何效果阻止攻击 |
| `get_speed_multiplier()` | 所有效果的速度倍率累乘 |
| `get_attack_speed_multiplier()` | 所有效果的攻速倍率累乘 |
| `add_status(effect)` | 添加状态效果对象 |
| `update_status(dt)` | 更新所有效果，移除过期的 |

---

## 数据流

```
武器 _deal_damage()                CombatSystem                   实体
───────────────────                ────────────                   ──────
DamageResult(                      读取 effects 列表
  effects=[{                       ↓
    "type": EffectType.STUN,       效果类型匹配
    "duration": 1.0                ↓
  }]                               创建 StunEffect 对象
)                                  ↓
                                   target.add_status(StunEffect(1.0))
                                                                  ↓
                                                      实体自己管理效果
                                                      is_movement_blocked() → True
                                                      update_status(dt) → 递减 duration
                                                      draw() → 效果自己画自己
```

**核心原则**：武器只返回数据字典，不知道效果对象的存在。CombatSystem 负责翻译。效果对象自己管理行为和绘制。

---

## 燃烧浮动文字

BurnEffect 的扣血在 `on_update()` 里直接调用 `entity.take_damage()`，不经过 CombatSystem 的 DamageResult 管线。如果需要浮动文字，写入实体的 `_pending_texts` 列表：

```python
def on_update(self, entity, dt):
    # ... 扣血逻辑 ...
    entity.take_damage(damage, attacker=None)
    entity._pending_texts.append((str(damage), Color.RED, 16))  # 红色浮动文字
```

CombatSystem 每帧调用 `_flush_pending_texts()` 从实体上取走并创建浮动文字。

---

## 状态效果对玩家和怪物的生效方式

两者完全统一，都通过 `CombatEntity` 基类的接口：

| 效果 | 怪物生效位置 | 玩家生效位置 |
|------|-------------|-------------|
| 阻止移动 | `BaseMonster.update()` 检查 `is_movement_blocked()` | `Soldier.update()` 乘 `get_speed_multiplier()` |
| 阻止攻击 | `BaseMonster.attack()` 检查 `is_attack_blocked()` | `Character.try_shoot()` 检查 `is_attack_blocked()` |
| 减速移动 | `speed * get_speed_multiplier()` | `speed * get_speed_multiplier()` |
| 减攻速 | `attack_cooldown -= dt * get_attack_speed_multiplier()` | `cooldown_timer -= dt * get_attack_speed_multiplier()` |
