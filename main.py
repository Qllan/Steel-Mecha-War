import pygame, math, random, sys

pygame.init()
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
F_BIG  = pygame.font.Font(None, 84)
F_HUGE = pygame.font.Font(None, 140)
F_MED  = pygame.font.Font(None, 44)
F_SM   = pygame.font.Font(None, 28)
F_TINY = pygame.font.Font(None, 20)

C_BG, C_GRID = (10, 11, 16), (24, 26, 36)
C_WHITE, C_BLUE = (235, 240, 255), (0, 200, 255)
C_RED, C_YELLOW = (255, 45, 45), (255, 210, 40)
C_GREEN, C_ORANGE = (40, 255, 110), (255, 140, 0)
C_CYAN = (60, 230, 255)
C_MAGENTA = (255, 80, 200)
C_DARKRED = (200, 70, 70)
C_MINT = (120, 255, 180)
C_DIM = (90, 95, 105)
C_GOLD = (255, 200, 80)
MAP_W, MAP_H = 2400, 2400
WAVES = [{'mt':4,'elite':0}, {'mt':5,'elite':1}, {'mt':6,'elite':2}]
SCAN_MAX, SCAN_DRAIN, SCAN_CD = 4.0, 25.0, 3.5
VERSION = "v0.2.1 // MEAT SHIELD"
_WIN_EVENT = getattr(pygame, 'WINDOWEVENT', None)
_WIN_FOCUS_LOST = getattr(pygame, 'WINDOWEVENT_FOCUS_LOST', None)
_ACTIVE_EVENT = getattr(pygame, 'ACTIVEEVENT', None)

PARTS = {
 'r_arm': {
   'rifle':  dict(n='ASSAULT RIFLE', cost=0,    w=30, cd=0.09, dmg=9,  stag=3,  encost=0, bspd=900, sz=2, col=C_YELLOW, knock=0,   desc='Rapid, low dmg'),
   'pulse':  dict(n='PULSE RIFLE',   cost=1200, w=35, cd=0.16, dmg=14, stag=5,  encost=2, bspd=850, sz=3, col=C_CYAN,   knock=0,   desc='Balanced energy'),
   'cannon': dict(n='HEAVY CANNON',  cost=800,  w=60, cd=0.75, dmg=85, stag=30, encost=6, bspd=680, sz=6, col=C_ORANGE, knock=260, desc='Huge dmg, knockback'),
   'rail':   dict(n='RAILGUN',       cost=2500, w=70, cd=1.8,  dmg=120,stag=60, encost=35,bspd=0,   sz=0, col=C_CYAN,   knock=0,   desc='Charged piercing beam', unlock=True),
 },
 'l_arm': {
   'shotgun':dict(n='SHOTGUN',       cost=0,    w=35, desc='RMB burst, range falloff'),
   'shield': dict(n='ENERGY SHIELD', cost=600,  w=25, desc='RMB block + perfect guard'),
   'grenade':dict(n='GRENADE LNCHR', cost=1500, w=45, desc='RMB lob, AoE stagger'),
 },
 'legs': {
   'biped':  dict(n='BIPEDAL',       cost=0,    w=50,  ap=350, spd=340, desc='Balanced'),
   'rjoint': dict(n='REVERSE-JOINT', cost=1400, w=40,  ap=280, spd=400, desc='Fast, fragile'),
   'tank':   dict(n='TANK',          cost=900,  w=110, ap=550, spd=245, desc='Slow, heavy armor'),
 },
 'gen': {
   'std':    dict(n='STD GENERATOR',   cost=0,    w=30, en=100, regen=22, desc='Standard EN'),
   'fast':   dict(n='FAST-CHARGE GEN', cost=1300, w=35, en=90,  regen=40, desc='Rapid regen'),
   'hcap':   dict(n='HIGH-CAP GEN',    cost=1000, w=45, en=150, regen=20, desc='Large EN pool'),
 },
}
SLOT_ORDER = ['r_arm', 'l_arm', 'legs', 'gen']
SLOT_LABEL = {'r_arm':'R-ARM', 'l_arm':'L-ARM', 'legs':'LEGS', 'gen':'GENERATOR'}
DEFAULT_PARTS = {'r_arm':'rifle', 'l_arm':'shotgun', 'legs':'biped', 'gen':'std'}

MISSIONS = [
 {'id':'m1','code':'MISSION 01','name':'HOSTILE SWEEP','reward':1000,'boss':True,'targets':0,
  'obj':'Eliminate all MT waves. Defeat rival AC VINDICTA.',
  'brief':['Hostile MT squad detected in sector 7.','Commander-class units providing fire support.',
           'Rival AC signature confirmed - VINDICTA, Heavy Cavalry ace.','Sweep the sector. Neutralize all hostiles.']},
 {'id':'m2','code':'MISSION 02','name':'PRIORITY TARGETS','reward':1800,'boss':False,'targets':3,
  'obj':'Destroy 3 marked GUNNER emplacements. Escorts are optional.',
  'brief':['Three gunner emplacements are shelling our positions.','They are marked as PRIORITY TARGETS.',
           'Escort screen will physically block your shots - they interpose themselves.',
           'Use AoE or piercing weapons, or strip the screen first.','Destroy all three targets. Extraction on completion.']},
]

def rot_pts(cx, cy, pts, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x*c - y*s, cy + x*s + y*c) for x, y in pts]
def lerp(a, b, t): return a + (b - a) * t
def clamp(v, a, b): return max(a, min(b, v))

def loadout_preview(cfg):
    r = PARTS['r_arm'][cfg['r_arm']]; l = PARTS['l_arm'][cfg['l_arm']]
    lg = PARTS['legs'][cfg['legs']]; g = PARTS['gen'][cfg['gen']]
    w = r['w'] + l['w'] + lg['w'] + g['w']
    spd = lg['spd'] * clamp(1.2 - w/500, 0.7, 1.2)
    return dict(ap=lg['ap'], spd=int(spd), en=g['en'], regen=g['regen'], weight=w,
                boost=clamp(0.6 + w/250, 0.6, 1.8))

VIG = pygame.Surface((W, H), pygame.SRCALPHA)
for i in range(90):
    pygame.draw.rect(VIG, (0, 0, 12, int(150*(1-i/90)**2)), (i, i, W-2*i, H-2*i), 1)
SCANLINES = pygame.Surface((W, H), pygame.SRCALPHA)
for y in range(0, H, 3):
    pygame.draw.line(SCANLINES, (0, 0, 0, 30), (0, y), (W, y))

def draw_mech_shape(surf, cx, cy, ang, cfg, scale=1.0, body_col=None, ghost=False, thrust=False, dim=False):
    if body_col is None:
        body_col = (70, 90, 130) if ghost else ((120, 125, 135) if dim else C_WHITE)
    s = scale
    def poly(pts, col, width=0):
        pygame.draw.polygon(surf, col, rot_pts(cx, cy, [(x*s, y*s) for x, y in pts], ang), width)
    if thrust and not ghost:
        for side in (-1, 1):
            poly([(-20, side*12), (-30-random.randint(0,6), side*10), (-20, side*8)], C_CYAN)
    poly([(-18,-14),(12,-16),(26,0),(12,16),(-18,14)], body_col)
    poly([(-18,-14),(12,-16),(26,0),(12,16),(-18,14)], (35,45,65), 2)
    poly([(10,-5),(24,0),(10,5)], (40,70,110) if ghost else C_BLUE)
    if cfg['legs'] == 'tank':
        lt=[(-22,-20),(-2,-20),(-2,-10),(-22,-10)]; lb=[(-22,10),(-2,10),(-2,20),(-22,20)]
        lc=(80,95,115) if ghost else (110,120,140)
    elif cfg['legs'] == 'rjoint':
        lt=[(-18,-16),(-4,-16),(-8,-8),(-20,-8)]; lb=[(-18,8),(-4,8),(-8,16),(-20,16)]
        lc=(120,140,170) if ghost else (150,170,200)
    else:
        lt=[(-20,-18),(-6,-18),(-6,-9),(-20,-9)]; lb=[(-20,9),(-6,9),(-6,18),(-20,18)]
        lc=(120,140,170) if ghost else (170,180,200)
    poly(lt, lc); poly(lb, lc)
    ra = cfg['r_arm']
    if ra == 'cannon':
        poly([(4,7),(34,7),(34,16),(4,16)], (150,100,40) if ghost else C_ORANGE)
    elif ra == 'rail':
        poly([(2,8),(38,8),(38,13),(2,13)], (40,110,140) if ghost else C_CYAN)
    elif ra == 'pulse':
        poly([(6,7),(30,7),(30,12),(6,12)], (60,130,150) if ghost else C_CYAN)
    else:
        poly([(6,7),(30,7),(30,12),(6,12)], (150,160,180) if ghost else (200,205,220))
    la = cfg['l_arm']
    if la == 'shield':
        poly([(14,-16),(20,-16),(20,-2),(14,-2)], (40,110,160) if ghost else (40,170,230))
    elif la == 'grenade':
        poly([(4,-14),(22,-14),(22,-6),(4,-6)], (140,90,40) if ghost else C_ORANGE)
    else:
        poly([(6,-12),(24,-12),(24,-7),(6,-7)], (120,50,50) if ghost else (200,70,70))

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, col, spread=150):
        super().__init__()
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-spread, spread), random.uniform(-spread, spread)
        self.life = self.max_life = random.uniform(0.3, 0.6)
        self.col, self.size = col, random.randint(2, 5)
    def update(self, dt):
        self.x += self.vx*dt; self.y += self.vy*dt
        self.vx *= 0.96; self.vy *= 0.96
        self.life -= dt
        if self.life <= 0: self.kill()
    def draw(self, surf, cam):
        s = self.size*(self.life/self.max_life)
        pygame.draw.rect(surf, self.col, (self.x-cam[0]-s/2, self.y-cam[1]-s/2, s, s))

class DamageNumber(pygame.sprite.Sprite):
    def __init__(self, x, y, val, col):
        super().__init__()
        self.x, self.y, self.val, self.col = x, y, int(val), col
        self.life = 0.7; self.vy = -70
    def update(self, dt):
        self.y += self.vy*dt; self.vy *= 0.95; self.life -= dt
        if self.life <= 0: self.kill()
    def draw(self, surf, cam):
        txt = F_TINY.render(str(self.val), True, self.col)
        txt.set_alpha(clamp(int(255*self.life/0.7), 0, 255))
        surf.blit(txt, (self.x-cam[0], self.y-cam[1]))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, ang, spd, dmg, stag, col, owner, sz=3, falloff=False):
        super().__init__()
        self.x, self.y, self.ang, self.speed = x, y, ang, spd
        self.vx, self.vy = math.cos(ang)*spd, math.sin(ang)*spd
        self.dmg, self.stag, self.col, self.owner, self.sz = dmg, stag, col, owner, sz
        self.falloff, self.dist = falloff, 0.0
        self.rect = pygame.Rect(x-sz, y-sz, sz*2, sz*2)
    def update(self, dt):
        self.x += self.vx*dt; self.y += self.vy*dt
        self.dist += self.speed*dt
        self.rect.center = (self.x, self.y)
        if not (0 < self.x < MAP_W and 0 < self.y < MAP_H): self.kill()
    def draw(self, surf, cam):
        pygame.draw.circle(surf, self.col, (int(self.x-cam[0]), int(self.y-cam[1])), self.sz)

class Grenade(Bullet):
    def __init__(self, x, y, ang):
        super().__init__(x, y, ang, 420, 0, 0, C_ORANGE, 'player', 5)
        self.fuse = 0.9
    def update(self, dt):
        super().update(dt)
        self.fuse -= dt
    def draw(self, surf, cam):
        cx, cy = int(self.x-cam[0]), int(self.y-cam[1])
        pygame.draw.circle(surf, self.col, (cx, cy), self.sz)
        pygame.draw.circle(surf, C_YELLOW, (cx, cy), self.sz+3, 1)

class MortarShell(Bullet):
    def __init__(self, x, y, ang):
        super().__init__(x, y, ang, 210, 0, 0, C_MINT, 'enemy', 6)
        self.fuse = 2.4
    def update(self, dt):
        super().update(dt)
        self.fuse -= dt
    def draw(self, surf, cam):
        cx, cy = int(self.x-cam[0]), int(self.y-cam[1])
        r = self.sz + int(2*math.sin(pygame.time.get_ticks()/80))
        pygame.draw.circle(surf, self.col, (cx, cy), r)
        pygame.draw.circle(surf, C_MINT, (cx, cy), r+5, 1)

