"""
召唤武器 - 定期在玩家位置创建炮台，自动攻击附近敌人
"""
import math
import random
import pygame
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE
from core.config import Color


class Turret:
    """炮台 - 轻量实体，固定位置自动攻击"""

    def __init__(self, x, y, weapon, owner, lifetime=8.0):
        self.x = x
        self.y = y
        self.weapon = weapon
        self.owner = owner  # 玩家，用于投射物归属
        self.lifetime = lifetime
        self.cooldown = 0
        self.angle = 0
        self.size = 14

    def update(self, targets, dt):
        """更新炮台：倒计时 + 自动攻击，返回 (DamageResult列表, Projectile列表)"""
        self.lifetime -= dt
        if self.lifetime <= 0:
            return [], []

        self.cooldown = max(0, self.cooldown - dt)

        if not targets or self.cooldown > 0:
            return [], []

        # 瞄准最近敌人
        nearest = None
        min_dist = float('inf')
        for t in targets:
            if t.dead:
                continue
            d = math.hypot(t.x - self.x, t.y - self.y)
            if d < min_dist:
                min_dist = d
                nearest = t

        if not nearest:
            return [], []

        self.angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
        self.cooldown = self.weapon.fire_rate / 60

        # 发射投射物
        projs = self.weapon.attack(self, targets, dt)
        # 投射物归属设为玩家（友方判定 + 吸血触发）
        for p in projs:
            p.owner = self.owner
            p.is_enemy = False
            # 回旋镖返回目标设为炮台
            if hasattr(p, 'return_target'):
                p.return_target = self
        return [], projs

    def draw(self, surface, cam_x=0, cam_y=0):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        # 底座
        pygame.draw.circle(surface, Color.DARK_GRAY, (sx, sy), self.size)
        pygame.draw.circle(surface, Color.WHITE, (sx, sy), self.size, 2)
        # 炮管
        end_x = sx + math.cos(self.angle) * (self.size + 6)
        end_y = sy + math.sin(self.angle) * (self.size + 6)
        pygame.draw.line(surface, Color.WHITE, (sx, sy), (int(end_x), int(end_y)), 3)
        # 生命条（剩余时间）
        ratio = max(0, self.lifetime / 8.0)
        bar_w = self.size * 2
        bar_h = 3
        bx = sx - bar_w // 2
        by = sy - self.size - 6
        pygame.draw.rect(surface, Color.DARK_GRAY, (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, Color.CYAN, (bx, by, int(bar_w * ratio), bar_h))


def _get_ranged_weapons():
    """获取所有远程武器类（is_ranged=True），自动支持新增武器"""
    from entities.weapons import player as mod
    result = []
    for name in dir(mod):
        cls = getattr(mod, name)
        if isinstance(cls, type) and issubclass(cls, Weapon) and getattr(cls, 'is_ranged', False):
            result.append(cls)
    return result


class SummonWeapon(Weapon):
    name = "召唤台"
    desc = "召唤 | 自动生成炮台"
    color = Color.CYAN
    damage = 0
    fire_rate = 180  # 3秒生成一个炮台
    # 召唤专属属性
    turret_lifetime = 8.0
    turret_damage_mult = 1.0    # 炮台伤害倍率
    turret_fire_rate_bonus = 0   # 炮台武器额外攻速（减少 fire_rate）
    _UPG_OVERLOAD_MAX = 5       # 过载最多选5次

    upgrades = [
        Upgrade("summon_lifetime", "持久作战", "炮台持续时间 +3秒", Color.BLUE,
                lambda p, w: setattr(w, 'turret_lifetime', w.turret_lifetime + 3)),
        Upgrade("summon_rapid", "快速部署", "召唤间隔缩短", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(60, w.fire_rate - 30)), _UPG_OVERLOAD_MAX),
        Upgrade("summon_damage", "武装强化", "炮台伤害 +50%", Color.RED,
                lambda p, w: w._apply_damage_mult(0.5)),
        Upgrade("summon_atkspd", "过载", "炮台攻速提升", Color.RED,
                lambda p, w: w._apply_fire_rate_bonus(3), _UPG_OVERLOAD_MAX),
    ]

    def __init__(self):
        super().__init__()
        self._turrets = []
        self._spawn_cooldown = 0

    def _apply_damage_mult(self, add_mult):
        """升级炮台伤害倍率，同步应用到所有已有炮台"""
        self.turret_damage_mult += add_mult
        for turret in self._turrets:
            turret.weapon.damage = int(turret.weapon._base_damage * self.turret_damage_mult)

    def _apply_fire_rate_bonus(self, add_fr):
        """升级炮台攻速，同步应用到所有已有炮台"""
        self.turret_fire_rate_bonus += add_fr
        for turret in self._turrets:
            turret.weapon.fire_rate = max(2, turret.weapon._base_fire_rate - self.turret_fire_rate_bonus)

    def attack(self, attacker, targets, dt=None):
        """召唤台不自己攻击"""
        return []

    def update(self, attacker, targets, dt):
        """定期生成炮台 + 更新所有炮台"""
        results = []
        self.pending_projectiles.clear()

        # 生成新炮台
        self._spawn_cooldown -= dt
        if self._spawn_cooldown <= 0:
            ranged_classes = _get_ranged_weapons()
            if ranged_classes:
                weapon_cls = random.choice(ranged_classes)
                weapon_inst = weapon_cls()
                # 记录基础值（供升级时重新计算）
                weapon_inst._base_damage = weapon_inst.damage
                weapon_inst._base_fire_rate = weapon_inst.fire_rate
                # 应用已有炮台强化加成
                weapon_inst.damage = int(weapon_inst.damage * self.turret_damage_mult)
                weapon_inst.fire_rate = max(2, weapon_inst.fire_rate - self.turret_fire_rate_bonus)
                turret = Turret(
                    attacker.x, attacker.y,
                    weapon_inst,
                    owner=attacker,
                    lifetime=self.turret_lifetime
                )
                self._turrets.append(turret)
                self._spawn_cooldown = self.fire_rate / 60

        # 更新所有炮台
        alive_turrets = []
        for turret in self._turrets:
            dmg_results, projs = turret.update(targets, dt)
            results.extend(dmg_results)
            self.pending_projectiles.extend(projs)
            if turret.lifetime > 0:
                alive_turrets.append(turret)
        self._turrets = alive_turrets

        return results

    def draw(self, surface, cam_x=0, cam_y=0, px=0, py=0):
        """绘制所有炮台"""
        for turret in self._turrets:
            turret.draw(surface, cam_x, cam_y)

    def get_display_stats(self):
        spawn_interval = self.fire_rate / 60
        return [
            f"召唤间隔: {spawn_interval:.1f}s",
            f"持续时间: {self.turret_lifetime:.0f}s",
        ]
