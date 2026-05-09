"""
喷火器 - 扇形火焰，范围持续伤害
"""
import math
import random
import pygame
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE, EffectType
from core.config import Color


class Flamethrower(Weapon):
    name = "喷火器"
    desc = "喷射 | 扇形火焰"
    color = Color.ORANGE
    damage = 8
    fire_rate = 8  # 极快射速，持续喷火
    # 喷火器专属属性
    flame_range = 150       # 火焰距离
    flame_angle = 0.5       # 扇形半角（弧度，总张角1.0约57度）
    burn_enabled = False    # 是否附带燃烧（升级解锁）

    upgrades = [
        Upgrade("flame_damage", "烈焰", "喷火器伤害 +3", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 3)),
        Upgrade("flame_range", "远射", "火焰距离 +30", Color.BLUE,
                lambda p, w: setattr(w, 'flame_range', w.flame_range + 30)),
        Upgrade("flame_spread", "广角喷射", "扇形角度增大", Color.YELLOW,
                lambda p, w: setattr(w, 'flame_angle', w.flame_angle + 0.15)),
        Upgrade("flame_burn", "燃烧", "命中附带燃烧效果（可叠加）", Color.GREEN,
                lambda p, w: setattr(w, 'burn_enabled', True), UPGRADE_ONCE),
    ]

    def attack(self, attacker, targets, dt=None):
        """喷火器不需要发射投射物"""
        return []

    def _deal_damage(self, target, targets, attacker, proj):
        """喷火器伤害"""
        effects = []
        if self.burn_enabled:
            effects.append({"type": EffectType.BURN})
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual, effects=effects)] + reaction

    def update(self, attacker, targets, dt):
        """持续喷火 - 对扇形范围内敌人造成伤害"""
        if not hasattr(self, '_cooldown'):
            self._cooldown = 0
        self._cooldown -= dt
        if self._cooldown > 0:
            return []

        if not targets:
            return []

        # 记录命中目标和玩家朝向（用于绘制）
        self._hit_targets = []
        self._last_angle = attacker.angle

        results = []
        hit_ids = set()
        # 扇形范围内所有敌人
        for target in targets:
            if target.dead:
                continue
            tid = id(target)
            dx = target.x - attacker.x
            dy = target.y - attacker.y
            dist = math.hypot(dx, dy)
            if dist > self.flame_range or dist < 1:
                continue
            # 角度判定
            angle_to_target = math.atan2(dy, dx)
            angle_diff = angle_to_target - attacker.angle
            # 归一化到 [-pi, pi]
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_diff) > self.flame_angle:
                continue

            if tid in hit_ids:
                continue
            hit_ids.add(tid)
            self._hit_targets.append((target.x, target.y, dist))

            hit_result = self.deal_damage(target, targets, attacker, None)
            results.extend(hit_result)

        if hit_ids:
            self._cooldown = self.fire_rate / 60

        return results

    def draw(self, surface, cam_x=0, cam_y=0, px=0, py=0):
        """绘制扇形火焰 - 随机粒子模拟火焰抖动"""
        if not hasattr(self, '_hit_targets'):
            return
        if not hasattr(self, '_last_angle'):
            return

        cx, cy = px - cam_x, py - cam_y
        half_angle = self.flame_angle
        angle = self._last_angle

        # 在扇形区域内随机撒粒子，近处密远处疏
        for _ in range(40):
            # 距离：偏向近处（平方根分布让近处更密）
            dist_ratio = random.random() ** 0.5
            dist = self.flame_range * dist_ratio
            # 角度：均匀分布在扇形内，加随机抖动
            a = angle + random.uniform(-half_angle, half_angle) * dist_ratio
            # 随机偏移增加抖动感
            a += random.uniform(-0.08, 0.08)
            px2 = cx + math.cos(a) * dist
            py2 = cy + math.sin(a) * dist

            # 颜色渐变：近=黄 中=橙 远=红
            if dist_ratio < 0.3:
                color = (255, 230, 50)   # 黄色核心
                radius = random.randint(2, 4)
            elif dist_ratio < 0.6:
                color = (255, 160, 30)   # 橙色中间
                radius = random.randint(2, 3)
            else:
                color = (220, 60, 20)    # 红色边缘
                radius = random.randint(1, 3)

            pygame.draw.circle(surface, color, (int(px2), int(py2)), radius)

        # 命中点爆火花
        for tx, ty, dist in self._hit_targets:
            sx_t = tx - cam_x
            sy_t = ty - cam_y
            for _ in range(3):
                ox = random.randint(-6, 6)
                oy = random.randint(-6, 6)
                pygame.draw.circle(surface, Color.YELLOW,
                                 (int(sx_t + ox), int(sy_t + oy)), 3)
                pygame.draw.circle(surface, (255, 255, 200),
                                 (int(sx_t + ox), int(sy_t + oy)), 1)

    def get_display_stats(self):
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"范围: {self.flame_range}",
            f"角度: {math.degrees(self.flame_angle * 2):.0f}°",
        ]
