"""
Boss追踪弹 - Boss专用，缓慢追踪玩家，超时消失
"""
from ..base import Weapon, DamageResult
from entities.projectiles import MissileProjectile


class BossHomingRifle(Weapon):
    """Boss追踪弹 - 缓慢追踪，超时消失"""

    name = "Boss追踪弹"
    damage = 15
    fire_rate = 90  # 1.5秒1发
    projectile_speed = 3  # 较慢，给玩家反应时间

    def attack(self, attacker, targets, dt=None):
        """发射追踪弹"""
        angle = attacker.angle
        p = MissileProjectile(attacker.x, attacker.y, angle, self.projectile_speed,
                              weapon=self, owner=attacker,
                              homing=True, targets=targets,
                              turn_rate=2.0)  # 渐进转向，2弧度/秒
        p.size = 8
        p.max_lifetime = 4.0  # 4秒后消失
        p.color = (200, 50, 255)  # 紫色追踪弹
        return [p]

    def _deal_damage(self, target, targets, attacker, proj):
        """Boss追踪弹伤害"""
        damage = getattr(attacker, 'damage', self.damage)
        actual, reaction = target.take_damage(damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction
