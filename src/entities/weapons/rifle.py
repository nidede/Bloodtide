"""
步枪 - 基础枪械，速射型
"""
from .base import Weapon
from entities.projectiles import Projectile
from core.config import Color
from core.weapon_upgrades import build_rifle_upgrades


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
    upgrades = build_rifle_upgrades()

    def fire(self, px, py, angle, player, monsters=None, dt=None):
        """发射子弹"""
        projectiles = []
        count = self.projectile_count
        for i in range(count):
            if count == 1:
                a = angle
            else:
                a = angle - self.spread / 2 + (self.spread / (count - 1)) * i
            p = Projectile(px, py, a, self.damage, self.projectile_speed,
                           self.crit_chance, self.crit_damage,
                           self.piercing, player.life_steal, player)
            projectiles.append(p)
        return projectiles

    def get_display_stats(self):
        """步枪显示伤害、攻速、暴击、暴伤"""
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"暴击: {self.crit_chance*100:.0f}%",
            f"暴伤: x{self.crit_damage:.2f}",
        ]

    def apply_upgrade(self, player, upgrade_id):
        upgrade = self.get_upgrade_by_id(upgrade_id)
        if upgrade:
            upgrade.apply(player, self)
