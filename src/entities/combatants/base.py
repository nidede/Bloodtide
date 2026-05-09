"""
战斗实体基类 - 玩家和怪物的公共父类

提供共享属性：位置、生命、速度、伤害等
提供共享方法：受伤判定、死亡判定、状态效果
"""
import pygame
from core.config import Color


class StatusEffect:
    """状态效果基类 - 子类重写方法定义行为变更"""

    def __init__(self, duration):
        self.duration = duration

    def on_update(self, entity, dt):
        """每帧更新，默认递减持续时间"""
        self.duration -= dt

    def on_remove(self, entity):
        """效果移除时触发"""
        pass

    # ---- 实体通过这些方法查询行为变更 ----

    def blocks_movement(self):
        """是否阻止移动"""
        return False

    def blocks_attack(self):
        """是否阻止攻击"""
        return False

    def speed_multiplier(self):
        """移动速度倍率"""
        return 1.0

    def attack_speed_multiplier(self):
        """攻击速度倍率（1.0=正常，<1=减速）"""
        return 1.0

    def draw(self, surface, sx, sy, size):
        """绘制状态效果图标，子类重写"""
        pass


class StunEffect(StatusEffect):
    """眩晕效果 - 阻止移动和攻击"""

    def blocks_movement(self):
        return True

    def blocks_attack(self):
        return True

    def draw(self, surface, sx, sy, size):
        """绘制眩晕星星"""
        import math
        import time
        t = time.time() * 3
        star_y = sy - size - 12
        for i in range(3):
            offset = (i - 1) * 10
            angle = t + i * 2.094
            bx = sx + offset + math.cos(angle) * 4
            by = star_y + math.sin(angle) * 3
            pygame.draw.circle(surface, Color.YELLOW, (int(bx), int(by)), 3)
            pygame.draw.circle(surface, Color.WHITE, (int(bx), int(by)), 1)


