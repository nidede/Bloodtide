"""
冰冻枪 - 发射冰弹，命中减速敌人移动和攻速
"""
import random
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE, EffectType
from entities.projectiles import Projectile
from core.config import Color


class FreezeGun(Weapon):
    name = "冰冻枪"
    desc = "速射 | 命中减速敌人"
    color = Color.CYAN
    damage = 8
    fire_rate = 18  # 约3.3发/秒
    is_ranged = True
    # 冰冻枪专属属性
    projectile_speed = 8
    freeze_chance = 0.15      # 冰冻触发概率
    freeze_duration = 5.0     # 冰冻持续时间
    freeze_speed_mult = 0.5   # 减速比例
    freeze_atk_mult = 0.5     # 减攻速比例

    upgrades = [
        Upgrade("freeze_damage", "冷凝弹", "冰冻枪伤害 +2", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 2)),
        Upgrade("freeze_chance", "深寒", "冰冻概率 +10%", Color.GREEN,
                lambda p, w: setattr(w, 'freeze_chance', min(0.8, w.freeze_chance + 0.10))),
        Upgrade("freeze_rapid", "速冻", "攻速提升", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(6, w.fire_rate - 2))),
        Upgrade("freeze_strong", "极寒", "减速效果增强（移动/攻速降至30%）", Color.PURPLE,
                lambda p, w: (setattr(w, 'freeze_speed_mult', 0.3),
                              setattr(w, 'freeze_atk_mult', 0.3)), UPGRADE_ONCE),
    ]

    def attack(self, attacker, targets, dt=None):
        """发射冰弹"""
        proj = Projectile(attacker.x, attacker.y, attacker.angle,
                         self.projectile_speed,
                         weapon=self, owner=attacker)
        proj.color = Color.CYAN
        return [proj]

    def _deal_damage(self, target, targets, attacker, proj):
        """冰冻枪伤害：概率冰冻"""
        effects = []
        if random.random() < self.freeze_chance:
            effects.append({
                "type": EffectType.FREEZE,
                "duration": self.freeze_duration,
                "speed_mult": self.freeze_speed_mult,
                "atk_mult": self.freeze_atk_mult,
            })
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual, effects=effects)] + reaction

    def get_display_stats(self):
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"冰冻: {self.freeze_chance*100:.0f}%",
        ]
