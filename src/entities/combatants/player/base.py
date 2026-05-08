"""
角色基类 - 所有玩家角色的父类

提供通用属性和方法：
- 等级/经验系统: gain_xp(), on_level_up()
- 受伤系统: take_damage() 带无敌帧和减伤
- 射击系统: try_shoot()
- 工具方法: _find_nearest()

子类需重写:
- on_level_up(): 定义升级时自动增加的属性
- handle_input(): 定义输入方式（可能不同角色操作不同）
- draw(): 定义外观
"""
import math
from core.config import Color, WORLD_WIDTH, WORLD_HEIGHT, PlayerConfig
from entities.combatants.base import CombatEntity
from entities.weapons.base import UPGRADE_ONCE


class Character(CombatEntity):
    """角色基类 - 继承战斗实体"""

    # 通用属性默认值
    attack = 0
    defense = 0
    crit_chance = 0.05
    crit_damage = 1.5
    life_steal = 0
    regen = 0
    xp_multiplier = 1.0
    # 可选：角色专属升级列表
    upgrades = []

    def __init__(self, x, y):
        super().__init__(x, y)

        # 从类属性初始化实例属性
        self.speed = self.__class__.speed
        self.max_hp = self.__class__.max_hp
        self.hp = self.max_hp
        self.defense = self.__class__.defense
        self.crit_chance = self.__class__.crit_chance
        self.crit_damage = self.__class__.crit_damage
        self.life_steal = self.__class__.life_steal
        self.regen = self.__class__.regen
        self.xp_multiplier = self.__class__.xp_multiplier

        # 等级/经验
        self.level = 1
        self.xp = 0
        self.xp_to_next = 50

        # 通用计时器
        self.cooldown_timer = 0
        self.invincible_timer = 0
        self.regen_timer = 0

        # 通用状态
        self.kills = 0
        self.angle = 0.0
        self.weapon = None
        self.facing_right = True

        # 冲刺
        self.has_dash = False
        self.dash_cooldown = 0
        self.dash_speed = 0.0

        # 升级计数
        self._upgrade_counts = {}

        # 注册效果
        self.add_effect(self.ON_DEAL_DAMAGE, self._lifesteal_effect)

    def gain_xp(self, amount):
        """获得经验，升级时调用 on_level_up()

        Returns:
            int: 本次升级的级数（0 表示未升级）
        """
        self.xp += int(amount * self.xp_multiplier)
        levels = 0
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.4)
            self.on_level_up()
            levels += 1
        return levels

    def on_level_up(self):
        """升级奖励 - 子类重写定义自动增加的属性"""
        pass

    def _calc_actual_damage(self, damage):
        """玩家受伤 - 无敌帧判断 + 减伤"""
        if self.invincible_timer > 0:
            return 0
        return max(1, damage - self.defense)

    def _on_take_damage(self, actual, attacker):
        """玩家受伤后 - 设置无敌帧"""
        self.invincible_timer = PlayerConfig.INVINCIBLE_FRAMES / 60

    def _on_hit_by(self, attacker, damage):
        """玩家被击中后 - 子类重写（如 Soldier 的反伤）"""
        return []

    def _lifesteal_effect(self, target, damage, **kwargs):
        """吸血效果 - 造成伤害时回复生命"""
        if self.life_steal > 0 and damage > 0:
            heal = max(1, int(damage * self.life_steal))
            self.hp = min(self.max_hp, self.hp + heal)

    def try_shoot(self, targets, dt):
        """通用射击逻辑"""
        if self.cooldown_timer > 0 or not targets or not self.weapon:
            return []
        nearest = self._find_nearest(targets)
        if not nearest:
            return []
        projs = self.weapon.attack(self, targets, dt)
        if projs:
            self.cooldown_timer = self.weapon.fire_rate / 60
        return projs

    def _find_nearest(self, targets):
        """找最近的目标"""
        if not targets:
            return None
        nearest = None
        min_dist = float('inf')
        for t in targets:
            dist = math.hypot(t.x - self.x, t.y - self.y)
            if dist < min_dist:
                min_dist = dist
                nearest = t
        return nearest

    def _update_timers(self, dt):
        """更新通用计时器"""
        self.cooldown_timer = max(0, self.cooldown_timer - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)
        self.dash_cooldown = max(0, self.dash_cooldown - dt)

        # 生命恢复
        if self.regen > 0:
            self.regen_timer += dt
            if self.regen_timer >= 1.0:
                self.regen_timer = 0
                self.hp = min(self.max_hp, self.hp + self.regen)

    def _clamp_position(self):
        """限制在世界边界内"""
        self.x = max(self.size, min(WORLD_WIDTH - self.size, self.x))
        self.y = max(self.size, min(WORLD_HEIGHT - self.size, self.y))

    # ========== 升级数值常量 - 子类可覆盖 ==========

    UPG_SPEED = 10
    UPG_MAX_HP = 30
    UPG_DEFENSE = 3
    UPG_LIFE_STEAL = 0.05
    UPG_REGEN = 2
    UPG_XP = 0.2

    # ========== 通用升级方法 - 子类可重写 ==========

    def _apply_speed(self, weapon):
        self.speed += self.UPG_SPEED

    def _apply_max_hp(self, weapon):
        self.max_hp += self.UPG_MAX_HP
        self.hp += self.UPG_MAX_HP

    def _apply_defense(self, weapon):
        self.defense += self.UPG_DEFENSE

    def _apply_life_steal(self, weapon):
        self.life_steal += self.UPG_LIFE_STEAL

    def _apply_regen(self, weapon):
        self.regen += self.UPG_REGEN

    def _apply_xp(self, weapon):
        self.xp_multiplier += self.UPG_XP

    def _apply_dash(self, weapon):
        self.has_dash = True

    # ========== 通用升级池 ==========
    # 格式：(uid, name, desc, color, apply_fn, max_count)
    # max_count: 可选次数上限，UPGRADE_UNLIMITED 表示无限

    GENERAL_UPGRADES = [
        ("speed",      "跑快点",   f"移动速度 +{UPG_SPEED}",              Color.CYAN,   lambda p, w: p._apply_speed(w)),
        ("max_hp",     "血量上限", f"最大生命 +{UPG_MAX_HP}",              Color.BLUE,   lambda p, w: p._apply_max_hp(w)),
        ("defense",    "护甲",     f"防御力 +{UPG_DEFENSE}",              Color.BLUE,   lambda p, w: p._apply_defense(w)),
        ("life_steal", "吸血",     f"生命偷取 +{int(UPG_LIFE_STEAL*100)}%", Color.GREEN,  lambda p, w: p._apply_life_steal(w)),
        ("regen",      "生命恢复", f"每秒回复 +{UPG_REGEN}",              Color.GREEN,  lambda p, w: p._apply_regen(w)),
        ("xp",         "经验加成", f"经验获取 +{int(UPG_XP*100)}%",       Color.YELLOW, lambda p, w: p._apply_xp(w)),
        ("dash",       "冲刺",     "解锁空格冲刺",                        Color.CYAN,   lambda p, w: p._apply_dash(w), UPGRADE_ONCE),
    ]
