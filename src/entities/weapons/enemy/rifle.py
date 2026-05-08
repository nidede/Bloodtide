"""
敌人步枪 - 远程怪物专用
伤害从 attacker.damage 同步，无暴击和升级树
"""
from ..base import Weapon, DamageResult
from entities.projectiles import Projectile


class EnemyRifle(Weapon):
    """敌人步枪 - 无暴击，伤害跟随怪物属性"""

    name = "敌人步枪"
    damage = 8
    fire_rate = 60  # 1秒1发
    projectile_speed = 4
    projectile_count = 1
    spread = 0.0

    def attack(self, attacker, targets, dt=None):
        """发射子弹"""
        projectiles = []
        for i in range(self.projectile_count):
            a = attacker.angle
            p = Projectile(attacker.x, attacker.y, a, self.projectile_speed,
                          weapon=self, owner=attacker)
            p.size = 6
            p.color = (255, 80, 80)  # 敌方子弹红色
            projectiles.append(p)
        return projectiles

    def _deal_damage(self, target, targets, attacker, proj):
        """敌人步枪伤害 - 无暴击，伤害跟随怪物属性"""
        damage = getattr(attacker, 'damage', self.damage)
        actual, reaction = target.take_damage(damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction
