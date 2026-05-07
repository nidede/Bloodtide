"""
武器升级配置 - 集中管理所有武器的升级选项
方便平衡调整和添加新武器

用法:
    from core.weapon_upgrades import make_upgrade, RIFLE_UPGRADES
    
    # 在武器类中使用
    upgrades = [
        make_upgrade(*RIFLE_UPGRADES[0]),  # rifle_damage
        make_upgrade(*RIFLE_UPGRADES[1]),  # rifle_rapid
        ...
    ]
"""
from entities.weapons.base import Upgrade
from core.config import Color


def make_upgrade(uid, name, desc, color, apply_fn):
    """从配置元组创建 Upgrade 对象"""
    return Upgrade(uid, name, desc, color, apply_fn)


# ============ 步枪升级配置 ============
# 格式: (id, 名称, 描述, 颜色, apply_fn)
RIFLE_UPGRADES = [
    ("rifle_damage", "强化枪管", "步枪伤害 +3", Color.RED,
     lambda p, w: setattr(w, 'damage', w.damage + 3)),
    
    ("rifle_rapid", "轻量化", "步枪射速提升", Color.BLUE,
     lambda p, w: setattr(w, 'fire_rate', max(3, w.fire_rate - 1))),
    
    ("rifle_burst", "三连发", "弹幕 +2 散射略增", Color.YELLOW,
     lambda p, w: (setattr(w, 'projectile_count', w.projectile_count + 2),
                   setattr(w, 'spread', w.spread + 0.05))),
    
    ("rifle_sniper", "狙击", "伤害+5 射速降低", Color.RED,
     lambda p, w: (setattr(w, 'damage', w.damage + 5),
                   setattr(w, 'fire_rate', min(15, w.fire_rate + 3)),
                   setattr(w, 'crit_chance', w.crit_chance + 0.05))),
    
    ("rifle_piercing", "穿透弹", "子弹穿透 +1", Color.PURPLE,
     lambda p, w: setattr(w, 'piercing', w.piercing + 1)),
    
    ("rifle_crit", "精准暴击", "暴击率 +10%", Color.GOLD,
     lambda p, w: setattr(w, 'crit_chance', min(0.8, w.crit_chance + 0.10))),
    
    ("rifle_critd", "穿甲弹", "暴击伤害 +50%", Color.GOLD,
     lambda p, w: setattr(w, 'crit_damage', w.crit_damage + 0.50)),
]

# ============ 导弹升级配置 ============
MISSILE_UPGRADES = [
    ("missile_homing", "追踪弹", "导弹追踪敌人", Color.GREEN,
     lambda p, w: setattr(w, 'homing', True)),
    
    ("missile_radius", "扩大爆炸", "爆炸范围 +25, 伤害 +5", Color.ORANGE,
     lambda p, w: (setattr(w, 'explosion_radius', w.explosion_radius + 25),
                   setattr(w, 'damage', w.damage + 5))),
    
    ("missile_damage", "高爆弹头", "导弹伤害 +8", Color.RED,
     lambda p, w: setattr(w, 'damage', w.damage + 8)),
]

# ============ 飞刀升级配置 ============
BLADE_UPGRADES = [
    ("blade_count", "更多飞刀", "飞刀 +1", Color.YELLOW,
     lambda p, w: (setattr(w, 'blade_count', w.blade_count + 1),
                   setattr(w, 'angles', w._calc_angles()),
                   w.total_rotations.append(0.0),
                   setattr(w, 'cooldowns', dict({**w.cooldowns, w.blade_count - 1: {}})))),
    
    ("blade_speed", "极速旋转", "旋转速度大幅提升", Color.CYAN,
     lambda p, w: setattr(w, 'rotation_speed', w.rotation_speed + 2.0)),
    
    ("blade_damage", "锋刃", "飞刀伤害 +3", Color.RED,
     lambda p, w: setattr(w, 'damage', w.damage + 3)),
    
    ("blade_range", "扩展范围", "飞刀旋转半径 +20, 伤害 +1", Color.CYAN,
     lambda p, w: (setattr(w, 'orbit_radius', w.orbit_radius + 20),
                   setattr(w, 'damage', w.damage + 1))),
    
    ("blade_length", "加长刀刃", "飞刀长度 +12", Color.CYAN,
     lambda p, w: setattr(w, 'blade_length', w.blade_length + 12)),
]


# ============ 预构建升级列表（可直接使用） ============
def build_rifle_upgrades():
    """构建步枪升级列表"""
    return [make_upgrade(*u) for u in RIFLE_UPGRADES]

def build_missile_upgrades():
    """构建导弹升级列表"""
    return [make_upgrade(*u) for u in MISSILE_UPGRADES]

def build_blade_upgrades():
    """构建飞刀升级列表"""
    return [make_upgrade(*u) for u in BLADE_UPGRADES]
