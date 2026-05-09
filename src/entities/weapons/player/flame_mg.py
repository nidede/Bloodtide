"""
火焰枪 - 高射速火焰子弹，命中概率触发燃烧
"""
import random
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE, EffectType
from entities.projectiles import Projectile
from core.config import Color


class FlameGun(Weapon):
    name = "火焰枪"
    desc = "速射 | 命中燃烧敌人"
    color = Color.ORANGE
    damage = 8
    fire_rate = 15  # 4发/秒，和步枪一样
    is_ranged = True
    # 火焰枪专属属性
    projectile_speed = 6
    projectile_size = 5
    burn_chance = 0.25      # 燃烧触发概率
    burn_dps = 4             # 燃烧每秒每层伤害

    upgrades = [
        Upgrade("fmg_damage", "燃烧弹头", "伤害 +3", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 3)),
        Upgrade("fmg_burn", "烈焰弹药", "燃烧概率 +10%", Color.GREEN,
                lambda p, w: setattr(w, 'burn_chance', min(0.8, w.burn_chance + 0.10))),
        Upgrade("fmg_rapid", "轻量化", "攻速 +1/s（最多5次）", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(3.0, 60 / (60 / w.fire_rate + 1))), 5),
        Upgrade("fmg_intense", "烈火", "燃烧每层伤害 +3", Color.RED,
                lambda p, w: setattr(w, 'burn_dps', w.burn_dps + 3)),
    ]

    def attack(self, attacker, targets, dt=None):
        """发射火焰子弹"""
        proj = Projectile(attacker.x, attacker.y, attacker.angle,
                         self.projectile_speed,
                         weapon=self, owner=attacker)
        proj.color = Color.ORANGE
        proj.size = self.projectile_size
        return [proj]

    def _deal_damage(self, target, targets, attacker, proj):
        """火焰枪伤害：概率燃烧"""
        effects = []
        if random.random() < self.burn_chance:
            effects.append({"type": EffectType.BURN, "dps": self.burn_dps})
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual, effects=effects)] + reaction

    def get_display_stats(self):
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"燃烧: {self.burn_chance*100:.0f}%",
            f"燃烧伤害: {self.burn_dps}/层/s",
        ]
