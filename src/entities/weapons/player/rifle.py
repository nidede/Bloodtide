"""
步枪 - 基础枪械，速射型
"""
import random
from ..base import Weapon, Upgrade
from entities.projectiles import Projectile
from core.config import Color


class Rifle(Weapon):
    name = "步枪"
    desc = "速射 | 基础枪械"
    color = Color.BLUE
    damage = 10
    fire_rate = 12
    # 步枪专属属性
    projectile_count = 1
    projectile_speed = 10
    spread = 0.06
    piercing = 0
    crit_chance = 0.05
    crit_damage = 1.5

    # 武器升级颜色标准：伤害-RED | 射速-BLUE | 弹幕-YELLOW | 穿透-PURPLE | 暴击-GOLD
    upgrades = [
        Upgrade("rifle_damage", "强化枪管", "步枪伤害 +3", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 3)),
        Upgrade("rifle_rapid", "轻量化", "步枪射速提升", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(3, w.fire_rate - 1))),
        Upgrade("rifle_burst", "三连发", "弹幕 +2 散射略增", Color.YELLOW,
                lambda p, w: (setattr(w, 'projectile_count', w.projectile_count + 2),
                              setattr(w, 'spread', w.spread + 0.05))),
        Upgrade("rifle_sniper", "狙击", "伤害+5 射速降低", Color.RED,
                lambda p, w: (setattr(w, 'damage', w.damage + 5),
                              setattr(w, 'fire_rate', min(15, w.fire_rate + 3)),
                              setattr(w, 'crit_chance', w.crit_chance + 0.05))),
        Upgrade("rifle_piercing", "穿透弹", "子弹穿透 +1", Color.PURPLE,
                lambda p, w: setattr(w, 'piercing', w.piercing + 1)),
        Upgrade("rifle_crit", "精准暴击", "暴击率 +10%", Color.GOLD,
                lambda p, w: setattr(w, 'crit_chance', min(0.8, w.crit_chance + 0.10))),
        Upgrade("rifle_critd", "穿甲弹", "暴击伤害 +50%", Color.GOLD,
                lambda p, w: setattr(w, 'crit_damage', w.crit_damage + 0.50)),
    ]

    def attack(self, attacker, targets, dt=None):
        """发射子弹"""
        projectiles = []
        count = self.projectile_count
        for i in range(count):
            if count == 1:
                a = attacker.angle
            else:
                a = attacker.angle - self.spread / 2 + (self.spread / (count - 1)) * i
            p = Projectile(attacker.x, attacker.y, a, self.projectile_speed,
                          weapon=self, owner=attacker, piercing=self.piercing)
            projectiles.append(p)
        return projectiles

    def deal_damage(self, target, targets, attacker, proj, particles, floating_texts):
        """步枪伤害：暴击"""
        is_crit = random.random() < self.crit_chance
        damage = int(self.damage * (self.crit_damage if is_crit else 1))
        actual = target.take_damage(damage, attacker=attacker)
        self._create_damage_text(target, actual, is_crit, floating_texts)
        if attacker and hasattr(attacker, 'trigger'):
            attacker.trigger(attacker.ON_DEAL_DAMAGE, target=target, damage=actual)
        return actual, is_crit

    def get_display_stats(self):
        """步枪显示伤害、攻速、暴击、暴伤"""
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"暴击: {self.crit_chance*100:.0f}%",
            f"暴伤: x{self.crit_damage:.2f}",
        ]
