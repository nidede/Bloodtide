"""
武器基类
"""
import math
from entities.projectiles import Projectile


class Upgrade:
    def __init__(self, uid, name, desc, icon_color, apply_fn):
        self.id = uid
        self.name = name
        self.desc = desc
        self.icon_color = icon_color
        self.apply_fn = apply_fn
    
    def apply(self, player, weapon):
        if self.apply_fn:
            self.apply_fn(player, weapon)


class Weapon:
    """武器基类
    
    通用属性: name, desc, color, damage, fire_rate, upgrades
    投射物类武器额外属性定义在子类中（如步枪的 crit_chance, piercing 等）
    """
    name = "武器"
    desc = ""
    color = (200, 200, 200)
    damage = 10
    fire_rate = 25
    upgrades = []

    def fire(self, px, py, angle, player, monsters=None, dt=None):
        """发射投射物，子类必须重写"""
        return []

    def deal_damage(self, monster, player, particles, floating_texts):
        """非投射物武器的伤害处理（如飞刀），投射物武器不需要重写（由 Projectile.deal_damage 处理）"""
        pass

    def update(self, player, monsters, particles, floating_texts, dt):
        pass

    def draw(self, surface, cam_x=0, cam_y=0, px=0, py=0):
        pass

    def get_display_stats(self):
        """返回要显示的属性列表，子类可重写"""
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
        ]

    def apply_upgrade(self, player, upgrade_id):
        pass
    
    def get_upgrade_by_id(self, upgrade_id):
        for upgrade in self.upgrades:
            if upgrade.id == upgrade_id:
                return upgrade
        return None
