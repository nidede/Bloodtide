"""
敌人近战武器 - 碰撞伤害
伤害从 attacker.damage 读取，确保怪物属性变化时武器伤害同步
"""
from ..base import Weapon, DamageResult


class EnemyMeleeWeapon(Weapon):
    """敌人近战武器 - 碰撞伤害，伤害跟随怪物属性"""

    name = "敌人近战"

    def _deal_damage(self, target, targets, attacker, proj):
        damage = getattr(attacker, 'damage', self.damage)
        actual, reaction = target.take_damage(damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction
