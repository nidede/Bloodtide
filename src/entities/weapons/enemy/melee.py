"""
敌人近战武器 - 碰撞伤害
伤害从 attacker.damage 读取，确保怪物属性变化时武器伤害同步
"""
from ..base import Weapon


class EnemyMeleeWeapon(Weapon):
    """敌人近战武器 - 碰撞伤害，伤害跟随怪物属性"""

    name = "敌人近战"

    def deal_damage(self, target, targets, attacker, proj, particles, floating_texts):
        damage = getattr(attacker, 'damage', self.damage)
        actual = target.take_damage(damage, attacker=attacker)
        self._create_damage_text(target, actual, False, floating_texts)
        if attacker and hasattr(attacker, 'trigger'):
            attacker.trigger(attacker.ON_DEAL_DAMAGE, target=target, damage=actual)
        return actual
