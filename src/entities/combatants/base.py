"""
战斗实体基类 - 玩家和怪物的公共父类

提供共享属性：位置、生命、速度、伤害等
提供共享方法：受伤判定、死亡判定
"""
from core.config import Color, MonsterConfig


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
        """受到伤害 - 扣血 + 闪白，然后触发 _on_hit_by 钩子

        Args:
            damage: 伤害值
            attacker: 攻击方实体（用于反伤等对攻击者的影响）

        Returns:
            实际造成的伤害值
        """
        self.hp -= damage
        self.flash_timer = MonsterConfig.FLASH_FRAMES
        self._on_hit_by(attacker, damage)
        return damage

    def _on_hit_by(self, attacker, damage):
        """被击中后的钩子 - 子类重写实现对攻击者的影响（反伤/减速/中毒等）"""
        pass

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