class BurnEffect(StatusEffect):
    """燃烧效果 - 每秒扣血，可叠加，永久持续"""

    def __init__(self, dps=1):
        super().__init__(float('inf'))  # 永久不消失
        self.dps = dps          # 每秒每层伤害
        self.stacks = 1         # 当前叠加层数
        self._tick_timer = 0.0  # 扣血计时器
        self._stack_cooldown = 0.0  # 叠加冷却（每秒只能叠1次）

    def try_stack(self):
        """尝试叠加1层，受1秒冷却限制。返回是否成功叠加"""
        if self._stack_cooldown <= 0:
            self.stacks += 1
            self._stack_cooldown = 1.0
            return True
        return False

    def on_update(self, entity, dt):
        """每帧更新：叠加冷却递减 + 每秒扣血"""
        self._stack_cooldown = max(0, self._stack_cooldown - dt)
        self._tick_timer += dt
        if self._tick_timer >= 1.0:
            self._tick_timer -= 1.0
            damage = self.stacks * self.dps
            entity.take_damage(damage, attacker=None)
            entity._pending_texts.append((str(damage), Color.RED, 16))

    def draw(self, surface, sx, sy, size):
        """绘制燃烧效果 - 身体上方小火焰"""
        import random
        for i in range(min(self.stacks, 5)):
            fx = sx + random.randint(-size // 2, size // 2)
            fy = sy - size - 5 - i * 3 + random.randint(-3, 3)
            flame_h = 6 + min(self.stacks, 10)
            pygame.draw.ellipse(surface, Color.ORANGE,
                              (fx - 3, fy - flame_h, 6, flame_h))
            pygame.draw.ellipse(surface, Color.YELLOW,
                              (fx - 2, fy - flame_h + 2, 4, flame_h - 3))


class FreezeEffect(StatusEffect):
    """冰冻效果 - 减速移动和攻速"""

    def __init__(self, duration=5.0, speed_mult=0.5, atk_mult=0.5):
        super().__init__(duration)
        self._speed_mult = speed_mult
        self._atk_mult = atk_mult

    def speed_multiplier(self):
        return self._speed_mult

    def attack_speed_multiplier(self):
        return self._atk_mult

    def draw(self, surface, sx, sy, size):
        """绘制冰冻效果 - 蓝色冰晶"""
        import math
        for i in range(4):
            angle = i * math.pi / 2
            px = sx + math.cos(angle) * (size + 3)
            py = sy + math.sin(angle) * (size + 3)
            pygame.draw.circle(surface, Color.CYAN, (int(px), int(py)), 4)
            pygame.draw.circle(surface, Color.WHITE, (int(px), int(py)), 2)


class TriggerType:
    """事件触发时机常量 - 实体注册和触发时共用，避免字符串拼写错误"""
    ON_DEAL_DAMAGE = "on_deal_damage"    # 造成伤害时（吸血等）
    ON_TAKE_DAMAGE = "on_take_damage"    # 被造成伤害时
    ON_KILL = "on_kill"                  # 击杀时


class CombatEntity:
    """战斗实体基类

    所有可战斗的实体（玩家、怪物）都继承此类。
    提供位置、生命、速度、受伤等公共属性和方法。

    子类需定义：
    - size: 体型大小
    - speed: 移动速度
    - max_hp: 最大生命值
    - is_enemy: 是否为敌方（Character=False, Monster=True）
    """

    size = 20
    speed = 100
    max_hp = 100
    flash_duration = 0.1  # 受击闪白持续时间（秒）
    is_enemy = False

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = self.max_hp
        self.flash_timer = 0
        self._effects = {}  # {trigger: [effect_fn, ...]} 事件回调
        self.status_effects = []  # [StatusEffect, ...] 持续状态列表
        self._pending_texts = []  # [(text, color, size), ...] 状态效果产生的浮动文字

    def add_effect(self, trigger, effect_fn):
        """注册效果函数"""
        self._effects.setdefault(trigger, []).append(effect_fn)

    def remove_effect(self, trigger, effect_fn):
        """移除效果函数"""
        if trigger in self._effects:
            self._effects[trigger] = [fn for fn in self._effects[trigger] if fn is not effect_fn]

    def trigger(self, trigger, **kwargs):
        """触发指定时机的所有效果"""
        for fn in self._effects.get(trigger, []):
            fn(**kwargs)

    # ---- 状态效果管理 ----

    def add_status(self, effect):
        """添加状态效果对象"""
        self.status_effects.append(effect)

    def update_status(self, dt):
        """更新所有状态效果，移除过期的"""
        expired = []
        for eff in self.status_effects:
            eff.on_update(self, dt)
            if eff.duration <= 0:
                eff.on_remove(self)
                expired.append(eff)
        for eff in expired:
            self.status_effects.remove(eff)

    def is_movement_blocked(self):
        """是否有状态阻止移动"""
        return any(eff.blocks_movement() for eff in self.status_effects)

    def is_attack_blocked(self):
        """是否有状态阻止攻击"""
        return any(eff.blocks_attack() for eff in self.status_effects)

    def get_speed_multiplier(self):
        """获取当前速度倍率（所有状态累乘）"""
        mult = 1.0
        for eff in self.status_effects:
            mult *= eff.speed_multiplier()
        return mult

    def get_attack_speed_multiplier(self):
        """获取当前攻速倍率（所有状态累乘）"""
        mult = 1.0
        for eff in self.status_effects:
            mult *= eff.attack_speed_multiplier()
        return mult

    @property
    def dead(self):
        """是否死亡"""
        return self.hp <= 0

    def take_damage(self, damage, attacker=None):
        """受击模板方法：防御计算 → 扣血 → 闪白 → 受击钩子

        子类可通过以下钩子定制行为：
        - _calc_actual_damage(damage): 计算实际伤害（减伤/无敌帧等）
        - _on_take_damage(actual, attacker): 受伤后的额外逻辑（无敌帧计时等）
        - _on_hit_by(attacker, damage): 被击中后的反击效果（反伤等），返回 DamageResult 列表

        Args:
            damage: 原始伤害值
            attacker: 攻击方实体（用于反伤等对攻击者的影响）

        Returns:
            (actual, reaction_results): 实际造成的伤害值, 反击 DamageResult 列表
        """
        actual = self._calc_actual_damage(damage)
        if actual <= 0:
            return 0, []
        self.hp -= actual
        self.flash_timer = self.flash_duration
        self._on_take_damage(actual, attacker)
        reaction_results = self._on_hit_by(attacker, actual)
        return actual, reaction_results or []

    def _calc_actual_damage(self, damage):
        """计算实际伤害 - 子类重写实现减伤/无敌帧，默认直接返回原值"""
        return damage

    def _on_take_damage(self, actual, attacker):
        """受伤后的额外逻辑 - 子类重写（如玩家设置无敌帧），默认空"""
        pass

    def _on_hit_by(self, attacker, damage):
        """被击中后的反击效果 - 子类重写（如反伤）

        Returns:
            list[DamageResult]: 反击产生的伤害结果
        """
        return []

    def _draw_health_bar(self, surface, sx, sy):
        """绘制血条"""
        import pygame
        if self.hp < self.max_hp:
            bw = self.size * 2
            bh = 4
            bx = int(sx - bw // 2)
            by = sy - self.size - 10
            pygame.draw.rect(surface, Color.DARK_GRAY, (bx, by, bw, bh))
            ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(surface, Color.RED, (bx, by, int(bw * ratio), bh))
