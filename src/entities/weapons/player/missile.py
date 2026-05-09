"""
导弹 - 范围爆炸，可追踪
"""
import math
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE, EffectType
from core.config import Color, MissileConfig
from entities.projectiles import MissileProjectile


class Missile(Weapon):
    name = "导弹"
    desc = "爆炸 | 范围伤害"
    color = Color.ORANGE
    damage = 30
    fire_rate = 45
    is_ranged = True
    projectile_count = 1
    projectile_speed = 5
    explosion_radius = 75
    homing = False

    # 武器升级颜色标准：伤害-RED | 追踪-GREEN | 爆炸-ORANGE | 数量-YELLOW
    upgrades = [
        Upgrade("missile_homing", "追踪弹", "导弹追踪敌人", Color.GREEN,
                lambda p, w: setattr(w, 'homing', True), UPGRADE_ONCE),
        Upgrade("missile_radius", "扩大爆炸", "爆炸范围 +25, 伤害 +5", Color.ORANGE,
                lambda p, w: (setattr(w, 'explosion_radius', w.explosion_radius + 25),
                              setattr(w, 'damage', w.damage + 5))),
        Upgrade("missile_damage", "高爆弹头", "导弹伤害 +8", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 8)),
    ]

    def attack(self, attacker, targets, dt=None):
        """发射导弹"""
        count = self.projectile_count
        projectiles = []
        for i in range(count):
            a = attacker.angle if count == 1 else attacker.angle - 0.15 + i * 0.3
            p = MissileProjectile(
                attacker.x, attacker.y, a, self.projectile_speed,
                weapon=self, owner=attacker,
                homing=self.homing,
                targets=targets or []
            )
            projectiles.append(p)
        return projectiles

    def _deal_damage(self, target, targets, attacker, proj):
        """导弹命中 → 爆炸范围伤害"""
        results = []
        for m in list(targets):
            if m.dead:
                continue
            dist = math.hypot(proj.x - m.x, proj.y - m.y)
            if dist < self.explosion_radius:
                ratio = 1 - dist / self.explosion_radius
                dmg = max(1, int(self.damage * ratio))
                actual, reaction = m.take_damage(dmg, attacker=attacker)
                results.append(DamageResult(m, actual))
                results.extend(reaction)

        # 爆炸特效数据
        results.append(DamageResult(None, 0, effects=[{
            "type": EffectType.EXPLOSION,
            "x": proj.x, "y": proj.y,
            "radius": self.explosion_radius,
        }]))
        return results

    def get_display_stats(self):
        return [
            f"伤害: {self.damage}",
            f"射速: {60/self.fire_rate:.1f}/s",
            f"爆炸范围: {self.explosion_radius}",
            f"追踪: {'是' if self.homing else '否'}",
        ]
