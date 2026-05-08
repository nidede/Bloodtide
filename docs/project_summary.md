# Monster Slayer 架构设计文档

---

## 一、项目概述

**Monster Slayer** 是一款基于 Pygame 的 Vampire Survivors 风格生存射击游戏。项目核心目标：在实现完整玩法的同时，保持清晰的分层架构和低耦合设计。

### 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.8+ |
| 游戏引擎 | Pygame | 2.5+ |
| 打包工具 | PyInstaller | 6.0+ |

---

## 二、架构原则

1. **分层解耦**：`core` → `entities` → `systems` → `ui` → `main`，依赖方向严格单向
2. **数据驱动**：实体层返回纯数据（`DamageResult`），UI 层根据数据创建视觉对象
3. **模板方法**：`take_damage` 和 `deal_damage` 使用模板方法，子类只需关注差异逻辑
4. **帧率无关**：所有计时器基于 `dt`（秒），衰减使用 `rate ** (dt * 60)`
5. **集中配置**：所有数值参数集中在 `config.py`，便于调整

---

## 三、模块划分与依赖关系

```
core/          基础层，无内部依赖
  ├── config.py    配置常量（被全项目引用）
  ├── camera.py    摄像机跟随
  ├── render.py    pygame_draw_circle 工具
  └── main.py      组装根（Game 类，导入所有层）

entities/      实体层，只依赖 core，零 UI 导入
  ├── combatants/
  │   ├── base.py          CombatEntity（take_damage 模板方法）
  │   ├── player/          Character → Soldier（无敌帧/反伤）
  │   └── monsters/        BaseMonster + 6 种怪物（各设 weapon_class）
  ├── weapons/
  │   ├── base.py          Weapon + DamageResult + Upgrade（零依赖）
  │   ├── player/          Rifle / Blades / Missile（_deal_damage 模板方法）
  │   └── enemy/           EnemyMeleeWeapon / EnemyRifle
  └── projectiles/         Projectile + MissileProjectile

systems/       系统层，依赖 core + entities，通过工厂解耦 UI
  ├── combat.py    CombatSystem（工厂模式，不导入 ui 类）
  ├── spawner.py   Spawner + MonsterRegistry
  └── upgrade.py   roll_upgrades()

ui/            界面层，只依赖 core
  ├── effects.py   Particle + FloatingText
  ├── game.py      HUD / WeaponSelectScreen / UpgradeScreen / PauseScreen
  ├── menu.py      MenuScreen / GameOverScreen
  └── base.py      MenuButton
```

### 依赖规则

| 规则 | 状态 |
|------|------|
| core 不依赖其他内部模块 | 满足 |
| entities 只依赖 core | 满足 |
| systems 不导入 ui | 满足（combat.py 通过工厂回调） |
| ui 不导入 entities / systems | 满足 |
| 无循环依赖 | 满足 |
| main.py 是唯一组装根 | 满足 |

---

## 四、核心设计模式

### 4.1 DamageResult 数据管线

**问题**：武器命中时需要创建浮动文字和粒子，但实体层不应依赖 UI。

**方案**：武器返回纯数据 `DamageResult`，由 `CombatSystem` 统一创建 UI 对象。

```
Weapon._deal_damage()
  → target.take_damage() → (actual, reaction_results)
  → 组装 [DamageResult(target, actual, is_crit, effects)]

CombatSystem.deal_damage() [基类模板方法]
  → 调用 _deal_damage()
  → 遍历结果，触发 attacker.trigger(ON_DEAL_DAMAGE)

CombatSystem._process_damage_results()
  → damage > 0 → text_factory() 创建浮动文字
  → effects    → particle_factory() 创建粒子/爆炸
```

**DamageResult 结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `target` | CombatEntity / None | 命中目标（None 表示纯特效） |
| `damage` | int | 实际伤害值 |
| `is_crit` | bool | 是否暴击 |
| `effects` | list[dict] | 武器专属特效数据 |

**特效类型**：

| type | 用途 | 参数 |
|------|------|------|
| `"particle"` | 自定义粒子 | x, y, color, speed, lifetime, size |
| `"explosion"` | 导弹爆炸 | x, y, radius |
| `"hit_particles"` | 默认命中粒子 | x, y |

### 4.2 模板方法模式

**take_damage**（CombatEntity）：

```python
def take_damage(self, damage, attacker=None):
    actual = self._calc_actual_damage(damage)   # 子类：无敌帧/减伤
    if actual <= 0:
        return 0, []
    self.hp -= actual
    self.flash_timer = self.flash_duration
    self._on_take_damage(actual, attacker)       # 子类：无敌帧计时
    reaction = self._on_hit_by(attacker, actual)  # 子类：反伤
    return actual, reaction
```

| 钩子 | Character 重写 | BaseMonster 重写 | Soldier 重写 |
|------|---------------|-----------------|-------------|
| `_calc_actual_damage` | 无敌帧判断 + 减伤 | — | — |
| `_on_take_damage` | 设置无敌帧计时 | — | — |
| `_on_hit_by` | — | — | 反伤，返回 DamageResult |

**deal_damage**（Weapon）：

```python
def deal_damage(self, target, targets, attacker, proj):
    results = self._deal_damage(target, targets, attacker, proj)  # 子类重写
    # 基类统一触发 ON_DEAL_DAMAGE（吸血等）
    if attacker and hasattr(attacker, 'trigger'):
        for r in results:
            if r.target is not None and r.damage > 0:
                attacker.trigger(attacker.ON_DEAL_DAMAGE, target=r.target, damage=r.damage)
    return results
```

