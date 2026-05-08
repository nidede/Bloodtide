"""
战斗实体基类 - 玩家和怪物的公共父类

提供共享属性：位置、生命、速度、伤害等
提供共享方法：受伤判定、死亡判定
"""
from core.config import Color


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

    # 效果触发时机
    ON_DEAL_DAMAGE = "on_deal_damage"  # 造成伤害时触发（吸血等）

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
        self._effects = {}  # {trigger: [effect_fn, ...]}

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