class Missile(Bullet):
    def __init__(self, x, y, ang, targets, owner):
        col = C_ORANGE if owner == 'player' else C_RED
        dmg = 55 if owner == 'player' else 22
        super().__init__(x, y, ang, 420, dmg, 35, col, owner, 4)
        self.targets, self.turn_spd = targets, 3.5
    def update(self, dt):
        tgt, min_d = None, 9999
        for e in self.targets:
            if not e.alive(): continue
            d = math.hypot(e.rect.centerx-self.x, e.rect.centery-self.y)
            if d < min_d: min_d, tgt = d, e
        if tgt:
            ta = math.atan2(tgt.rect.centery-self.y, tgt.rect.centerx-self.x)
            diff = ta - self.ang
            while diff > math.pi: diff -= 2*math.pi
            while diff < -math.pi: diff += 2*math.pi
            self.ang += clamp(diff, -self.turn_spd*dt, self.turn_spd*dt)
        self.vx, self.vy = math.cos(self.ang)*self.speed, math.sin(self.ang)*self.speed
        super().update(dt)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, is_boss=False, is_elite=False, is_target=False, force_type=None):
        super().__init__()
        self.x, self.y, self.is_boss, self.is_elite, self.is_target = x, y, is_boss, is_elite, is_target
        self.ang = 0
        self.mtype = 'striker'
        if not is_boss and not is_elite:
            if force_type: self.mtype = force_type
            else:
                r = random.random()
                self.mtype = 'striker' if r < 0.35 else ('rusher' if r < 0.60 else ('gunner' if r < 0.85 else 'mortar'))
        if is_boss:
            self.max_ap, self.max_stagger, self.spd, self.w = 2000, 280, 240, 50
        elif is_elite:
            self.max_ap, self.max_stagger, self.spd, self.w = 260, 95, 215, 22
        elif self.mtype == 'rusher':
            self.max_ap, self.max_stagger, self.spd, self.w = 85, 45, 220, 16
        elif self.mtype == 'gunner':
            self.max_ap, self.max_stagger, self.spd, self.w = 130, 60, 110, 20
        elif self.mtype == 'mortar':
            self.max_ap, self.max_stagger, self.spd, self.w = 110, 55, 100, 19
        else:
            self.max_ap, self.max_stagger, self.spd, self.w = 100, 55, 145, 18
        if is_target:
            self.max_ap = 160
        self.ap = self.max_ap
        self.stagger, self.stg_timer = 0, 0
        self.shoot_cd = random.uniform(0.5, 1.5)
        self.rect = pygame.Rect(x-self.w, y-self.w, self.w*2, self.w*2)
        self.vx = self.vy = 0
        self.qb_timer = 0
        self.phase2 = self.phase2_trigger = False
        self.hit_flash = 0
        self.telegraph = 0
        self.dodge_cd = random.uniform(0.5, 1.5)
        self.dodge_timer = 0; self.dvx = self.dvy = 0
        self.pending_ram = False
        self.contact_cd = 0
        self.burst_timer = 0; self.burst_ang = 0
        self.pref_dist = {'striker':340,'gunner':470,'mortar':520}.get(self.mtype, 300)
        self.slot_ang = random.uniform(0, 2*math.pi)
        self.phase = random.uniform(0, 2*math.pi)
        self.recover = 0
        self.relocate = 0
        self.aim_ang = 0
        self.dash_dir = None
        self.spawn_flash = 0.6 if is_elite else 0
        self.guard_of = None
        self.barrier_max = 60
        self.barrier = self.barrier_max
        self.barrier_active = True
        self.barrier_regen_cd = 0
        self.attack_n = 0
        self.enraged = False
        self.behavior = 'STRAFE'
        self.flank_side = random.choice([-1, 1])
        self.flank_timer = random.uniform(2.5, 5)
        self.flank_mode = random.choice([True, False])
        self.flank_mode_timer = random.uniform(5, 9)
        self.lunge_cd = random.uniform(0.8, 1.6)
        self.lunge_hit = False
        self.hunt_ang = random.uniform(0, 2*math.pi)
        self.boss_en_max = 100
        self.boss_en = 100
        self.boss_qb_cd = 0
        self.boss_blade_cd = 0
        self.boss_missile_cd = 2.0
        self.boss_burst_cd = 0
        self.boss_shotgun_cd = 0
        self.boss_burst_left = 0
        self.boss_burst_t = 0
        self.boss_muzzle = 0
        self.boss_blade_anim = 0
        self.boss_blade_pending = 0
        self.boss_ab = 0
        self.boss_orbit = random.choice([-1, 1])
        self.boss_orbit_t = random.uniform(2, 4)
        self.boss_ghosts = []
        self.boss_mode = 'ENGAGE'
    def take_damage(self, dmg, stag, game, col=C_YELLOW, bypass=False):
        if self.is_elite and self.barrier_active and not bypass:
            self.barrier -= dmg
            self.barrier_regen_cd = 4.0
            if game:
                bx = self.x + math.cos(self.ang)*self.w; by = self.y + math.sin(self.ang)*self.w
                for _ in range(4): game.particles.add(Particle(bx, by, C_CYAN, 160))
            if self.barrier <= 0:
                self.barrier = 0; self.barrier_active = False
                self.stg_timer = max(self.stg_timer, 1.0)
                if game:
                    game.add_float("BARRIER DOWN!", self.x, self.y-self.w-34, C_CYAN, big=True)
                    game.add_shake(6)
                    for _ in range(14): game.particles.add(Particle(self.x, self.y, C_CYAN, 220))
            return
        was_stg = self.stg_timer > 0
        self.ap -= dmg*(3.0 if was_stg else 1.0)
        self.stagger += stag
        self.hit_flash = 0.08
        if game:
            game.dmg_nums.add(DamageNumber(self.x, self.y-self.w-10, dmg*(3.0 if was_stg else 1.0), C_ORANGE if was_stg else col))
            game.add_shake(2 if not self.is_boss else 4)
            if self.guard_of is not None and self.guard_of.alive():
                for _ in range(3): game.particles.add(Particle(self.x, self.y, C_MINT, 100))
        if self.stagger >= self.max_stagger:
            self.stagger = 0; self.stg_timer = 2.5
            if game:
                game.stats['staggers'] += 1
                game.add_shake(8)
                game.slowmo_timer = max(game.slowmo_timer, 0.15)
                game.add_float("ACS BREAK!" if self.is_boss else "STAGGER!", self.x, self.y-self.w-34, C_ORANGE, big=True)
                for _ in range(20): game.particles.add(Particle(self.x, self.y, C_WHITE, 250))
        if self.ap <= 0:
            self.kill()
            if game:
                game.combo += 1; game.combo_timer = 2.5
                game.add_shake(10 if self.is_boss else 6)
                for _ in range(40 if self.is_boss else 15):
                    game.particles.add(Particle(self.x, self.y, random.choice([C_ORANGE, C_RED, C_YELLOW]), 320 if self.is_boss else 300))
                if self.is_elite:
                    game.add_float("SQUAD LINK DOWN", self.x, self.y-self.w-34, C_ORANGE, big=True)
                if self.guard_of is not None:
                    game.add_float("GUARD DOWN", self.x, self.y-self.w-34, C_MINT)
                if self.is_target:
                    game.targets_remaining = max(0, game.targets_remaining - 1)
                    game.add_float(f"TARGET DOWN  {game.mission_targets - game.targets_remaining}/{game.mission_targets}", self.x, self.y-self.w-34, C_GOLD, big=True)
                if not self.is_boss:
                    d = math.hypot(self.x-game.player.x, self.y-game.player.y)
                    for _ in range(14): game.particles.add(Particle(self.x, self.y, C_ORANGE, 240))
                    if d < 95:
                        game.hurt(20 if self.is_elite else 15, self.x, self.y)
    def try_dodge(self, bullets):
        if self.mtype == 'rusher': return
        if self.dodge_cd > 0 or self.dodge_timer > 0: return
        for b in bullets:
            if b.owner != 'player': continue
            dx, dy = self.x-b.x, self.y-b.y
            if math.hypot(dx, dy) < 150 and (b.vx*dx + b.vy*dy) > 0:
                perp = (-b.vy, b.vx); m = math.hypot(*perp) or 1
                side = random.choice([-1, 1])
                self.dvx, self.dvy = perp[0]/m*600*side, perp[1]/m*600*side
                self.dodge_timer = 0.16
                self.dodge_cd = 2.0 if self.is_elite else 3.8
                break
    def aim_angle(self, plr, bspd, lead):
        dx, dy = plr.x-self.x, plr.y-self.y
        dist = math.hypot(dx, dy) or 1
        if lead > 0:
            t = dist/bspd
            px = plr.x + getattr(plr,'pvx',0)*t*lead
            py = plr.y + getattr(plr,'pvy',0)*t*lead
            return math.atan2(py-self.y, px-self.x)
        return math.atan2(dy, dx)
    def player_threat(self, plr):
        if plr.qb_timer > 0 or plr.ab_active:
            pdx, pdy = self.x-plr.x, self.y-plr.y
            pd = math.hypot(pdx, pdy) or 1
            if (plr.pvx*pdx + plr.pvy*pdy)/pd > 300:
                return True
        return False
    # ---- Живой щит: перехват ----
    def guard_move(self, plr, game, spd):
        t = self.guard_of
        gdx, gdy = plr.x - t.x, plr.y - t.y
        gd = math.hypot(gdx, gdy) or 1
        gx = t.x + (gdx/gd)*95
        gy = t.y + (gdy/gd)*95
        ddx, ddy = gx - self.x, gy - self.y
        dd = math.hypot(ddx, ddy) or 1
        boost = 1.0
        for b in game.bullets:
            if b.owner != 'player': continue
            bx, by = t.x - b.x, t.y - b.y
            bd = math.hypot(bx, by)
            if 1 < bd < 420:
                bspd = math.hypot(b.vx, b.vy) or 1
                if (b.vx*bx + b.vy*by)/(bd*bspd) > 0.92:
                    boost = 2.4
                    break
        mv = spd*1.3*boost
        if dd > 12:
            self.vx, self.vy = (ddx/dd)*mv, (ddy/dd)*mv
        else:
            self.vx, self.vy = 0, 0
    def target_move(self, plr, game, spd, dist, dx, dy):
        nx, ny = dx/dist, dy/dist
        px, py = -ny, nx
        if dist < 380:
            self.vx, self.vy = -nx*spd*1.15, -ny*spd*1.15
        else:
            wob = math.sin(game.time*1.2 + self.phase)
            self.vx, self.vy = px*spd*0.4*wob, py*spd*0.4*wob
    def boss_decide(self, plr, game, dist):
        if self.boss_en >= 20 and self.boss_qb_cd <= 0 and self.qb_timer <= 0:
            if self.player_threat(plr): return 'DODGE'
            for b in game.bullets:
                if b.owner != 'player': continue
                bdx, bdy = self.x-b.x, self.y-b.y
                if math.hypot(bdx, bdy) < 140 and (b.vx*bdx + b.vy*bdy) > 0:
                    return 'DODGE'
        if plr.stalled and dist > 180 and self.boss_en >= 30:
            return 'PUNISH'
        return 'ENGAGE'
    def boss_move(self, behavior, plr, game, dist, dx, dy, dt):
        nx, ny = dx/dist, dy/dist
        px, py = -ny, nx
        spd = self.spd*(1.28 if self.phase2 else 1)
        if self.qb_timer > 0:
            self.qb_timer -= dt
            if self.dash_dir:
                self.vx, self.vy = self.dash_dir[0]*880, self.dash_dir[1]*880
                self.boss_ghosts.append((self.x, self.y, self.ang, 0.22))
            if self.qb_timer <= 0: self.dash_dir = None
            return
        if self.boss_ab > 0:
            self.boss_ab -= dt
            self.boss_en -= 45*dt
            self.vx, self.vy = nx*700, ny*700
            game.particles.add(Particle(self.x-nx*30, self.y-ny*30, C_ORANGE, 90))
            self.boss_ghosts.append((self.x, self.y, self.ang, 0.15))
            if self.boss_en <= 0: self.boss_ab = 0
            return
        if behavior == 'DODGE':
            if self.boss_qb_cd <= 0 and self.boss_en >= 20:
                side = random.choice([-1, 1])
                self.dash_dir = (px*side, py*side)
                self.qb_timer = 0.22
                self.boss_en -= 20
                self.boss_qb_cd = 2.2
            self.vx, self.vy = 0, 0
        elif behavior == 'PUNISH':
            if self.boss_ab <= 0 and self.boss_en >= 30 and dist > 180:
                self.boss_ab = 0.5
            self.vx, self.vy = nx*spd*1.2, ny*spd*1.2
        elif self.phase2:
            if dist > 150:
                self.vx, self.vy = nx*spd*1.2, ny*spd*1.2
            else:
                self.vx, self.vy = px*spd*0.7*self.boss_orbit, py*spd*0.7*self.boss_orbit
        else:
            if dist < 320: self.vx, self.vy = -nx*spd, -ny*spd
            elif dist > 480: self.vx, self.vy = nx*spd, ny*spd
            else: self.vx, self.vy = px*spd*0.6*self.boss_orbit, py*spd*0.6*self.boss_orbit
    def boss_act(self, behavior, plr, game, dist, bullets, dt):
        if behavior == 'DODGE': return
        if self.boss_burst_left > 0:
            self.boss_burst_t -= dt
            if self.boss_burst_t <= 0:
                self.boss_burst_t = 0.09
                self.boss_burst_left -= 1
                ang = self.aim_angle(plr, 560, 0.5) + random.uniform(-0.03, 0.03)
                bullets.add(Bullet(self.x, self.y, ang, 560, 8, 3, C_RED, 'enemy', 3))
                self.boss_muzzle = 0.05
        if self.phase2:
            if dist < 190 and self.boss_blade_cd <= 0 and self.boss_en >= 30:
                self.boss_blade_cd = 2.0; self.boss_en -= 30
                self.boss_blade_anim = 0.3; self.boss_blade_pending = 0.15
                game.add_shake(4)
            if dist < 220 and self.boss_shotgun_cd <= 0 and self.boss_en >= 15:
                self.boss_shotgun_cd = 2.4; self.boss_en -= 15
                for i in range(5):
                    bullets.add(Bullet(self.x, self.y, self.ang+(i-2)*0.1, 650, 12, 6, C_RED, 'enemy', 4))
                self.boss_muzzle = 0.06
        else:
            if self.boss_burst_cd <= 0 and dist < 600 and self.boss_burst_left <= 0:
                self.boss_burst_cd = 1.5; self.boss_burst_left = 4
            if self.boss_missile_cd <= 0 and self.boss_en >= 15 and dist > 250:
                self.boss_missile_cd = 6.0; self.boss_en -= 15
                for i in range(5):
                    bullets.add(Missile(self.x, self.y, self.ang+random.uniform(-0.6,0.6), [plr], 'enemy'))
    def boss_tick(self, dt, plr, bullets, game):
        for attr in ('hit_flash','boss_qb_cd','boss_blade_cd','boss_missile_cd','boss_burst_cd','boss_shotgun_cd','boss_muzzle','boss_blade_anim'):
            if getattr(self, attr) > 0: setattr(self, attr, getattr(self, attr)-dt)
        if self.spawn_flash > 0: self.spawn_flash -= dt
        self.boss_ghosts = [(x,y,a,t-dt) for x,y,a,t in self.boss_ghosts if t-dt > 0]
        self.boss_orbit_t -= dt
        if self.boss_orbit_t <= 0:
            self.boss_orbit *= -1; self.boss_orbit_t = random.uniform(2, 4)
        if self.qb_timer <= 0 and self.boss_ab <= 0:
            self.boss_en = min(self.boss_en_max, self.boss_en + 18*dt)
        if not self.phase2 and not self.phase2_trigger and self.ap < self.max_ap*0.5:
            self.phase2_trigger = True
            game.slowmo_timer = 2.0
            game.slowmo_text = "VINDICTA: LIMITER RELEASED"
            game.add_shake(12)
            self.ap = min(self.max_ap, self.ap + self.max_ap*0.08)
        if self.phase2_trigger and not self.phase2 and game.slowmo_timer <= 0:
            self.phase2 = True
            game.slowmo_text = ""
            game.add_float("BLADE MODE", self.x, self.y-self.w-40, C_RED, big=True)
        dx, dy = plr.x-self.x, plr.y-self.y
        dist = math.hypot(dx, dy) or 1
        self.ang = math.atan2(dy, dx)
        if self.stg_timer > 0:
            self.stg_timer -= dt
            self.vx = self.vy = 0
            if self.stg_timer <= 0 and self.boss_en >= 20:
                self.qb_timer = 0.25
                self.dash_dir = (-dx/dist, -dy/dist)
                self.boss_en -= 20; self.boss_qb_cd = 2.0
        else:
            behavior = self.boss_decide(plr, game, dist)
            self.boss_mode = behavior
            self.boss_move(behavior, plr, game, dist, dx, dy, dt)
            self.boss_act(behavior, plr, game, dist, bullets, dt)
        if self.boss_blade_pending > 0:
            self.boss_blade_pending -= dt
            if self.boss_blade_pending <= 0:
                if math.hypot(plr.x-self.x, plr.y-self.y) < 185:
                    game.hurt(30, self.x, self.y)
                    game.hitstop = max(game.hitstop, 0.05)
        self.x += self.vx*dt; self.y += self.vy*dt
        self.x = clamp(self.x, 40, MAP_W-40); self.y = clamp(self.y, 40, MAP_H-40)
        self.rect.center = (self.x, self.y)
    def boss_draw(self, surf, cam, scan_mode=False):
        cx, cy = self.x-cam[0], self.y-cam[1]
        s = 1.9
        flash = self.hit_flash > 0 or (self.stg_timer > 0 and int(self.stg_timer*10) % 2)
        p2 = self.phase2
        body_col = (150,150,160) if flash else (95,58,58)
        accent = C_RED if p2 else C_ORANGE
        body = [(-22,-18),(14,-20),(30,0),(14,20),(-22,18)]
        def poly(pts, col, width=0):
            pygame.draw.polygon(surf, col, rot_pts(cx, cy, [(x*s,y*s) for x,y in pts], self.ang), width)
        for gx, gy, ga, gt in self.boss_ghosts:
            a = clamp(gt/0.22, 0, 1)
            pygame.draw.polygon(surf, (int(95*a), int(45*a), int(45*a)), rot_pts(gx-cam[0], gy-cam[1], [(x*s,y*s) for x,y in body], ga))
        if abs(self.vx)+abs(self.vy) > 30 or self.qb_timer > 0 or self.boss_ab > 0:
            for side in (-1,1):
                poly([(-24, side*13), (-34-random.randint(0,8), side*11), (-24, side*9)], accent)
        for side in (-1,1):
            poly([(-20, side*16), (-4, side*16), (-4, side*8), (-20, side*8)], (70,45,45))
        poly(body, body_col); poly(body, (40,25,25), 2)
        for side in (-1,1):
            poly([(-14, side*18), (2, side*18), (2, side*24), (-14, side*24)], (60,40,40))
        poly([(14,-6),(28,0),(14,6)], C_RED if p2 else C_YELLOW)
        if p2:
            blade = [(20,8),(58,2),(60,10),(22,16)]
            poly(blade, C_ORANGE); poly(blade, C_YELLOW, 1)
            if self.boss_blade_anim > 0:
                poly([(0,-34),(70,-70),(78,0),(70,70),(0,34)], C_ORANGE, 3)
        else:
            poly([(16,6),(44,6),(44,12),(16,12)], (80,80,90))
            pygame.draw.line(surf, (60,60,70), rot_pts(cx,cy,[(-18*s,-14*s)],self.ang)[0], rot_pts(cx,cy,[(-2*s,-30*s)],self.ang)[0], 3)
        if self.boss_muzzle > 0:
            gx, gy = rot_pts(cx,cy,[(46*s,9*s)],self.ang)[0]
            pygame.draw.circle(surf, C_YELLOW, (int(gx),int(gy)), random.randint(4,7))
        if self.spawn_flash > 0:
            pygame.draw.circle(surf, C_RED, (int(cx),int(cy)), max(1,int((0.8-self.spawn_flash)*220)), 3)
        if scan_mode:
            pygame.draw.polygon(surf, C_RED, rot_pts(cx,cy,[(x*s*1.15,y*s*1.15) for x,y in body],self.ang), 3)
            if self.stg_timer > 0:
                surf.blit(F_TINY.render("WEAK POINT", True, C_RED), (cx-42, cy-self.w-26))
        if self.boss_en < 20 and int(pygame.time.get_ticks()/200) % 2:
            surf.blit(F_TINY.render("GUARD DOWN", True, C_YELLOW), (cx-44, cy-self.w-42))
        lbl = F_TINY.render(self.boss_mode + (" // BLADE" if p2 else ""), True, C_RED if p2 else C_DIM)
        surf.blit(lbl, (cx-lbl.get_width()//2, cy+self.w+8))
    def elite_decide(self, plr, game, dist):
        if self.stg_timer > 0: return 'IDLE'
        if not self.barrier_active: return 'RETREAT'
        if self.player_threat(plr): return 'EVADE'
        if self.enraged: return 'PRESSURE'
        allies = sum(1 for o in game.enemies if not o.is_boss and not o.is_elite)
        if allies <= 1: return 'RALLY'
        if dist < 170: return 'DISENGAGE'
        if dist > 460: return 'ADVANCE'
        if allies >= 4: return 'SUPPORT'
        return 'FLANK' if self.flank_mode else 'STRAFE'
    def elite_move(self, plr, game, dist, dx, dy, spd):
        b = self.behavior
        nx, ny = dx/dist, dy/dist
        px, py = -ny, nx
        if b == 'IDLE': self.vx = self.vy = 0
        elif b == 'RETREAT':
            wz = math.sin(game.time*6 + self.phase)*0.5
            self.vx = -nx*spd + px*spd*wz; self.vy = -ny*spd + py*spd*wz
        elif b == 'EVADE': self.vx, self.vy = px*spd*1.5*self.flank_side, py*spd*1.5*self.flank_side
        elif b == 'PRESSURE':
            if dist > 160: self.vx, self.vy = nx*spd*1.2, ny*spd*1.2
            else: self.vx, self.vy = px*spd*self.flank_side, py*spd*self.flank_side
        elif b == 'RALLY':
            if dist > 220: self.vx, self.vy = nx*spd*1.1, ny*spd*1.1
            else: self.vx, self.vy = px*spd*self.flank_side, py*spd*self.flank_side
        elif b == 'DISENGAGE': self.vx, self.vy = (-nx*spd, -ny*spd) if dist < 300 else (0,0)
        elif b == 'ADVANCE': self.vx, self.vy = (nx*spd, ny*spd) if dist > 300 else (0,0)
        elif b == 'SUPPORT':
            self.vx, self.vy = px*spd*0.6*self.flank_side, py*spd*0.6*self.flank_side
            if dist > 440: self.vx += nx*spd*0.5; self.vy += ny*spd*0.5
            elif dist < 380: self.vx += -nx*spd*0.5; self.vy += -ny*spd*0.5
        elif b == 'FLANK':
            rear = plr.ang + math.pi + self.flank_side*0.9
            gx, gy = plr.x + math.cos(rear)*300, plr.y + math.sin(rear)*300
            gdx, gdy = gx-self.x, gy-self.y
            gd = math.hypot(gdx, gdy) or 1
            self.vx, self.vy = ((gdx/gd)*spd, (gdy/gd)*spd) if gd > 30 else (0,0)
        else:
            self.vx, self.vy = px*spd*self.flank_side, py*spd*self.flank_side
            if dist > 340: self.vx += nx*spd*0.5; self.vy += ny*spd*0.5
            elif dist < 260: self.vx += -nx*spd*0.5; self.vy += -ny*spd*0.5
    def rusher_decide(self, plr, game, dist):
        if self.stg_timer > 0: return 'IDLE'
        if self.qb_timer > 0: return 'LUNGE'
        if self.recover > 0: return 'RECOVER'
        if dist > 420: return 'CHASE'
        return 'STALK'
    def rusher_move(self, plr, game, dist, dx, dy, spd):
        b = self.behavior
        nx, ny = dx/dist, dy/dist
        px, py = -ny, nx
        frenzy = self.ap < self.max_ap*0.4
        if b == 'IDLE': self.vx = self.vy = 0
        elif b == 'RECOVER': self.vx, self.vy = -nx*spd*0.4, -ny*spd*0.4
        elif b == 'CHASE': self.vx, self.vy = nx*spd*1.2, ny*spd*1.2
        else:
            rad = 170 if frenzy else 210
            gx, gy = plr.x + math.cos(self.hunt_ang)*rad, plr.y + math.sin(self.hunt_ang)*rad
            gdx, gdy = gx-self.x, gy-self.y
            gd = math.hypot(gdx, gdy) or 1
            weave = math.sin(game.time*6 + self.phase)*0.35
            self.vx = (gdx/gd)*spd + px*spd*weave
            self.vy = (gdy/gd)*spd + py*spd*weave
    def rusher_think(self, plr, game, dist):
        if self.lunge_cd > 0 or self.recover > 0: return
        for o in game.enemies:
            if o is not self and o.mtype == 'rusher' and (o.pending_ram or o.qb_timer > 0): return
        frenzy = self.ap < self.max_ap*0.4
        if (plr.stalled or plr.scanning) and dist < 420:
            self.pending_ram = True; self.telegraph = 0.2
        elif frenzy and dist < 300:
            self.pending_ram = True; self.telegraph = 0.3
        elif dist < 320:
            self.pending_ram = True; self.telegraph = 0.35
    def update(self, dt, plr, bullets, game):
        if self.is_boss:
            self.boss_tick(dt, plr, bullets, game); return
        if self.hit_flash > 0: self.hit_flash -= dt
        if self.dodge_cd > 0: self.dodge_cd -= dt
        if self.contact_cd > 0: self.contact_cd -= dt
        if self.recover > 0: self.recover -= dt
        if self.relocate > 0: self.relocate -= dt
        if self.spawn_flash > 0: self.spawn_flash -= dt
        if self.mtype == 'rusher' and self.lunge_cd > 0: self.lunge_cd -= dt
        if self.is_elite:
            self.enraged = self.ap < self.max_ap*0.5
            self.flank_timer -= dt
            if self.flank_timer <= 0:
                self.flank_side *= -1; self.flank_timer = random.uniform(2.5, 5)
            self.flank_mode_timer -= dt
            if self.flank_mode_timer <= 0:
                self.flank_mode = not self.flank_mode; self.flank_mode_timer = random.uniform(5, 9)
            if self.barrier_regen_cd > 0: self.barrier_regen_cd -= dt
            else:
                if not self.barrier_active:
                    self.barrier_active = True; self.barrier = self.barrier_max*0.5
                elif self.barrier < self.barrier_max:
                    self.barrier = min(self.barrier_max, self.barrier + 15*dt)
        if self.burst_timer > 0 and self.stg_timer <= 0:
            self.burst_timer -= dt
            if self.burst_timer <= 0:
                bullets.add(Bullet(self.x, self.y, self.burst_ang, 520, 14, 4, C_RED, 'enemy', 4))
        if self.telegraph > 0 and self.mtype in ('gunner','mortar'):
            self.aim_ang = self.aim_angle(plr, 520 if self.mtype=='gunner' else 210, 0.65 if self.mtype=='gunner' else 0.9)
        if self.stg_timer > 0:
            self.stg_timer -= dt; self.vx = self.vy = 0
        else:
            dx, dy = plr.rect.centerx-self.x, plr.rect.centery-self.y
            dist = math.hypot(dx, dy) or 1
            self.ang = math.atan2(dy, dx)
            spd = self.spd*(1.3 if self.enraged else 1)
            if self.mtype == 'rusher' and self.ap < self.max_ap*0.4: spd *= 1.25
            if self.is_elite: self.behavior = self.elite_decide(plr, game, dist)
            elif self.mtype == 'rusher': self.behavior = self.rusher_decide(plr, game, dist)
            if self.qb_timer > 0:
                self.qb_timer -= dt
                if self.dash_dir and (self.is_elite or self.mtype == 'rusher'):
                    if self.mtype == 'rusher':
                        dspd = 1000 if self.ap < self.max_ap*0.4 else 900
                        game.particles.add(Particle(self.x, self.y, C_MAGENTA, 80))
                    else:
                        dspd = 820
                        game.particles.add(Particle(self.x, self.y, C_ORANGE, 60))
                    self.vx, self.vy = self.dash_dir[0]*dspd, self.dash_dir[1]*dspd
                else:
                    self.vx, self.vy = (dx/dist)*820, (dy/dist)*820
                if self.qb_timer <= 0:
                    self.dash_dir = None
                    if self.mtype == 'rusher':
                        self.recover = 0.18 if self.lunge_hit else 0.35
            elif self.dodge_timer > 0:
                self.dodge_timer -= dt; self.vx, self.vy = self.dvx, self.dvy
            elif self.is_elite:
                self.elite_move(plr, game, dist, dx, dy, spd)
            elif self.mtype == 'rusher':
                self.rusher_move(plr, game, dist, dx, dy, spd)
            else:
                if self.guard_of is not None and not self.guard_of.alive():
                    self.guard_of = None
                if self.is_target:
                    self.target_move(plr, game, spd, dist, dx, dy)
                elif self.guard_of is not None:
                    self.guard_move(plr, game, spd)
                else:
                    gx, gy = plr.x + math.cos(self.slot_ang)*self.pref_dist, plr.y + math.sin(self.slot_ang)*self.pref_dist
                    gdx, gdy = gx-self.x, gy-self.y
                    gd = math.hypot(gdx, gdy) or 1
                    mv = spd*(1.6 if self.relocate > 0 else 1.0)
                    self.vx, self.vy = ((gdx/gd)*mv, (gdy/gd)*mv) if gd > 25 else (0,0)
            if self.telegraph > 0:
                self.telegraph -= dt
                if self.telegraph <= 0:
                    if self.pending_ram:
                        self.pending_ram = False
                        t = dist/900
                        px2 = plr.x + getattr(plr,'pvx',0)*t*0.8
                        py2 = plr.y + getattr(plr,'pvy',0)*t*0.8
                        ddx, ddy = px2-self.x, py2-self.y
                        dd = math.hypot(ddx, ddy) or 1
                        self.dash_dir = (ddx/dd, ddy/dd)
                        self.qb_timer = 0.28
                        self.lunge_cd = 1.3 if self.ap < self.max_ap*0.4 else 2.2
                        self.lunge_hit = False
                    else:
                        self.fire(plr, bullets, game)
            else:
                self.shoot_cd -= dt
                if self.mtype == 'rusher':
                    self.rusher_think(plr, game, dist)
                elif self.shoot_cd <= 0 and dist < 760:
                    can_fire = True
                    if self.is_elite and self.behavior in ('IDLE','RETREAT','EVADE'): can_fire = False
                    shooters = sum(1 for o in game.enemies if not o.is_boss and o.telegraph > 0)
                    if can_fire and shooters < game.fire_cap:
                        self.telegraph = 0.6 if self.mtype in ('gunner','mortar') else (0.5 if self.is_elite else 0.35)
        self.x += self.vx*dt; self.y += self.vy*dt
        self.x = clamp(self.x, 30, MAP_W-30); self.y = clamp(self.y, 30, MAP_H-30)
        self.rect.center = (self.x, self.y)
    def fire(self, plr, bullets, game=None):
        if self.is_elite:
            self.attack_n += 1
            ang = self.aim_angle(plr, 500, 0.45)
            pspeed = math.hypot(getattr(plr,'pvx',0), getattr(plr,'pvy',0))
            dist = math.hypot(plr.x-self.x, plr.y-self.y)
            if pspeed < 130 and dist < 420:
                bullets.add(Bullet(self.x, self.y, ang, 430, 26, 8, C_YELLOW, 'enemy', 7))
                self.shoot_cd = 2.0
            else:
                for i in range(3):
                    bullets.add(Bullet(self.x, self.y, ang+(i-1)*0.08, 500, 14, 4, C_ORANGE, 'enemy', 3))
                self.shoot_cd = 1.3
            if self.enraged: self.shoot_cd *= 0.8
            perp = (-math.sin(self.ang), math.cos(self.ang))
            side = random.choice([-1, 1])
            self.dash_dir = (perp[0]*side, perp[1]*side)
            self.qb_timer = 0.22
        elif self.mtype == 'gunner':
            bullets.add(Bullet(self.x, self.y, self.aim_ang, 540, 15, 4, C_RED, 'enemy', 4))
            self.burst_ang = self.aim_ang; self.burst_timer = 0.14
            self.shoot_cd = 2.4
        elif self.mtype == 'mortar':
            bullets.add(MortarShell(self.x, self.y, self.aim_ang))
            self.shoot_cd = 3.2
        else:
            ang = self.aim_angle(plr, 470, 0.55)
            bullets.add(Bullet(self.x, self.y, ang+random.uniform(-0.04,0.04), 470, 12, 3, C_RED, 'enemy', 3))
            self.shoot_cd = 1.6
        if not self.is_elite and self.mtype != 'rusher':
            self.relocate = random.uniform(0.4, 0.8)
    def draw(self, surf, cam, scan_mode=False):
        if self.is_boss:
            self.boss_draw(surf, cam, scan_mode); return
        cx, cy = self.x-cam[0], self.y-cam[1]
        flash_white = self.stg_timer > 0 and int(self.stg_timer*10) % 2
        if self.is_elite:
            col = C_WHITE if flash_white else C_ORANGE
            body = [(26,0),(10,-15),(-16,-11),(-16,11),(10,15)]
            pygame.draw.polygon(surf, col, rot_pts(cx, cy, body, self.ang))
            pygame.draw.polygon(surf, (120,70,10), rot_pts(cx, cy, body, self.ang), 2)
            for s in (-1,1):
                pygame.draw.line(surf, C_YELLOW, rot_pts(cx,cy,[(12,s*6)],self.ang)[0], rot_pts(cx,cy,[(26,s*16)],self.ang)[0], 2)
            pygame.draw.circle(surf, C_RED if self.enraged else C_YELLOW, (int(cx),int(cy)), 5)
            if self.enraged: pygame.draw.circle(surf, C_RED, (int(cx),int(cy)), self.w+6, 1)
            if self.barrier_active:
                bcol = C_CYAN if self.barrier > self.barrier_max*0.4 else (C_CYAN if int(pygame.time.get_ticks()/120)%2 else (30,80,100))
                pts = [(cx+math.cos(self.ang-1.15+(i/8)*2.3)*(self.w+11), cy+math.sin(self.ang-1.15+(i/8)*2.3)*(self.w+11)) for i in range(9)]
                pygame.draw.lines(surf, bcol, False, pts, 3)
            bw = self.w*2; bx, by = cx-self.w, cy-self.w-16
            pygame.draw.rect(surf, (40,44,55), (bx,by,bw,4))
            pygame.draw.rect(surf, C_RED, (bx,by,bw*clamp(self.ap/self.max_ap,0,1),4))
            pygame.draw.rect(surf, (40,44,55), (bx,by+5,bw,3))
            pygame.draw.rect(surf, C_CYAN, (bx,by+5,bw*clamp(self.barrier/self.barrier_max,0,1),3))
            surf.blit(F_TINY.render("ELITE", True, C_ORANGE), (cx-20, by-16))
            if self.spawn_flash > 0:
                pygame.draw.circle(surf, C_ORANGE, (int(cx),int(cy)), max(1,int((0.6-self.spawn_flash)*180)), 2)
            bcol = {'PRESSURE':C_RED,'RETREAT':C_CYAN,'EVADE':C_YELLOW,'RALLY':C_ORANGE,'FLANK':C_MAGENTA,'SUPPORT':C_BLUE}.get(self.behavior, C_DIM)
            lbl = F_TINY.render(self.behavior, True, bcol if scan_mode else (70,75,85))
            surf.blit(lbl, (cx-lbl.get_width()//2, cy+self.w+6))
        elif self.mtype == 'rusher':
            frenzy = self.ap < self.max_ap*0.4
            col = C_WHITE if flash_white else C_MAGENTA
            sc = 0.7 if self.pending_ram else 1.0
            jx = random.uniform(-2,2) if self.pending_ram else 0
            jy = random.uniform(-2,2) if self.pending_ram else 0
            pygame.draw.polygon(surf, col, rot_pts(cx+jx, cy+jy, [(18*sc,0),(-12*sc,-12*sc),(-6*sc,0),(-12*sc,12*sc)], self.ang))
            if frenzy: pygame.draw.circle(surf, C_RED, (int(cx),int(cy)), self.w+5, 1)
            if self.pending_ram:
                pygame.draw.line(surf, C_MAGENTA, (cx,cy), (cx+math.cos(self.ang)*80, cy+math.sin(self.ang)*80), 2)
            if self.ap < self.max_ap:
                bw = self.w*2; bx, by = cx-self.w, cy-self.w-11
                pygame.draw.rect(surf, (40,44,55), (bx,by,bw,4))
                pygame.draw.rect(surf, C_RED, (bx,by,bw*clamp(self.ap/self.max_ap,0,1),4))
            lbl = F_TINY.render(self.behavior, True, C_MAGENTA if scan_mode else (70,75,85))
            surf.blit(lbl, (cx-lbl.get_width()//2, cy+self.w+6))
        else:
            if self.mtype == 'gunner': base = C_DARKRED
            elif self.mtype == 'mortar': base = (60,160,110)
            else: base = C_RED
            col = C_WHITE if flash_white else base
            if self.mtype == 'gunner':
                pygame.draw.rect(surf, col, (cx-self.w, cy-self.w, self.w*2, self.w*2))
                pygame.draw.line(surf, C_YELLOW, (cx,cy), (cx+math.cos(self.ang)*(self.w+12), cy+math.sin(self.ang)*(self.w+12)), 3)
            elif self.mtype == 'mortar':
                pygame.draw.circle(surf, col, (int(cx),int(cy)), self.w)
                pygame.draw.circle(surf, C_MINT, (int(cx),int(cy)), self.w-6, 2)
            else:
                pygame.draw.rect(surf, col, (cx-self.w, cy-self.w, self.w*2, self.w*2))
                pygame.draw.rect(surf, C_ORANGE, (cx-4, cy-4, 8, 8))
            if self.guard_of is not None and self.guard_of.alive():
                pygame.draw.circle(surf, C_MINT, (int(cx),int(cy)), self.w+4, 1)
            if self.ap < self.max_ap:
                bw = self.w*2; bx, by = cx-self.w, cy-self.w-11
                pygame.draw.rect(surf, (40,44,55), (bx,by,bw,4))
                pygame.draw.rect(surf, C_RED, (bx,by,bw*clamp(self.ap/self.max_ap,0,1),4))
                pygame.draw.rect(surf, (40,44,55), (bx,by+5,bw,3))
                pygame.draw.rect(surf, C_ORANGE, (bx,by+5,bw*clamp(self.stagger/self.max_stagger,0,1),3))
        if self.is_target:
            ty = cy - self.w - 26
            pygame.draw.polygon(surf, C_GOLD, [(cx,ty-8),(cx+7,ty),(cx,ty+8),(cx-7,ty)])
            surf.blit(F_TINY.render("TARGET", True, C_GOLD), (cx-22, ty-22))
        if self.hit_flash > 0 and not self.is_elite and self.mtype != 'rusher':
            pygame.draw.rect(surf, C_WHITE, (cx-self.w, cy-self.w, self.w*2, self.w*2), 3)
        if self.telegraph > 0 and self.mtype in ('gunner','mortar'):
            pygame.draw.line(surf, C_RED if self.mtype=='gunner' else C_MINT, (cx,cy), (cx+math.cos(self.aim_ang)*420, cy+math.sin(self.aim_ang)*420), 1)
        elif self.telegraph > 0 and not self.is_elite and self.mtype != 'rusher':
            pygame.draw.line(surf, C_RED, (cx,cy), (cx+math.cos(self.ang)*70, cy+math.sin(self.ang)*70), 2)
        elif self.telegraph > 0 and self.is_elite:
            pygame.draw.line(surf, C_YELLOW, (cx,cy), (cx+math.cos(self.ang)*90, cy+math.sin(self.ang)*90), 2)
        if scan_mode:
            pygame.draw.rect(surf, C_RED, (cx-self.w-3, cy-self.w-3, self.w*2+6, self.w*2+6), 2)
            if self.stg_timer > 0:
                surf.blit(F_TINY.render("WEAK POINT", True, C_RED), (cx-42, cy-self.w-24))

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, cfg):
        super().__init__()
        self.x, self.y, self.ang = x, y, 0
        self.cfg = cfg
        st = loadout_preview(cfg)
        self.weight = st['weight']
        self.max_ap = st['ap']; self.ap = st['ap']; self.ap_ghost = st['ap']
        self.base_spd = st['spd']
        self.boost_mult = st['boost']
        self.max_en = st['en']; self.en = st['en']; self.en_regen = st['regen']
        r = PARTS['r_arm'][cfg['r_arm']]
        self.rifle_cd_max, self.rifle_dmg, self.rifle_stag = r['cd'], r['dmg'], r['stag']
        self.rifle_encost, self.rifle_knock = r['encost'], r['knock']
        self.rifle_bspd, self.rifle_sz, self.rifle_col = r['bspd'], r['sz'], r['col']
        self.rifle_cd = 0
        self.rail_charge = 0; self.rail_cd = 0
        self.shotgun_cd = self.missile_cd = self.blade_cd = 0
        self.qb_timer = self.qb_cd = 0
        self.ab_active = False; self.i_frames = 0; self.blade_timer = 0
        self.shield_active = False; self.shield_up_at = -99; self.muzzle = 0
        self.missile_ammo = 16
        self.stalled = False; self.stall_timer = 0
        self.scanning = False
        self.pvx = self.pvy = 0
        self.rect = pygame.Rect(x-20, y-20, 40, 40)
        self.ghosts = []
        self.moving = False
    def qb_cost(self):
        base = 15 if self.cfg['legs'] == 'rjoint' else 22
        return base * self.boost_mult
    def take_hit(self, dmg, ang, game):
        if self.shield_active and self.cfg['l_arm'] == 'shield' and not self.stalled:
            diff = abs(ang - self.ang)
            if diff > math.pi: diff = 2*math.pi - diff
            if diff < math.pi/2.2:
                if game and (game.time - self.shield_up_at) < 0.22:
                    game.add_float("PERFECT GUARD", self.x, self.y-50, C_CYAN, big=True)
                    game.add_shake(5)
                    game.hitstop = max(game.hitstop, 0.05)
                    fx = self.x + math.cos(self.ang)*30; fy = self.y + math.sin(self.ang)*30
                    for _ in range(12): game.particles.add(Particle(fx, fy, C_CYAN, 250))
                    tgt, bd = None, 320
                    for e in game.enemies:
                        d = math.hypot(e.x-self.x, e.y-self.y)
                        if d < bd:
                            ae = math.atan2(e.y-self.y, e.x-self.x)
                            df = abs(ae - self.ang)
                            if df > math.pi: df = 2*math.pi - df
                            if df < 1.2:
                                tgt, bd = e, d
                    if tgt: game.apply_stagger(tgt, 55)
                    return False
                self.en = max(0, self.en - dmg*0.4)
                return False
        self.ap -= dmg
        return True
    def fire_larm(self, game):
        if self.stalled: return
        la = self.cfg['l_arm']
        if la == 'shotgun':
            if self.shotgun_cd > 0: return
            self.shotgun_cd = 1.1
            for i in range(6):
                a = self.ang + (i-2.5)*0.12
                game.bullets.add(Bullet(self.x+math.cos(a)*28, self.y+math.sin(a)*28, a, 720, 13, 9, C_RED, 'player', 4, falloff=True))
            self.muzzle = 0.05; game.add_shake(3)
        elif la == 'grenade':
            if self.shotgun_cd > 0: return
            self.shotgun_cd = 1.6
            game.bullets.add(Grenade(self.x+math.cos(self.ang)*28, self.y+math.sin(self.ang)*28, self.ang))
            self.muzzle = 0.05; game.add_shake(3)
    def fire_rail(self, game):
        game.add_shake(8)
        self.muzzle = 0.1
        dx, dy = math.cos(self.ang), math.sin(self.ang)
        game.beams.append({'x1':self.x+dx*30,'y1':self.y+dy*30,'x2':self.x+dx*900,'y2':self.y+dy*900,'life':0.25})
        for e in game.enemies:
            ex, ey = e.x-self.x, e.y-self.y
            proj = ex*dx + ey*dy
            if proj < 0 or proj > 900: continue
            if abs(ex*dy - ey*dx) < e.w + 12:
                e.take_damage(120, 60, game, C_CYAN, bypass=True)
                game.hitstop = max(game.hitstop, 0.05)
        for _ in range(20):
            t = random.random()
            game.particles.add(Particle(self.x+dx*(30+870*t), self.y+dy*(30+870*t), C_CYAN, 120))
    def update(self, dt, keys, mpos, mbtn, cam, game):
        mx, my = mpos[0]+cam[0], mpos[1]+cam[1]
        self.ang = math.atan2(my-self.y, mx-self.x)
        if self.en <= 0 and not self.stalled:
            self.stalled = True; self.stall_timer = 1.6
        if self.stalled:
            self.stall_timer -= dt; self.en = 0
            if self.stall_timer <= 0:
                self.stalled = False; self.en = 30
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1
        if dx or dy:
            m = math.hypot(dx, dy); dx, dy = dx/m, dy/m
        spd = self.base_spd*(0.5 if self.stalled else 1)*(0.75 if self.scanning else 1.0)
        self.moving = False
        if self.qb_timer > 0:
            spd = 1600; self.qb_timer -= dt; self.moving = True
            if self.cfg['legs'] == 'tank': dx, dy = math.cos(self.ang), math.sin(self.ang)
            self.ghosts.append((self.x, self.y, self.ang, 0.28))
        elif self.ab_active and self.en > 0 and not self.stalled and not self.scanning:
            spd = 850; self.en -= 55*self.boost_mult*dt; self.moving = True
            dx, dy = math.cos(self.ang), math.sin(self.ang)
            self.ghosts.append((self.x, self.y, self.ang, 0.15))
        else:
            if not self.stalled: self.en = min(self.max_en, self.en + self.en_regen*dt)
            self.ab_active = False
        if dx or dy: self.moving = True
        oldx, oldy = self.x, self.y
        self.x += dx*spd*dt; self.y += dy*spd*dt
        self.x = clamp(self.x, 20, MAP_W-20); self.y = clamp(self.y, 20, MAP_H-20)
        if dt > 0:
            self.pvx = (self.x-oldx)/dt; self.pvy = (self.y-oldy)/dt
        self.rect.center = (self.x, self.y)
        for attr in ('i_frames','blade_timer','muzzle','rifle_cd','shotgun_cd','missile_cd','blade_cd','qb_cd','rail_cd'):
            v = getattr(self, attr)
            if v > 0: setattr(self, attr, v - dt)
        self.ghosts = [(x,y,a,t-dt) for x,y,a,t in self.ghosts if t-dt > 0]
        self.ap_ghost = lerp(self.ap_ghost, self.ap, 4*dt) if self.ap_ghost > self.ap else self.ap
        was_up = self.shield_active
        self.shield_active = (self.cfg['l_arm'] == 'shield' and mbtn[2] and self.en > 0 and not self.stalled)
        if self.shield_active and not was_up:
            self.shield_up_at = game.time
        if self.shield_active: self.en = max(0, self.en - 40*dt)
        if self.cfg['r_arm'] == 'rail':
            if mbtn[0] and not self.stalled and self.rail_cd <= 0 and self.en >= 35:
                self.rail_charge = min(1.0, self.rail_charge + dt/0.6)
                if self.rail_charge >= 1.0:
                    self.fire_rail(game)
                    self.rail_charge = 0; self.rail_cd = 1.8; self.en -= 35
            else:
                self.rail_charge = max(0, self.rail_charge - dt*2)
        elif mbtn[0] and not self.stalled:
            if self.rifle_cd <= 0 and self.en >= self.rifle_encost:
                self.rifle_cd = self.rifle_cd_max
                self.en -= self.rifle_encost
                gx, gy = self.x+math.cos(self.ang)*32, self.y+math.sin(self.ang)*32
                game.bullets.add(Bullet(gx, gy, self.ang, self.rifle_bspd, self.rifle_dmg, self.rifle_stag, self.rifle_col, 'player', self.rifle_sz))
                self.muzzle = 0.05
                if self.rifle_knock > 0:
                    self.x -= math.cos(self.ang)*self.rifle_knock*dt*8
                    self.y -= math.sin(self.ang)*self.rifle_knock*dt*8
                    game.add_shake(3)
        if keys[pygame.K_q] and self.missile_cd <= 0 and self.en >= 20 and self.missile_ammo >= 4 and not self.stalled:
            self.missile_cd = 2.5; self.en -= 20; self.missile_ammo -= 4
            for i in range(4):
                game.bullets.add(Missile(self.x, self.y, self.ang+(i-1.5)*0.2, game.enemies, 'player'))
        if keys[pygame.K_e] and self.blade_cd <= 0 and self.en >= 45 and not self.stalled:
            self.blade_cd = 1.2; self.en -= 45; self.blade_timer = 0.2
            game.add_shake(5)
            for e in game.enemies:
                if math.hypot(e.x-self.x, e.y-self.y) < 160:
                    a_e = math.atan2(e.y-self.y, e.x-self.x)
                    diff = abs(a_e - self.ang)
                    if diff > math.pi: diff = 2*math.pi - diff
                    if diff < math.pi/2.5:
                        if e.is_boss and e.boss_blade_anim > 0:
                            game.add_float("CLASH!", (self.x+e.x)//2, min(self.y,e.y)-60, C_YELLOW, big=True)
                            game.hitstop = max(game.hitstop, 0.12)
                            game.add_shake(8)
                            e.boss_blade_pending = 0
                            for _ in range(20): game.particles.add(Particle((self.x+e.x)/2, (self.y+e.y)/2, C_YELLOW, 300))
                        e.take_damage(200, 100, game, C_CYAN, bypass=True)
                        game.hitstop = max(game.hitstop, 0.06)
                        for _ in range(15): game.particles.add(Particle(e.x, e.y, C_CYAN, 250))
        if keys[pygame.K_LSHIFT] and self.qb_cd <= 0 and self.en >= self.qb_cost() and not self.stalled and not self.scanning:
            self.qb_cd = 0.6; self.qb_timer = 0.2; self.en -= self.qb_cost(); self.i_frames = 0.25
        self.ab_active = keys[pygame.K_SPACE] and self.en > 0 and not self.stalled and not self.scanning
        if self.ab_active:
            for e in game.enemies:
                if self.rect.colliderect(e.rect):
                    e.take_damage(80*dt, 30*dt, game, C_CYAN, bypass=True)
    def draw(self, surf, cam):
        for x, y, a, t in self.ghosts:
            draw_mech_shape(surf, x-cam[0], y-cam[1], a, self.cfg, 1.0, ghost=True)
        cx, cy = self.x-cam[0], self.y-cam[1]
        if self.i_frames > 0 and int(self.i_frames*20) % 2: return
        draw_mech_shape(surf, cx, cy, self.ang, self.cfg, 1.0, thrust=self.moving, dim=self.stalled)
        if self.muzzle > 0:
            gx, gy = self.x+math.cos(self.ang)*36-cam[0], self.y+math.sin(self.ang)*36-cam[1]
            pygame.draw.circle(surf, C_YELLOW, (int(gx),int(gy)), random.randint(4,7))
        if self.shield_active:
            pygame.draw.polygon(surf, C_CYAN, rot_pts(cx, cy, [(26,-26),(34,-26),(34,26),(26,26)], self.ang), 3)
        if self.blade_timer > 0:
            pygame.draw.polygon(surf, C_CYAN, rot_pts(cx, cy, [(0,-30),(120,-60),(120,60),(0,30)], self.ang), 3)
        if self.stalled:
            surf.blit(F_TINY.render("EN STALL", True, C_RED), (cx-32, cy-40))

class Game:
    def __init__(self):
        self.config = dict(DEFAULT_PARTS)
        self.owned = set(DEFAULT_PARTS.values())
        self.credits = 0
        self.best_rank = {}
        self.rail_unlocked = False
        self.mission_idx = 0
        self.garage_sel = 0
        self.garage_idx = {s: 0 for s in SLOT_ORDER}
        self.buy_flash = 0; self.deny_flash = 0
        self.dust = [(random.randint(0, MAP_W), random.randint(0, MAP_H), random.uniform(0.3, 1.0)) for _ in range(60)]
        self.reset()
    def reset(self):
        m = MISSIONS[self.mission_idx]
        self.player = Player(MAP_W/2, MAP_H/2, self.config)
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.dmg_nums = pygame.sprite.Group()
        self.cam = [self.player.x-W/2, self.player.y-H/2]
        self.scan_mode = False; self.scan_time = SCAN_MAX; self.scan_cd = 0.0
        self.slowmo_timer = 0; self.slowmo_text = ""
        self.damage_flash = 0; self.shake = 0; self.hitstop = 0
        self.wave_idx = -1; self.wave_cleared = False; self.wave_delay = 1.2
        self.boss_spawned = False
        self.m2_spawned = False; self.m2_reinf = 6.0
        self.m2_esc1 = False; self.m2_esc2 = False
        self.guard_timer = 0.0
        self.mission_targets = m['targets']
        self.targets_remaining = m['targets']
        self.beams = []
        self.banner = "WAVE 1 INBOUND" if m['boss'] else "LOCATE PRIORITY TARGETS"
        self.banner_timer = 2.0
        self.stats = {'time':0.0, 'dmg_taken':0, 'staggers':0}
        self.final_rank = None; self.earned = 0
        self.hitmark = 0
        self.combo = 0; self.combo_timer = 0
        self.floats = []; self.dmg_dirs = []
        self.bosscard = 0
        self.show_fps = False; self.show_help = False
        self.time = 0; self.flank_phase = 0
        self.base_fire_cap = 2; self.fire_cap = 2
    def add_shake(self, a): self.shake = min(20, self.shake + a)
    def add_float(self, text, x, y, col, big=False):
        self.floats.append({'t':text,'x':x,'y':y,'col':col,'life':1.0,'big':big})
    def apply_stagger(self, e, amt):
        if e.stg_timer > 0: return
        e.stagger += amt
        if e.stagger >= e.max_stagger:
            e.stagger = 0; e.stg_timer = 2.5
            self.stats['staggers'] += 1
            self.add_float("ACS BREAK!" if e.is_boss else "STAGGER!", e.x, e.y-e.w-34, C_ORANGE, big=True)
            self.add_shake(8)
            self.slowmo_timer = max(self.slowmo_timer, 0.15)
            for _ in range(20): self.particles.add(Particle(e.x, e.y, C_WHITE, 250))
    def hurt(self, dmg, sx, sy):
        if self.player.i_frames > 0: return False
        a = math.atan2(sy-self.player.y, sx-self.player.x)
        hit = self.player.take_hit(dmg, a, self)
        self.dmg_dirs.append((a, 0.7))
        if hit:
            self.damage_flash = 0.3
            self.add_shake(6)
            self.stats['dmg_taken'] += dmg
        else:
            fx = self.player.x + math.cos(self.player.ang)*30
            fy = self.player.y + math.sin(self.player.ang)*30
            for _ in range(6): self.particles.add(Particle(fx, fy, C_CYAN, 180))
        return hit
    def assign_guards(self):
        targets = [e for e in self.enemies if e.is_target]
        escorts = [e for e in self.enemies if not e.is_target and not e.is_elite and not e.is_boss and e.mtype in ('striker','gunner')]
        for e in escorts:
            if e.guard_of is not None and not e.guard_of.alive():
                e.guard_of = None
        for t in targets:
            if any(e.guard_of is t for e in escorts):
                continue
            free = [e for e in escorts if e.guard_of is None]
            if not free: break
            best = min(free, key=lambda e: math.hypot(e.x-t.x, e.y-t.y))
            best.guard_of = t
    def spawn_wave(self, idx):
        w = WAVES[idx]
        for _ in range(w['mt']): self.enemies.add(Enemy(*self.rand_far()))
        for _ in range(w['elite']): self.enemies.add(Enemy(*self.rand_far(), is_elite=True))
        self.base_fire_cap = min(2 + idx, 4)
    def rand_far(self):
        while True:
            x, y = random.randint(150, MAP_W-150), random.randint(150, MAP_H-150)
            if math.hypot(x-self.player.x, y-self.player.y) > 550:
                return x, y
    def finish_victory(self):
        self.compute_rank()
        m = MISSIONS[self.mission_idx]
        mult = {'S':2.0,'A':1.5,'B':1.2,'C':1.0}.get(self.final_rank, 1.0)
        self.earned = int(m['reward']*mult)
        self.credits += self.earned
        prev = self.best_rank.get(self.mission_idx)
        order = ['C','B','A','S']
        if prev is None or order.index(self.final_rank) > order.index(prev):
            self.best_rank[self.mission_idx] = self.final_rank
        if self.mission_idx == 1 and not self.rail_unlocked:
            self.rail_unlocked = True
    def finish_defeat(self):
        self.earned = int(MISSIONS[self.mission_idx]['reward']*0.2)
        self.credits += self.earned
    def update(self, dt, keys, mpos, mbtn):
        self.time += dt
        self.stats['time'] += dt
        m = MISSIONS[self.mission_idx]
        tx, ty = self.player.x-W/2, self.player.y-H/2
        self.cam[0] = lerp(self.cam[0], tx, 8*dt)
        self.cam[1] = lerp(self.cam[1], ty, 8*dt)
        boss_slow = self.slowmo_timer > 0
        if boss_slow: self.slowmo_timer -= dt
        if self.scan_mode:
            self.scan_time -= dt
            self.player.en -= SCAN_DRAIN*dt
            if self.scan_time <= 0 or self.player.en <= 0:
                self.player.en = max(0, self.player.en)
                self.scan_mode = False; self.scan_cd = SCAN_CD
        else:
            if self.scan_cd > 0: self.scan_cd -= dt
        self.player.scanning = self.scan_mode
        enemy_move_dt = dt*(0.25 if boss_slow else 1.0)*(0.5 if self.scan_mode else 1.0)
        ebullet_dt = dt*(0.25 if boss_slow else 1.0)
        num_elites = sum(1 for e in self.enemies if e.is_elite)
        self.fire_cap = self.base_fire_cap + num_elites
        std = [e for e in self.enemies if not e.is_boss and e.mtype != 'rusher' and not e.is_elite and not e.is_target and e.guard_of is None]
        for i, e in enumerate(std):
            e.slot_ang = (i/max(1,len(std)))*2*math.pi + self.flank_phase
        rushers = [e for e in self.enemies if e.mtype == 'rusher']
        for i, r in enumerate(rushers):
            r.hunt_ang = (i/max(1,len(rushers)))*2*math.pi + self.flank_phase*1.6
        self.flank_phase += dt*0.12
        if m['boss']:
            if not self.boss_spawned:
                if len(self.enemies) == 0:
                    if not self.wave_cleared:
                        self.wave_cleared = True; self.wave_delay = 1.6
                        if self.wave_idx >= 0:
                            self.add_float("WAVE CLEARED", self.player.x, self.player.y-70, C_GREEN, big=True)
                            self.player.en = min(self.player.max_en, self.player.en + 30)
                            self.add_float("+30 EN", self.player.x, self.player.y-100, C_BLUE)
                    self.wave_delay -= dt
                    if self.wave_delay <= 0:
                        self.wave_cleared = False
                        if self.wave_idx + 1 < len(WAVES):
                            self.wave_idx += 1
                            self.spawn_wave(self.wave_idx)
                            el = WAVES[self.wave_idx]['elite']
                            self.banner = f"WAVE {self.wave_idx+1} INBOUND" + (" // ELITE COMMANDER DETECTED" if el else "")
                            self.banner_timer = 2.2
                        else:
                            b = Enemy(MAP_W/2+500, MAP_H/2, is_boss=True)
                            b.spawn_flash = 0.8
                            self.enemies.add(b)
                            self.boss_spawned = True
                            self.banner = "WARNING: RIVAL AC DETECTED"
                            self.banner_timer = 3.0
                            self.bosscard = 2.5
                            self.slowmo_timer = max(self.slowmo_timer, 0.6)
                            self.add_shake(8)
                else:
                    self.wave_cleared = False
        else:
            if not self.m2_spawned:
                self.m2_spawned = True
                for _ in range(m['targets']):
                    self.enemies.add(Enemy(*self.rand_far(), is_target=True, force_type='gunner'))
                for _ in range(5):
                    self.enemies.add(Enemy(*self.rand_far()))
            if self.targets_remaining <= 2 and not self.m2_esc1:
                self.m2_esc1 = True
                self.enemies.add(Enemy(*self.rand_far(), is_elite=True))
                for _ in range(2): self.enemies.add(Enemy(*self.rand_far()))
                self.banner = "ELITE COMMANDER RESPONDING"
                self.banner_timer = 2.0
            if self.targets_remaining <= 1 and not self.m2_esc2:
                self.m2_esc2 = True
                for _ in range(3): self.enemies.add(Enemy(*self.rand_far()))
                self.banner = "REINFORCEMENTS INBOUND"
                self.banner_timer = 2.0
            self.m2_reinf -= dt
            escorts = sum(1 for e in self.enemies if not e.is_target)
            if self.m2_reinf <= 0 and escorts < 6 and self.targets_remaining > 0:
                self.m2_reinf = 7.0
                for _ in range(2): self.enemies.add(Enemy(*self.rand_far()))
        # Назначение телохранителей
        self.guard_timer -= dt
        if self.guard_timer <= 0:
            self.guard_timer = 0.5
            if m['targets'] > 0:
                self.assign_guards()
        if self.banner_timer > 0: self.banner_timer -= dt
        if self.bosscard > 0: self.bosscard -= dt
        if self.hitmark > 0: self.hitmark -= dt
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0: self.combo = 0
        for f in self.floats:
            f['life'] -= dt; f['y'] -= 40*dt
        self.floats = [f for f in self.floats if f['life'] > 0]
        self.dmg_dirs = [(a, l-dt) for a, l in self.dmg_dirs if l-dt > 0]
        for bm in self.beams: bm['life'] -= dt
        self.beams = [bm for bm in self.beams if bm['life'] > 0]
        self.player.update(dt, keys, mpos, mbtn, self.cam, self)
        for e in self.enemies:
            if e.is_elite or (e.mtype in ('striker','gunner','mortar') and e.guard_of is None):
                e.try_dodge(self.bullets)
        self.enemies.update(enemy_move_dt, self.player, self.bullets, self)
        boss = next((e for e in self.enemies if e.is_boss), None)
        if boss and boss.boss_ab > 0 and boss.rect.colliderect(self.player.rect):
            self.hurt(25, boss.x, boss.y)
        for e in self.enemies:
            if e.mtype == 'rusher' and not e.is_boss and e.qb_timer > 0 and e.contact_cd <= 0:
                if e.rect.colliderect(self.player.rect):
                    self.hurt(20, e.x, e.y)
                    e.contact_cd = 0.5; e.lunge_hit = True
        for b in list(self.bullets):
            b.update(dt if b.owner == 'player' else ebullet_dt)
        for b in list(self.bullets):
            if isinstance(b, MortarShell):
                d = math.hypot(b.x-self.player.x, b.y-self.player.y)
                if b.fuse <= 0 or d < 30:
                    for _ in range(18): self.particles.add(Particle(b.x, b.y, C_MINT, 260))
                    self.add_shake(5)
                    if d < 110: self.hurt(24, b.x, b.y)
                    b.kill()
            elif isinstance(b, Grenade):
                near = any(math.hypot(e.x-b.x, e.y-b.y) < e.w+20 for e in self.enemies)
                if b.fuse <= 0 or near:
                    for e in self.enemies:
                        if math.hypot(e.x-b.x, e.y-b.y) < 120:
                            e.take_damage(45, 30, self, C_ORANGE)
                    for _ in range(20): self.particles.add(Particle(b.x, b.y, C_ORANGE, 280))
                    self.add_shake(6)
                    b.kill()
        self.particles.update(dt)
        self.dmg_nums.update(dt)
        for b in list(self.bullets):
            if b.owner == 'player':
                for e in self.enemies:
                    if b.rect.colliderect(e.rect):
                        mult = clamp(1.0 - b.dist/380, 0.3, 1.0) if b.falloff else 1.0
                        e.take_damage(b.dmg*mult, b.stag, self, b.col)
                        self.hitmark = 0.1
                        for _ in range(5): self.particles.add(Particle(b.x, b.y, b.col))
                        if isinstance(b, Missile):
                            self.hitstop = max(self.hitstop, 0.04)
                            for _ in range(12): self.particles.add(Particle(b.x, b.y, C_ORANGE, 250))
                        b.kill(); break
            elif b.owner == 'enemy' and not isinstance(b, MortarShell):
                if b.rect.colliderect(self.player.rect):
                    if self.hurt(b.dmg, b.x, b.y):
                        for _ in range(5): self.particles.add(Particle(b.x, b.y, C_RED))
                    b.kill()
        if self.damage_flash > 0: self.damage_flash -= dt
        if self.shake > 0: self.shake = max(0, self.shake - 40*dt)
        if self.player.ap <= 0:
            self.finish_defeat()
            return 'GAME_OVER'
        if m['boss']:
            if self.boss_spawned and not any(e.is_boss for e in self.enemies):
                self.finish_victory(); return 'VICTORY'
        else:
            if self.m2_spawned and self.targets_remaining == 0:
                self.finish_victory(); return 'VICTORY'
        return 'PLAYING'
    def compute_rank(self):
        score = 10000 - self.stats['time']*60 - self.stats['dmg_taken']*12 + self.stats['staggers']*600
        self.final_rank = 'S' if score >= 7500 else 'A' if score >= 5500 else 'B' if score >= 3500 else 'C'
    def draw(self, surf):
        sx = random.uniform(-self.shake, self.shake) if self.shake else 0
        sy = random.uniform(-self.shake, self.shake) if self.shake else 0
        cam = [self.cam[0]+sx, self.cam[1]+sy]
        m = MISSIONS[self.mission_idx]
        surf.fill(C_BG)
        for step, par, col in ((200,0.5,(18,20,28)),(100,1.0,C_GRID)):
            ox = (-cam[0]*par) % step; oy = (-cam[1]*par) % step
            for x in range(int(ox), W, step): pygame.draw.line(surf, col, (x,0),(x,H))
            for y in range(int(oy), H, step): pygame.draw.line(surf, col, (0,y),(W,y))
        for dx, dy, sp in self.dust:
            pygame.draw.circle(surf, (60,70,90), (int((dx-cam[0]*sp)%W), int((dy-cam[1]*sp)%H)), 1)
        pygame.draw.rect(surf, C_RED, (-cam[0], -cam[1], MAP_W, MAP_H), 4)
        # Линии связи телохранителей
        ov = pygame.Surface((W,H), pygame.SRCALPHA)
        drew_link = False
        for e in self.enemies:
            g = getattr(e, 'guard_of', None)
            if g is not None and g.alive():
                ex, ey = e.x-cam[0], e.y-cam[1]
                gx2, gy2 = g.x-cam[0], g.y-cam[1]
                pygame.draw.line(ov, (120,255,180,55), (ex,ey),(gx2,gy2), 1)
                pygame.draw.circle(ov, (120,255,180,110), (int(gx2),int(gy2)), g.w+8, 2)
                drew_link = True
        elites = [e for e in self.enemies if e.is_elite]
        for el in elites:
            ex, ey = el.x-cam[0], el.y-cam[1]
            pygame.draw.circle(ov, (255,140,0,70), (int(ex),int(ey)), el.w+14+int(3*math.sin(pygame.time.get_ticks()/200)), 2)
            for o in self.enemies:
                if o is el or o.is_elite or o.is_boss: continue
                if math.hypot(o.x-el.x, o.y-el.y) < 450:
                    pygame.draw.line(ov, (255,140,0,45), (ex,ey), (o.x-cam[0],o.y-cam[1]), 1)
            drew_link = True
        if drew_link: surf.blit(ov, (0,0))
        for p in self.particles: p.draw(surf, cam)
        for b in self.bullets: b.draw(surf, cam)
        for bm in self.beams:
            a = clamp(bm['life']/0.25, 0, 1)
            pygame.draw.line(surf, C_CYAN, (bm['x1']-cam[0],bm['y1']-cam[1]), (bm['x2']-cam[0],bm['y2']-cam[1]), int(6*a)+1)
            pygame.draw.line(surf, C_WHITE, (bm['x1']-cam[0],bm['y1']-cam[1]), (bm['x2']-cam[0],bm['y2']-cam[1]), max(1,int(2*a)))
        for e in self.enemies: e.draw(surf, cam, self.scan_mode)
        self.player.draw(surf, cam)
        for d in self.dmg_nums: d.draw(surf, cam)
        for f in self.floats:
            fnt = F_MED if f['big'] else F_TINY
            txt = fnt.render(f['t'], True, f['col'])
            txt.set_alpha(clamp(int(255*f['life']), 0, 255))
            surf.blit(txt, (f['x']-cam[0]-txt.get_width()//2, f['y']-cam[1]))
        if self.dmg_dirs:
            ov = pygame.Surface((W,H), pygame.SRCALPHA)
            pcx, pcy = self.player.x-cam[0], self.player.y-cam[1]
            for a, l in self.dmg_dirs:
                al = int(200*clamp(l/0.7, 0, 1))
                x1, y1 = pcx+math.cos(a)*45, pcy+math.sin(a)*45
                x2, y2 = pcx+math.cos(a)*62, pcy+math.sin(a)*62
                pygame.draw.line(ov, (255,50,50,al), (x1,y1),(x2,y2), 3)
                pygame.draw.polygon(ov, (255,50,50,al), [(pcx+math.cos(a)*72,pcy+math.sin(a)*72),(pcx+math.cos(a+0.4)*60,pcy+math.sin(a+0.4)*60),(pcx+math.cos(a-0.4)*60,pcy+math.sin(a-0.4)*60)])
            surf.blit(ov, (0,0))
        nearest, nd = None, 9999
        for e in self.enemies:
            d = math.hypot(e.x-self.player.x, e.y-self.player.y)
            if d < nd: nd, nearest = d, e
        if nearest:
            ex, ey = nearest.x-cam[0], nearest.y-cam[1]
            r = nearest.w + 12 + int(3*math.sin(pygame.time.get_ticks()/200))
            for qx, qy in ((-1,-1),(1,-1),(-1,1),(1,1)):
                pygame.draw.line(surf, C_GOLD if nearest.is_target else C_YELLOW, (ex+qx*r,ey+qy*r),(ex+qx*r-qx*8,ey+qy*r), 2)
                pygame.draw.line(surf, C_GOLD if nearest.is_target else C_YELLOW, (ex+qx*r,ey+qy*r),(ex+qx*r,ey+qy*r-qy*8), 2)
        if self.scan_mode:
            ov = pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,120,200,45))
            surf.blit(ov, (0,0))
            sweep = (pygame.time.get_ticks()/8) % (W+200) - 100
            pygame.draw.line(surf, C_CYAN, (sweep,0),(sweep,H), 2)
            surf.blit(F_SM.render("SCAN MODE // RECON ONLY", True, C_CYAN), (40, 90))
        if self.damage_flash > 0:
            fr = pygame.Surface((W,H), pygame.SRCALPHA)
            pygame.draw.rect(fr, (255,0,0,int(180*(self.damage_flash/0.3))), (0,0,W,H), 40)
            surf.blit(fr, (0,0))
        if self.player.ap/self.player.max_ap < 0.25:
            pulse = (math.sin(pygame.time.get_ticks()/150)+1)/2
            fr = pygame.Surface((W,H), pygame.SRCALPHA)
            pygame.draw.rect(fr, (255,0,0,int(60*pulse)), (0,0,W,H), 50)
            surf.blit(fr, (0,0))
        if self.slowmo_timer > 0 and self.slowmo_text:
            txt = F_MED.render(self.slowmo_text, True, C_YELLOW)
            surf.blit(txt, (W//2-txt.get_width()//2, H//2-120))
        if self.banner_timer > 0:
            txt = F_BIG.render(self.banner, True, C_RED if "WARNING" in self.banner else C_YELLOW)
            txt.set_alpha(int(255*clamp(self.banner_timer/0.5, 0, 1)))
            surf.blit(txt, (W//2-txt.get_width()//2, 140))
        if self.bosscard > 0:
            a = clamp(self.bosscard/0.6, 0, 1)
            cy0 = H//2 - 40
            ln = int(300*a)
            pygame.draw.line(surf, C_RED, (W//2-ln, cy0-40),(W//2+ln, cy0-40), 2)
            pygame.draw.line(surf, C_RED, (W//2-ln, cy0+60),(W//2+ln, cy0+60), 2)
            t1 = F_BIG.render("VINDICTA", True, C_YELLOW); t1.set_alpha(int(255*a))
            t2 = F_SM.render("HEAVY CAVALRY // ACE PILOT", True, C_RED); t2.set_alpha(int(255*a))
            surf.blit(t1, (W//2-t1.get_width()//2, cy0-30))
            surf.blit(t2, (W//2-t2.get_width()//2, cy0+30))
        pygame.draw.rect(surf, (15,17,24), (20,20,250,92))
        pygame.draw.rect(surf, C_CYAN, (20,20,3,92))
        surf.blit(F_TINY.render(m['code'] + " // " + m['name'], True, C_CYAN), (32, 26))
        surf.blit(F_SM.render("OBJ: " + ("DEFEAT RIVAL AC 'VINDICTA'" if (m['boss'] and self.boss_spawned) else m['obj'][:34]), True, C_WHITE), (32, 46))
        if m['targets'] > 0:
            guarded = sum(1 for e in self.enemies if e.is_target and any(o.guard_of is e for o in self.enemies))
            surf.blit(F_TINY.render(f"TARGETS: {self.mission_targets - self.targets_remaining}/{self.mission_targets}   GUARDED: {guarded}   HOSTILES: {len(self.enemies)}", True, C_GOLD), (32, 72))
        else:
            surf.blit(F_TINY.render(f"HOSTILES: {len(self.enemies)}", True, C_YELLOW), (32, 72))
        if m['boss'] and not self.boss_spawned:
            surf.blit(F_TINY.render(f"WAVE {self.wave_idx+1}/{len(WAVES)}", True, C_DIM), (140, 72))
            if len(self.enemies) == 0 and self.wave_idx + 1 < len(WAVES):
                if int(pygame.time.get_ticks()/300) % 2:
                    nxt = WAVES[self.wave_idx+1]
                    surf.blit(F_TINY.render(f"INCOMING: {nxt['mt']}x MT  {nxt['elite']}x ELITE", True, C_ORANGE), (32, 92))
        if self.combo >= 2:
            fnt = F_BIG if self.combo_timer > 2.1 else F_MED
            txt = fnt.render(f"x{self.combo} CHAIN", True, C_ORANGE)
            surf.blit(txt, (W//2-txt.get_width()//2, 100))
        pygame.draw.rect(surf, (35,38,48), (20,H-45,304,24))
        pygame.draw.rect(surf, (255,120,120), (22,H-43,300*clamp(self.player.ap_ghost/self.player.max_ap,0,1),20))
        pygame.draw.rect(surf, C_GREEN, (22,H-43,300*clamp(self.player.ap/self.player.max_ap,0,1),20))
        surf.blit(F_SM.render("AP", True, C_WHITE), (25, H-70))
        pygame.draw.rect(surf, (35,38,48), (W-324,H-45,304,24))
        low_en = self.player.en < 25
        en_col = (255,80,80) if self.player.stalled else ((255,140,60) if low_en and int(pygame.time.get_ticks()/250)%2 else C_BLUE)
        pygame.draw.rect(surf, en_col, (W-322,H-43,300*(self.player.en/self.player.max_en),20))
        surf.blit(F_SM.render("EN", True, C_WHITE), (W-315, H-70))
        if low_en and int(pygame.time.get_ticks()/300) % 2:
            surf.blit(F_TINY.render("LOW ENERGY", True, C_RED), (W-120, H-70))
        if self.scan_mode:
            slabel, scol, sfrac = "SCAN ACTIVE", C_CYAN, self.scan_time/SCAN_MAX
        elif self.scan_cd > 0:
            slabel, scol, sfrac = "SCAN RECHARGING", C_RED, 1 - self.scan_cd/SCAN_CD
        else:
            slabel, scol, sfrac = "SCAN READY [C]", C_GREEN, 1.0
        surf.blit(F_TINY.render(slabel, True, scol), (W-160, 152))
        pygame.draw.rect(surf, (40,44,55), (W-160,172,120,6))
        pygame.draw.rect(surf, scol, (W-160,172,120*clamp(sfrac,0,1),6))
        boss = next((e for e in self.enemies if e.is_boss), None)
        if boss:
            bw = 500
            pygame.draw.rect(surf, (35,38,48), (W//2-bw//2-2,18,bw+4,18))
            pygame.draw.rect(surf, C_RED, (W//2-bw//2,20,bw*clamp(boss.ap/boss.max_ap,0,1),14))
            pygame.draw.rect(surf, (35,38,48), (W//2-bw//2-2,40,bw+4,8))
            pygame.draw.rect(surf, C_ORANGE, (W//2-bw//2,41,bw*clamp(boss.stagger/boss.max_stagger,0,1),6))
            pygame.draw.rect(surf, (35,38,48), (W//2-bw//2-2,51,bw+4,6))
            ben_col = (255,80,80) if boss.boss_en < 20 and int(pygame.time.get_ticks()/200)%2 else C_BLUE
            pygame.draw.rect(surf, ben_col, (W//2-bw//2,52,bw*clamp(boss.boss_en/boss.boss_en_max,0,1),4))
            surf.blit(F_SM.render("VINDICTA // BLADE MODE" if boss.phase2 else "VINDICTA // HEAVY CAVALRY", True, C_YELLOW), (W//2-bw//2, 60))
        p = self.player
        msl_rdy = p.missile_cd <= 0 and p.missile_ammo >= 4 and p.en >= 20
        bld_rdy = p.blade_cd <= 0 and p.en >= 45
        tokens = [
            ("R:"+PARTS['r_arm'][p.cfg['r_arm']]['n'].split()[0], C_WHITE),
            ("L:"+PARTS['l_arm'][p.cfg['l_arm']]['n'].split()[0], C_WHITE),
            ("LEGS:"+PARTS['legs'][p.cfg['legs']]['n'].split('-')[0], C_WHITE),
            (f"MSL:{p.missile_ammo}", C_GREEN if msl_rdy else C_DIM),
            ("BLADE:"+f"{max(0,p.blade_cd):.1f}", C_GREEN if bld_rdy else C_DIM),
        ]
        x = W//2 - 330
        for txt, col in tokens:
            s = F_SM.render(txt, True, col)
            surf.blit(s, (x, H-80))
            x += s.get_width() + 20
        rx, ry, rr = W-80, 80, 60
        pygame.draw.circle(surf, (15,40,25), (rx,ry), rr, 2)
        pygame.draw.circle(surf, C_BLUE, (rx,ry), 3)
        for e in self.enemies:
            dx, dy = e.x-self.player.x, e.y-self.player.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                scale = min(dist,1200)/1200*rr
                ang = math.atan2(dy, dx)
                if e.is_boss: col = C_YELLOW
                elif e.is_target: col = C_GOLD
                elif e.is_elite: col = C_ORANGE
                elif e.mtype == 'rusher': col = C_MAGENTA
                elif e.mtype == 'mortar': col = C_MINT
                else: col = C_RED
                pygame.draw.circle(surf, col, (int(rx+math.cos(ang)*scale), int(ry+math.sin(ang)*scale)), 4 if e.is_boss else (3 if (e.is_elite or e.is_target) else 2))
        if self.show_fps:
            surf.blit(F_TINY.render(f"{clock.get_fps():.0f} FPS", True, C_GREEN), (W-70, 200))
        surf.blit(F_TINY.render(VERSION, True, C_DIM), (W-140, H-20))
        surf.blit(VIG, (0,0)); surf.blit(SCANLINES, (0,0))
    def draw_help(self, surf):
        ov = pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,0,0,160))
        surf.blit(ov, (0,0))
        surf.blit(F_MED.render("CONTROLS", True, C_CYAN), (W//2-90, 120))
        lines = [
            "WASD ............ MOVE", "MOUSE ........... AIM",
            "LMB ............. R-ARM FIRE / CHARGE RAIL", "RMB ............. L-ARM (shotgun/grenade/shield)",
            "Q ............... MISSILES (4)", "E ............... ENERGY BLADE (clashes!)",
            "SHIFT ........... QUICK BOOST (i-frames)", "SPACE ........... ASSAULT BOOST (ram)",
            "C / TAB ......... SCAN MODE", "RMB (late) ...... PERFECT GUARD w/ shield",
            "ESC ............. PAUSE", "R ............... QUICK RESTART",
            "H ............... TOGGLE HELP", "F3 .............. FPS",
        ]
        for i, ln in enumerate(lines):
            surf.blit(F_SM.render(ln, True, C_WHITE), (W//2-260, 175 + i*32))

def draw_garage(surf, game, t):
    surf.fill(C_BG)
    off = (t*20) % 100
    for x in range(int(-off), W, 100): pygame.draw.line(surf, C_GRID, (x,0),(x,H))
    for y in range(0, H, 100): pygame.draw.line(surf, C_GRID, (0,y),(W,y))
    surf.blit(F_BIG.render("GARAGE", True, C_WHITE), (60, 40))
    surf.blit(F_SM.render("AC-2D // LOADOUT   " + VERSION, True, C_BLUE), (64, 120))
    cr = F_MED.render(f"{game.credits} CR", True, C_GOLD)
    surf.blit(cr, (W-60-cr.get_width(), 50))
    surf.blit(F_TINY.render("CREDITS", True, C_DIM), (W-60-F_TINY.render("CREDITS",True,C_DIM).get_width(), 90))
    px, py = 300, 400
    pygame.draw.circle(surf, (20,40,60), (px, py+90), 70)
    pygame.draw.circle(surf, C_BLUE, (px, py+90), 70, 2)
    draw_mech_shape(surf, px, py+math.sin(t*2)*6, -math.pi/2, game.config, 3.0, thrust=True)
    slot = SLOT_ORDER[game.garage_sel]
    parts = list(PARTS[slot].keys())
    preview_cfg = dict(game.config)
    preview_cfg[slot] = parts[game.garage_idx[slot]]
    st = loadout_preview(preview_cfg)
    stats = [('AP', st['ap']/600), ('SPEED', st['spd']/420), ('EN', st['en']/160),
             ('REGEN', st['regen']/45), ('WEIGHT', 1 - st['weight']/320)]
    sy = 520
    surf.blit(F_SM.render("UNIT STATS", True, C_BLUE), (180, sy))
    for j, (k, v) in enumerate(stats):
        yy = sy + 35 + j*28
        surf.blit(F_TINY.render(k, True, C_WHITE), (180, yy))
        pygame.draw.rect(surf, (40,44,55), (270, yy+2, 180, 12))
        pygame.draw.rect(surf, C_CYAN, (270, yy+2, 180*clamp(v,0,1), 12))
    bx = 560
    surf.blit(F_SM.render("PARTS  (LEFT/RIGHT browse, ENTER buy/equip)", True, C_BLUE), (bx, 160))
    for i, sl in enumerate(SLOT_ORDER):
        active = (i == game.garage_sel)
        plist = list(PARTS[sl].keys())
        cpid = plist[game.garage_idx[sl]]
        p = PARTS[sl][cpid]
        locked = p.get('unlock') and not game.rail_unlocked
        owned = cpid in game.owned
        equipped = game.config[sl] == cpid
        y = 210 + i*95
        col = C_YELLOW if active else C_WHITE
        marker = ">>" if active else "  "
        pulse = int(4*math.sin(t*6)) if active else 0
        surf.blit(F_TINY.render(SLOT_LABEL[sl], True, C_DIM), (bx+pulse, y))
        surf.blit(F_MED.render(f"{marker} {p['n']}", True, C_DIM if locked else col), (bx+pulse, y+18))
        surf.blit(F_TINY.render(p['desc'] + f"   [{p['w']}kg]", True, (140,150,170)), (bx+40, y+52))
        if locked:
            surf.blit(F_TINY.render("LOCKED - complete MISSION 02", True, C_RED), (bx+400, y+22))
        elif not owned:
            afford = game.credits >= p['cost']
            surf.blit(F_TINY.render(f"ENTER: BUY  {p['cost']} CR", True, C_GREEN if afford else C_RED), (bx+400, y+22))
        elif equipped:
            surf.blit(F_TINY.render("EQUIPPED", True, C_GREEN), (bx+400, y+22))
        else:
            surf.blit(F_TINY.render("OWNED - ENTER to equip", True, C_DIM), (bx+400, y+22))
    if game.buy_flash > 0:
        surf.blit(F_MED.render("PURCHASED", True, C_GREEN), (bx+200, 620))
    if game.deny_flash > 0:
        surf.blit(F_MED.render("INSUFFICIENT CREDITS", True, C_RED), (bx+150, 620))
    surf.blit(F_SM.render("UP/DOWN slot   M: SELECT MISSION & DEPLOY", True, C_BLUE), (W//2-320, H-50))
    surf.blit(VIG, (0,0)); surf.blit(SCANLINES, (0,0))

def draw_missions(surf, game, sel, t):
    surf.fill(C_BG)
    off = (t*25) % 100
    for x in range(int(-off), W, 100): pygame.draw.line(surf, C_GRID, (x,0),(x,H))
    surf.blit(F_BIG.render("MISSION SELECT", True, C_WHITE), (W//2-330, 60))
    for i, m in enumerate(MISSIONS):
        locked = (i == 1 and game.best_rank.get(0) is None)
        active = (i == sel)
        y = 200 + i*210
        col = C_YELLOW if active else (C_DIM if locked else C_WHITE)
        pygame.draw.rect(surf, (18,20,28), (W//2-420, y, 840, 170))
        pygame.draw.rect(surf, col, (W//2-420, y, 840, 170), 3 if active else 1)
        surf.blit(F_MED.render(m['code'] + "  " + m['name'], True, col), (W//2-390, y+20))
        surf.blit(F_SM.render(m['obj'], True, (160,170,190) if not locked else C_DIM), (W//2-390, y+65))
        surf.blit(F_TINY.render(f"REWARD: {m['reward']} CR (rank bonus x2.0 S)", True, C_GOLD if not locked else C_DIM), (W//2-390, y+105))
        best = game.best_rank.get(i)
        if best:
            surf.blit(F_TINY.render(f"BEST RANK: {best}", True, C_CYAN), (W//2-390, y+130))
        if locked:
            surf.blit(F_MED.render("LOCKED - complete MISSION 01", True, C_RED), (W//2+60, y+60))
        elif active:
            surf.blit(F_TINY.render(">> ENTER: BRIEFING", True, C_YELLOW), (W//2+220, y+130))
    surf.blit(F_SM.render("UP/DOWN select   ENTER briefing   ESC garage", True, C_BLUE), (W//2-320, H-50))
    surf.blit(VIG, (0,0)); surf.blit(SCANLINES, (0,0))

def draw_briefing(surf, game, t):
    surf.fill(C_BG)
    m = MISSIONS[game.mission_idx]
    pygame.draw.line(surf, C_CYAN, (80, 120), (W-80, 120), 2)
    surf.blit(F_TINY.render("INCOMING TRANSMISSION // OPERATOR", True, C_CYAN), (80, 80))
    surf.blit(F_BIG.render(m['name'], True, C_WHITE), (80, 150))
    surf.blit(F_SM.render(m['code'], True, C_DIM), (80, 240))
    for i, ln in enumerate(m['brief']):
        if t > i*0.5:
            surf.blit(F_SM.render("> " + ln, True, C_WHITE), (100, 300 + i*45))
    pygame.draw.line(surf, C_CYAN, (80, 540), (W-80, 540), 1)
    surf.blit(F_SM.render("OBJECTIVE: " + m['obj'], True, C_GOLD), (80, 555))
    surf.blit(F_SM.render(f"REWARD: {m['reward']} CR  +  RANK BONUS", True, C_GOLD), (80, 590))
    if int(t*2) % 2:
        surf.blit(F_MED.render("ENTER TO DEPLOY", True, C_YELLOW), (W//2-160, 640))
    surf.blit(VIG, (0,0)); surf.blit(SCANLINES, (0,0))

def draw_pause(surf, sel):
    ov = pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,0,0,170))
    surf.blit(ov, (0,0))
    surf.blit(F_BIG.render("PAUSED", True, C_WHITE), (W//2-160, 140))
    items = ["RESUME", "RESTART MISSION", "RETURN TO GARAGE"]
    for i, it in enumerate(items):
        col = C_YELLOW if i == sel else C_WHITE
        surf.blit(F_MED.render((">> " if i == sel else "   ") + it, True, col), (W//2-200, 280+i*70))
    surf.blit(F_TINY.render("ESC resume   R restart   H help", True, C_DIM), (W//2-180, 520))

def main():
    state = 'START'
    game = Game()
    pause_sel = 0
    mission_sel = 0
    brief_t = 0.0
    running = True
    gt = 0.0
    while running:
        dt = clock.tick(60) / 1000.0
        gt += dt
        if game.buy_flash > 0: game.buy_flash -= dt
        if game.deny_flash > 0: game.deny_flash -= dt
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_btn = pygame.mouse.get_pressed()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if _WIN_EVENT is not None and e.type == _WIN_EVENT and getattr(e,'event',None) == _WIN_FOCUS_LOST and state == 'PLAYING':
                state = 'PAUSED'; pause_sel = 0
            elif _ACTIVE_EVENT is not None and e.type == _ACTIVE_EVENT and getattr(e,'gain',1) == 0 and state == 'PLAYING':
                state = 'PAUSED'; pause_sel = 0
            if e.type == pygame.KEYDOWN:
                if state == 'START' and e.key == pygame.K_SPACE:
                    state = 'GARAGE'
                elif state == 'GARAGE':
                    slot = SLOT_ORDER[game.garage_sel]
                    parts = list(PARTS[slot].keys())
                    if e.key == pygame.K_UP: game.garage_sel = (game.garage_sel-1) % 4
                    elif e.key == pygame.K_DOWN: game.garage_sel = (game.garage_sel+1) % 4
                    elif e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        ni = (game.garage_idx[slot] + (1 if e.key == pygame.K_RIGHT else -1)) % len(parts)
                        game.garage_idx[slot] = ni
                        npid = parts[ni]
                        np = PARTS[slot][npid]
                        if npid in game.owned and not (np.get('unlock') and not game.rail_unlocked):
                            game.config[slot] = npid
                    elif e.key == pygame.K_RETURN:
                        pid = parts[game.garage_idx[slot]]
                        p = PARTS[slot][pid]
                        locked = p.get('unlock') and not game.rail_unlocked
                        if pid not in game.owned and not locked:
                            if game.credits >= p['cost']:
                                game.credits -= p['cost']
                                game.owned.add(pid)
                                game.config[slot] = pid
                                game.buy_flash = 1.0
                            else:
                                game.deny_flash = 1.0
                        elif pid in game.owned:
                            game.config[slot] = pid
                    elif e.key == pygame.K_m:
                        state = 'MISSIONS'; mission_sel = 0
                elif state == 'MISSIONS':
                    if e.key == pygame.K_UP: mission_sel = (mission_sel-1) % 2
                    elif e.key == pygame.K_DOWN: mission_sel = (mission_sel+1) % 2
                    elif e.key == pygame.K_ESCAPE: state = 'GARAGE'
                    elif e.key == pygame.K_RETURN:
                        if not (mission_sel == 1 and game.best_rank.get(0) is None):
                            game.mission_idx = mission_sel
                            state = 'BRIEFING'; brief_t = 0.0
                elif state == 'BRIEFING':
                    if e.key == pygame.K_RETURN:
                        game.reset(); state = 'PLAYING'
                    elif e.key == pygame.K_ESCAPE:
                        state = 'MISSIONS'
                elif state == 'PLAYING':
                    if e.key == pygame.K_ESCAPE:
                        state = 'PAUSED'; pause_sel = 0
                    elif e.key == pygame.K_r:
                        game.reset()
                    elif e.key == pygame.K_F3:
                        game.show_fps = not game.show_fps
                    elif e.key == pygame.K_h:
                        game.show_help = not game.show_help
                    elif e.key in (pygame.K_c, pygame.K_TAB):
                        if game.scan_mode:
                            game.scan_mode = False; game.scan_cd = SCAN_CD
                        elif game.scan_cd <= 0 and game.player.en > 5:
                            game.scan_mode = True; game.scan_time = SCAN_MAX
                elif state == 'PAUSED':
                    if e.key == pygame.K_ESCAPE: state = 'PLAYING'
                    elif e.key in (pygame.K_UP, pygame.K_w): pause_sel = (pause_sel-1) % 3
                    elif e.key in (pygame.K_DOWN, pygame.K_s): pause_sel = (pause_sel+1) % 3
                    elif e.key == pygame.K_r:
                        game.reset(); state = 'PLAYING'
                    elif e.key == pygame.K_h:
                        game.show_help = not game.show_help
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if pause_sel == 0: state = 'PLAYING'
                        elif pause_sel == 1: game.reset(); state = 'PLAYING'
                        else: state = 'GARAGE'
                elif state in ('VICTORY', 'GAME_OVER'):
                    if e.key == pygame.K_SPACE: state = 'GARAGE'
                    elif e.key == pygame.K_r:
                        game.reset(); state = 'PLAYING'
            if state == 'PLAYING' and e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                game.player.fire_larm(game)
        if state == 'BRIEFING':
            brief_t += dt
        screen.fill(C_BG)
        if state == 'START':
            off = (gt*30) % 100
            for x in range(int(-off), W, 100): pygame.draw.line(screen, C_GRID, (x,0),(x,H))
            screen.blit(F_BIG.render("ARMORED CORE", True, C_WHITE), (W//2-380, H//2-160))
            screen.blit(F_MED.render("2D // VERTICAL SHIFT", True, C_BLUE), (W//2-200, H//2-70))
            if int(gt*2) % 2:
                screen.blit(F_MED.render("PRESS SPACE TO ENTER GARAGE", True, C_YELLOW), (W//2-290, H//2+30))
            screen.blit(F_TINY.render("M02: escorts now screen the targets - they will take the bullets for them.", True, C_CYAN), (W//2-370, H//2+90))
            screen.blit(F_TINY.render("AoE and piercing weapons beat the shield. Or strip it first.", True, C_CYAN), (W//2-330, H//2+120))
            screen.blit(F_TINY.render(VERSION, True, C_DIM), (W//2-60, H-40))
            screen.blit(VIG, (0,0)); screen.blit(SCANLINES, (0,0))
        elif state == 'GARAGE':
            draw_garage(screen, game, gt)
        elif state == 'MISSIONS':
            draw_missions(screen, game, mission_sel, gt)
        elif state == 'BRIEFING':
            draw_briefing(screen, game, brief_t)
        elif state in ('PLAYING', 'PAUSED'):
            if state == 'PLAYING':
                if game.hitstop > 0:
                    game.hitstop -= dt
                else:
                    res = game.update(dt, keys, mouse_pos, mouse_btn)
                    if res != 'PLAYING': state = res
            game.draw(screen)
            mx, my = mouse_pos
            mwx, mwy = mouse_pos[0]+game.cam[0], mouse_pos[1]+game.cam[1]
            over = any(math.hypot(e.x-mwx, e.y-mwy) < e.w+15 for e in game.enemies)
            ccol = C_RED if over else C_CYAN
            pygame.draw.circle(screen, ccol, (mx,my), 10, 1)
            pygame.draw.line(screen, ccol, (mx-14,my),(mx-6,my), 1)
            pygame.draw.line(screen, ccol, (mx+6,my),(mx+14,my), 1)
            pygame.draw.line(screen, ccol, (mx,my-14),(mx,my-6), 1)
            pygame.draw.line(screen, ccol, (mx,my+6),(mx,my+14), 1)
            if game.hitmark > 0:
                for ddx, ddy in ((-1,-1),(1,-1),(-1,1),(1,1)):
                    pygame.draw.line(screen, C_WHITE, (mx+ddx*5,my+ddy*5),(mx+ddx*11,my+ddy*11), 2)
            p = game.player
            if p.cfg['r_arm'] == 'rail' and p.rail_charge > 0:
                pygame.draw.rect(screen, (40,44,55), (mx-25, my+20, 50, 6))
                pygame.draw.rect(screen, C_CYAN if p.rail_charge < 1 else C_WHITE, (mx-25, my+20, 50*p.rail_charge, 6))
            pips = [
                ("S", p.cfg['l_arm'] == 'shotgun' and p.shotgun_cd <= 0),
                ("M", p.missile_cd <= 0 and p.missile_ammo >= 4 and p.en >= 20),
                ("B", p.blade_cd <= 0 and p.en >= 45),
            ]
            for i, (lab, rdy) in enumerate(pips):
                yy = my + 32 + i*14
                pygame.draw.rect(screen, (40,44,55), (mx+18, yy, 10, 10))
                if rdy: pygame.draw.rect(screen, C_CYAN, (mx+18, yy, 10, 10))
                screen.blit(F_TINY.render(lab, True, C_WHITE if rdy else C_DIM), (mx+32, yy-2))
            if game.show_help: game.draw_help(screen)
            if state == 'PAUSED': draw_pause(screen, pause_sel)
        elif state == 'VICTORY':
            screen.blit(F_BIG.render("MISSION COMPLETE", True, C_GREEN), (W//2-420, H//2-200))
            rank_col = {'S':C_YELLOW,'A':C_GREEN,'B':C_BLUE,'C':C_RED}.get(game.final_rank, C_WHITE)
            screen.blit(F_HUGE.render(game.final_rank or "?", True, rank_col), (W//2-40, H//2-120))
            st = game.stats
            screen.blit(F_SM.render(f"TIME {st['time']:.1f}s   DMG TAKEN {int(st['dmg_taken'])}   STAGGERS {st['staggers']}", True, C_WHITE), (W//2-300, H//2+60))
            screen.blit(F_MED.render(f"EARNED: +{game.earned} CR", True, C_GOLD), (W//2-180, H//2+105))
            if game.mission_idx == 1 and game.rail_unlocked:
                screen.blit(F_SM.render("UNLOCKED: RAILGUN (garage)", True, C_CYAN), (W//2-200, H//2+150))
            screen.blit(F_SM.render("R: RETRY   |   SPACE: GARAGE", True, C_YELLOW), (W//2-200, H//2+195))
            screen.blit(VIG, (0,0)); screen.blit(SCANLINES, (0,0))
        elif state == 'GAME_OVER':
            screen.blit(F_BIG.render("MISSION FAILED", True, C_RED), (W//2-380, H//2-100))
            screen.blit(F_SM.render(f"SALVAGE: +{game.earned} CR", True, C_GOLD), (W//2-160, H//2))
            screen.blit(F_SM.render("R: RETRY   |   SPACE: GARAGE", True, C_YELLOW), (W//2-200, H//2+60))
            screen.blit(VIG, (0,0)); screen.blit(SCANLINES, (0,0))
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()