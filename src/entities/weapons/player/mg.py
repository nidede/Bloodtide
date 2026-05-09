"""
机枪 - 高射速型，每发随机偏移
"""
import random
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE
from entities.projectiles import Projectile
from core.config import Color


_UPG_RAPID_MAX = 5  # 射速最多选5次


class MachineGun(Weapon):
    name = "机枪"
    desc = "速射 | 弹幕倾泻"
    color = Color.YELLOW
    damage = 6
    fire_rate = 5
    is_ranged = True
    # 机枪专属属性
    projectile_speed = 9
    spread = 0.15
    piercing = 0
    _shots = 1

    # 武器升级颜色标准：伤害-RED | 射速-BLUE | 弹幕-YELLOW | 穿透-PURPLE | 暴击-GOLD
    upgrades = [
        Upgrade("mg_damage", "重型弹头", "机枪伤害 +2", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 2)),
        Upgrade("mg_rapid", "润滑弹链", "机枪攻速 +3/s", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(2.0, 60 / (60 / w.fire_rate + 3))), _UPG_RAPID_MAX),
        Upgrade("mg_focus", "收束枪管", "散射减小", Color.BLUE,
                lambda p, w: setattr(w, 'spread', max(0.03, w.spread - 0.03)), UPGRADE_ONCE),
        Upgrade("mg_piercing", "穿甲弹", "子弹穿透 +1", Color.PURPLE,
                lambda p, w: setattr(w, 'piercing', w.piercing + 1)),
        Upgrade("mg_double", "双管齐发", "每次发射2发，散射增大", Color.YELLOW,
                lambda p, w: (setattr(w, '_shots', 2),
                              setattr(w, 'spread', w.spread + 0.06)), UPGRADE_ONCE),
    ]

    def attack(self, attacker, targets, dt=None):
        """发射子弹，角度随机偏移"""
        projectiles = []
        for _ in range(self._shots):
            angle = attacker.angle + random.uniform(-self.spread, self.spread)
            p = Projectile(attacker.x, attacker.y, angle, self.projectile_speed,
                          weapon=self, owner=attacker, piercing=self.piercing)
            p.color = Color.ORANGE
            projectiles.append(p)
        return projectiles

    def _deal_damage(self, target, targets, attacker, proj):
        """机枪伤害：稳定输出"""
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction

    def get_display_stats(self):
        """机枪显示伤害、攻速、散射"""
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"散射: {self.spread:.2f}",
        ]
