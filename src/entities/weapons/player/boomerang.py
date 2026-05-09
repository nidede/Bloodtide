"""
回旋镖 - 飞出后自动返回，来回各命中一次
"""
from ..base import Weapon, Upgrade, DamageResult
from entities.projectiles import BoomerangProjectile
from core.config import Color


class Boomerang(Weapon):
    name = "回旋镖"
    desc = "投掷 | 飞出返回双重命中"
    color = Color.YELLOW
    damage = 15
    fire_rate = 30  # 约2秒一发
    is_ranged = True
    # 回旋镖专属属性
    projectile_speed = 6
    max_distance = 200   # 飞行最远距离

    upgrades = [
        Upgrade("boom_damage", "锋利边缘", "回旋镖伤害 +5", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 5)),
        Upgrade("boom_range", "远投", "飞行距离 +50", Color.BLUE,
                lambda p, w: setattr(w, 'max_distance', w.max_distance + 50)),
        Upgrade("boom_rapid", "快手", "攻速提升", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(12, w.fire_rate - 3))),
    ]

    def attack(self, attacker, targets, dt=None):
        """投掷回旋镖"""
        proj = BoomerangProjectile(
            attacker.x, attacker.y, attacker.angle,
            self.projectile_speed,
            weapon=self, owner=attacker,
            max_distance=self.max_distance
        )
        return [proj]

    def get_display_stats(self):
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"距离: {self.max_distance}",
        ]
