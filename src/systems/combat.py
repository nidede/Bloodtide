"""
战斗系统 - 怪物碰撞、伤害计算、死亡处理
"""
import math
import random
from core.config import Color, OrbConfig, CombatConfig, MonsterConfig


class CombatSystem:
    """战斗系统 - 处理所有战斗相关逻辑"""

    def __init__(self):
        self._dead_monsters = set()
        self._dead_orbs = set()

    def update_projectiles(self, projectiles, monsters, player, particles, floating_texts, dt):
        """处理投射物与怪物的碰撞 - 只负责碰撞检测，伤害逻辑由投射物自己处理"""
        for proj in projectiles:
            proj.update(dt)
            
            # 怪物子弹：只检查与玩家的碰撞
            is_monster_bullet = hasattr(proj.owner, 'monster_type') and proj.owner is not None
            if is_monster_bullet:
                dist = math.hypot(proj.x - player.x, proj.y - player.y)
                if dist < proj.size + player.size:
                    player.take_damage(proj.damage, particles)
                    floating_texts.append(self._create_floating_text(
                        player.x, player.y - player.size - 10,
                        str(proj.damage), Color.RED, 22
                    ))
                    proj.alive = False
                continue
            
            # 玩家子弹：碰撞检测 + 委托投射物处理伤害
            for monster in monsters:
                if proj.owner is not None and proj.owner is monster:
                    continue
                if id(monster) in proj.hit_monsters:
                    continue
                dist = math.hypot(proj.x - monster.x, proj.y - monster.y)
                if dist < proj.size + monster.size:
                    damage, is_crit = proj.deal_damage(monster, player, particles, floating_texts)

                    for _ in range(CombatConfig.HIT_PARTICLE_COUNT):
                        particles.append(
                            self._create_particle(proj.x, proj.y, Color.YELLOW,
                                                  speed=CombatConfig.HIT_PARTICLE_SPEED,
                                                  lifetime=CombatConfig.HIT_PARTICLE_LIFETIME)
                        )
                    break

    def update_monsters(self, monsters, player, projectiles, particles, floating_texts, dt, is_visible):
        """处理怪物AI、移动和近战碰撞"""
        for monster in monsters:
            if is_visible(monster.x, monster.y, CombatConfig.MONSTER_VISIBLE_RANGE):
                if monster.monster_type == "ranged":
                    dist = math.hypot(player.x - monster.x, player.y - monster.y)
                    dx = player.x - monster.x
                    dy = player.y - monster.y
                    if dist > 0:
                        if dist < CombatConfig.MELEE_RANGE:
                            move_dx = -(dx / dist) * monster.speed * dt
                            move_dy = -(dy / dist) * monster.speed * dt
                        elif dist < CombatConfig.OPTIMAL_RANGE:
                            move_dx = (dx / dist) * monster.speed * CombatConfig.RETREAT_SPEED_RATIO * dt
                            move_dy = (dy / dist) * monster.speed * CombatConfig.RETREAT_SPEED_RATIO * dt
                        else:
                            move_dx = (dx / dist) * monster.speed * dt
                            move_dy = (dy / dist) * monster.speed * dt
                        monster.x += move_dx
                        monster.y += move_dy
                    monster.attack_cooldown = max(0, monster.attack_cooldown - dt)
                    monster.flash_timer = max(0, monster.flash_timer - dt)
                else:
                    monster.update(player, dt)
            else:
                monster.attack_cooldown = max(0, monster.attack_cooldown - dt)
                monster.flash_timer = max(0, monster.flash_timer - dt)
                dx = player.x - monster.x
                dy = player.y - monster.y
                dist = math.hypot(dx, dy)
                if dist > 0 and dist < CombatConfig.DETECTION_RANGE:
                    monster.x += (dx / dist) * monster.speed * CombatConfig.CHASE_SPEED_RATIO

            if hasattr(monster, 'attack'):
                monster.attack(player, projectiles)
            if monster.collides_with_player(player) and monster.attack_cooldown <= 0:
                dmg = player.take_damage(monster.damage, particles)
                monster.attack_cooldown = MonsterConfig.ATTACK_COOLDOWN

                if player.thorns > 0:
                    monster.hp -= player.thorns
                    floating_texts.append(self._create_floating_text(
                        monster.x, monster.y - monster.size,
                        str(player.thorns), Color.PURPLE, 16
                    ))

                if dmg > 0:
                    floating_texts.append(self._create_floating_text(
                        player.x, player.y - player.size - 10,
                        str(dmg), Color.RED, 22
                    ))
                    return dmg
        return 0

    def process_dead_monsters(self, monsters, player, xp_orbs, particles, floating_texts):
        """处理怪物死亡和掉落"""
        for m in monsters:
            if m.dead:
                player.kills += 1
                orb_count = CombatConfig.BOSS_ORB_COUNT if m.monster_type == "boss" else CombatConfig.NORMAL_ORB_COUNT
                for _ in range(orb_count):
                    ox = m.x + random.randint(-CombatConfig.ORB_DROP_OFFSET, CombatConfig.ORB_DROP_OFFSET)
                    oy = m.y + random.randint(-CombatConfig.ORB_DROP_OFFSET, CombatConfig.ORB_DROP_OFFSET)
                    is_magnet = random.random() < OrbConfig.MAGNET_DROP_CHANCE
                    from ui.effects import XPOrb
                    xp_orbs.append(XPOrb(ox, oy, m.xp_value // orb_count, is_magnet))
                for _ in range(CombatConfig.DEATH_PARTICLE_COUNT):
                    particles.append(
                        self._create_particle(m.x, m.y, m.color,
                                              speed=CombatConfig.PARTICLE_DEATH_SPEED,
                                              lifetime=CombatConfig.PARTICLE_DEATH_LIFETIME)
                    )
                self._dead_monsters.add(id(m))

    def cleanup(self, monsters, xp_orbs):
        """清理死亡的怪物和经验球"""
        monsters[:] = [m for m in monsters if id(m) not in self._dead_monsters]
        self._dead_monsters.clear()
        xp_orbs[:] = [o for o in xp_orbs if id(o) not in self._dead_orbs]
        self._dead_orbs.clear()

    def mark_orb_dead(self, orb_id):
        """标记经验球为待删除"""
        self._dead_orbs.add(orb_id)

    def handle_explosions(self, projectiles, monsters, particles, floating_texts):
        """处理导弹爆炸"""
        for proj in projectiles:
            if hasattr(proj, 'explode') and not proj.alive and not getattr(proj, '_exploded', False):
                proj._exploded = True
                proj.explode(monsters, particles, floating_texts)

    def check_player_death(self, player, particles):
        """检查玩家是否死亡"""
        return player.hp <= 0

    def spawn_death_particles(self, player, particles):
        """生成玩家死亡粒子"""
        for _ in range(CombatConfig.PLAYER_DEATH_PARTICLE_COUNT):
            particles.append(
                self._create_particle(player.x, player.y, Color.RED,
                                      speed=CombatConfig.PARTICLE_PLAYER_DEATH_SPEED,
                                      lifetime=CombatConfig.PARTICLE_PLAYER_DEATH_LIFETIME,
                                      size=5)
            )

    def _create_particle(self, x, y, color, speed=120, lifetime=0.25, size=3):
        """创建粒子"""
        from ui.effects import Particle
        return Particle(x, y, color, speed, lifetime, size)

    def _create_floating_text(self, x, y, text, color, size, lifetime=0.5):
        """创建浮动文字"""
        from ui.effects import FloatingText
        return FloatingText(x, y, text, color, size, lifetime)
