"""
彩虹机枪 - 随机发射普通/冰冻/火焰子弹
"""
import random
from ..base import Weapon, Upgrade, DamageResult, EffectType
from entities.projectiles import Projectile
from core.config import Color


# 子弹类型配置：(tag, color, size, speed)
_BULLET_TYPES = [
    ("normal", Color.YELLOW, 3, 9),    # 步枪弹
    ("freeze", Color.CYAN,   4, 7),    # 冰冻弹
    ("burn",   Color.ORANGE, 5, 6),    # 火焰弹
]


class RainbowMG(Weapon):
    name = "彩虹机枪"
    desc = "速射 | 随机属性子弹"
    color = Color.PURPLE
    damage = 4
    fire_rate = 5  # 12发/秒
    is_ranged = True
    # 彩虹机枪专属属性
    spread = 0.12
    freeze_duration = 3.0
    freeze_speed_mult = 0.5
    freeze_atk_mult = 0.5
    burn_dps = 3

    upgrades = [
        Upgrade("rmg_damage", "全属性强化", "伤害 +2", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 2)),
        Upgrade("rmg_rapid", "超频", "攻速 +3/s（最多5次）", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(2.0, 60 / (60 / w.fire_rate + 3))), 5),
        Upgrade("rmg_freeze", "深冷弹", "冰冻时间 +2秒", Color.CYAN,
                lambda p, w: setattr(w, 'freeze_duration', w.freeze_duration + 2)),
        Upgrade("rmg_burn", "炽热弹", "燃烧每层伤害 +2", Color.ORANGE,
                lambda p, w: setattr(w, 'burn_dps', w.burn_dps + 2)),
    ]

    def attack(self, attacker, targets, dt=None):
        """随机发射一种属性子弹"""
        tag, color, size, speed = random.choice(_BULLET_TYPES)
        angle = attacker.angle + random.uniform(-self.spread, self.spread)
        proj = Projectile(attacker.x, attacker.y, angle, speed,
                         weapon=self, owner=attacker)
        proj.color = color
        proj.size = size
        proj.tag = tag
        return [proj]

    def _deal_damage(self, target, targets, attacker, proj):
        """根据子弹 tag 触发不同效果"""
        effects = []
        tag = getattr(proj, 'tag', None) if proj else None
        if tag == "freeze":
            effects.append({
                "type": EffectType.FREEZE,
                "duration": self.freeze_duration,
                "speed_mult": self.freeze_speed_mult,
                "atk_mult": self.freeze_atk_mult,
            })
        elif tag == "burn":
            effects.append({"type": EffectType.BURN, "dps": self.burn_dps})
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual, effects=effects)] + reaction

    def get_display_stats(self):
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"冰冻: {self.freeze_duration:.0f}s",
            f"燃烧: {self.burn_dps}/层/s",
        ]