| 子类 | `_deal_damage` 特殊逻辑 |
|------|------------------------|
| Rifle | 暴击判定，`is_crit` 标记 |
| Blades | 直伤，`update()` 中追加 particle 特效 |
| Missile | AoE 遍历 targets，追加 explosion 特效 |
| EnemyMeleeWeapon | 从 attacker 读取伤害值 |
| EnemyRifle | 同上 |

### 4.3 工厂模式（CombatSystem → UI 解耦）

```python
# Game 层组装
combat = CombatSystem(Particle, FloatingText)

# CombatSystem 内部
def _create_particle(self, x, y, color, speed, lifetime, size):
    return self._particle_factory(x, y, color, speed, lifetime, size)

def _create_damage_text(self, target, damage, is_crit, floating_texts):
    floating_texts.append(self._text_factory(x, y, text, color, size))
```

`CombatSystem` 不导入任何 UI 类，只在构造时接收工厂回调。

### 4.4 怪物注册表

```python
@MonsterRegistry.register
class NormalMonster(BaseMonster):
    TYPE = "normal"
    HP_BASE = 20
    ...

# 使用
monster = MonsterRegistry.get("normal", level=3, x=100, y=200)
```

每个怪物子类显式设置 `weapon_class`（`EnemyMeleeWeapon` 或 `EnemyRifle`），基类不再硬编码武器类型。

---

## 五、战斗管线

`CombatSystem.update()` 是唯一的战斗入口，Game 层只需调用一次：

```python
damage_taken, total_levels = self.combat.update(
    monsters, player, projectiles,
    particles, floating_texts, dt, self._is_visible)
```

管线步骤：

| 步骤 | 说明 | 返回 |
|------|------|------|
| 1. 武器持续效果 | 飞刀旋转等 `weapon.update()` | `list[DamageResult]` |
| 2. 投射物碰撞 | 碰撞检测 → `weapon.deal_damage()` | `list[DamageResult]` |
| 3. 怪物 AI/攻击 | 移动/攻击 → `monster.attack()` | `(projs, list[DamageResult])` |
| 4. 死亡处理 | 经验分配 + 死亡粒子 | `total_levels` |
| 5. 清理 | 删除死亡实体和过期投射物 | — |

每步的 `DamageResult` 都通过 `_process_damage_results()` 统一创建视觉特效。

---

## 六、帧率无关设计

所有时间和速度基于 `dt`（秒），不依赖帧数：

| 机制 | 实现方式 |
|------|----------|
| 移动 | `x += speed * dt` |
| 计时器 | `timer = max(0, timer - dt)` |
| 粒子衰减 | `decay = 0.96 ** (dt * 60)` |
| 冲刺衰减 | `dash_speed *= 0.85 ** (dt * 60)` |
| 闪白时间 | `flash_timer = 0.1`（秒） |
| 震屏 | `screen_shake -= dt`，独立 `screen_shake_intensity` |

---

## 七、升级系统

### 升级流程

```
击杀怪物 → player.gain_xp(xp_value) → 返回升级次数
  ↓
pending_level_ups += total_levels
  ↓
弹出升级界面（3选1）→ 选择后应用
  ↓
如果 pending_level_ups > 0 → 继续弹出下一轮
```

`gain_xp()` 使用 `while` 循环处理多级升级，`pending_level_ups` 队列确保每次升级都有选择机会。

### 升级池

- **通用升级**：定义在 `Character.GENERAL_UPGRADES`，子类可追加（如 Soldier 的反伤）
- **武器升级**：定义在各武器的 `upgrades` 列表
- `roll_upgrades()` 从两个池中随机抽取 3 个选项

---

## 八、性能优化

1. **视锥裁剪**：屏幕外怪物使用简化 AI（直线追击，跳过完整行为）
2. **投射物 hit_set**：每个投射物维护已命中目标集合，避免重复命中
3. **死亡清理**：使用 `id()` 集合标记死亡实体，统一清理
4. **工厂回调**：CombatSystem 不直接实例化 UI 对象，延迟导入开销为零

---

## 九、扩展指南

### 添加新武器

```python
class Shotgun(Weapon):
    name = "霰弹枪"
    damage = 8
    fire_rate = 25

    def attack(self, attacker, targets, dt=None):
        # 返回投射物列表
        ...

    def _deal_damage(self, target, targets, attacker, proj):
        # 返回 list[DamageResult]，ON_DEAL_DAMAGE 由基类处理
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction
```

### 添加新怪物

```python
@MonsterRegistry.register
class PoisonMonster(BaseMonster):
    TYPE = "poison"
    HP_BASE = 25
    weapon_class = EnemyMeleeWeapon
    ...
```

### 添加新角色

```python
class Mage(Character):
    speed = 160
    max_hp = 70

    def _on_hit_by(self, attacker, damage):
        # 法师被击中时的特殊效果，返回 list[DamageResult]
        return []

    GENERAL_UPGRADES = Character.GENERAL_UPGRADES + [
        ("spell_power", "法术强度", "...", Color.PURPLE, lambda p, w: ...),
    ]
```

---

**文档版本**: v2.0
**更新日期**: 2026-05-08
