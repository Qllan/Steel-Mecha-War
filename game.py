import pygame, math, random, sys, array, json, os, traceback

# ================= ВЕБ-ФЛАГ И БЕЗОПАСНЫЙ СТАРТ =================
WEB = (sys.platform == 'emscripten')   # True только в веб-сборке pygbag

if not WEB:                            # в вебе mixer НЕ трогаем вообще
    try: pygame.mixer.pre_init(22050, -16, 1, 512)
    except Exception: pass
pygame.init()
if not WEB:
    try: pygame.mixer.init()
    except Exception: pass

W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
F_TITLE = pygame.font.Font(None, 120)
F_BIG  = pygame.font.Font(None, 84)
F_HUGE = pygame.font.Font(None, 140)
F_MED  = pygame.font.Font(None, 44)
F_SM   = pygame.font.Font(None, 28)
F_TINY = pygame.font.Font(None, 20)

C_BG, C_GRID = (8, 9, 14), (22, 25, 36)
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
WAVES_M1 = [{'mt':4,'elite':0}, {'mt':5,'elite':1}, {'mt':6,'elite':2}]
WAVES_M3 = [{'turret':2,'mt':4,'elite':0}, {'turret':2,'mt':4,'elite':1}]
SCAN_MAX, SCAN_DRAIN, SCAN_CD = 4.0, 25.0, 3.5
VERSION = "v0.3.1 // TRUE DUELIST"
SAVE_FILE = "ac2d_save.json"
_WIN_EVENT = getattr(pygame, 'WINDOWEVENT', None)
_WIN_FOCUS_LOST = getattr(pygame, 'WINDOWEVENT_FOCUS_LOST', None)
_ACTIVE_EVENT = getattr(pygame, 'ACTIVEEVENT', None)

SR = 22050
MUTED = False
SND = {}
MUSIC = None

def _seq(*notes):
    if not notes: return []
    total = max(s + d for _, s, d, _, _ in notes)
    n = int(SR * total)
    out = [0.0] * n
    for f, s, d, v, w in notes:
        start = int(SR * s); ln = int(SR * d)
        for i in range(ln):
            if start + i >= n: break
            t = i / SR
            if w == 'square': val = 1.0 if math.sin(2*math.pi*f*t) > 0 else -1.0
            elif w == 'saw': val = 2.0*((f*t) % 1) - 1.0
            elif w == 'noise': val = random.uniform(-1, 1)
            else: val = math.sin(2*math.pi*f*t)
            out[start+i] += val * (1 - i/ln) * v
    return out

def _snd(samples):
    try:
        buf = array.array('h', [int(max(-1.0, min(1.0, s))*30000) for s in samples])
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None

def build_audio():
    global MUSIC
    if WEB:                            # в вебе звук отключён — тихо и безопасно
        return
    try:
        SND['boot']    = _snd(_seq((110,0,0.12,0.5,'sine'),(220,0.08,0.12,0.5,'sine'),(330,0.16,0.14,0.5,'sine'),(440,0.24,0.3,0.6,'sine'),(660,0.24,0.3,0.3,'sine')))
        SND['ui']      = _snd(_seq((880,0,0.05,0.25,'square')))
        SND['confirm'] = _snd(_seq((660,0,0.08,0.4,'sine'),(990,0.07,0.15,0.4,'sine')))
        SND['deny']    = _snd(_seq((220,0,0.15,0.4,'square'),(180,0.1,0.2,0.4,'square')))
        SND['rifle']   = _snd(_seq((700,0,0.06,0.18,'square'),(300,0,0.05,0.12,'saw')))
        SND['pulse']   = _snd(_seq((950,0,0.08,0.2,'sine'),(500,0,0.06,0.15,'sine')))
        SND['cannon']  = _snd(_seq((120,0,0.25,0.7,'sine'),(60,0,0.3,0.5,'sine'),(400,0,0.08,0.3,'noise')))
        SND['rail']    = _snd(_seq((1400,0,0.25,0.4,'saw'),(200,0,0.3,0.4,'sine'),(800,0,0.15,0.3,'noise')))
        SND['shotgun'] = _snd(_seq((300,0,0.15,0.5,'noise'),(150,0,0.2,0.4,'sine')))
        SND['grenade'] = _snd(_seq((180,0,0.12,0.5,'sine'),(90,0,0.15,0.4,'sine')))
        SND['missile'] = _snd(_seq((500,0,0.2,0.3,'saw'),(700,0.05,0.2,0.2,'saw')))
        SND['explosion']= _snd(_seq((90,0,0.4,0.7,'sine'),(50,0,0.5,0.5,'sine'),(600,0,0.25,0.5,'noise')))
        SND['bigboom'] = _snd(_seq((70,0,0.7,0.8,'sine'),(40,0,0.8,0.6,'sine'),(500,0,0.4,0.6,'noise'),(250,0.1,0.4,0.4,'noise')))
        SND['hit']     = _snd(_seq((400,0,0.04,0.15,'square')))
        SND['hurt']    = _snd(_seq((250,0,0.15,0.5,'square'),(120,0.05,0.2,0.4,'square')))
        SND['boost']   = _snd(_seq((300,0,0.18,0.35,'noise'),(500,0.03,0.15,0.25,'saw')))
        SND['stagger'] = _snd(_seq((500,0,0.3,0.5,'square'),(150,0.1,0.3,0.4,'square')))
        SND['perfect'] = _snd(_seq((1320,0,0.15,0.4,'sine'),(1760,0.05,0.2,0.4,'sine')))
        SND['blade']   = _snd(_seq((300,0,0.12,0.4,'saw'),(800,0.03,0.12,0.3,'saw'),(500,0,0.1,0.3,'noise')))
        SND['warning'] = _snd(_seq((440,0,0.2,0.5,'square'),(440,0.3,0.2,0.5,'square'),(440,0.6,0.3,0.5,'square')))
        SND['shield']  = _snd(_seq((1000,0,0.08,0.3,'sine'),(600,0,0.06,0.2,'sine')))
        SND['victory'] = _snd(_seq((440,0,0.15,0.4,'sine'),(554,0.12,0.15,0.4,'sine'),(659,0.24,0.3,0.5,'sine'),(880,0.4,0.4,0.5,'sine')))
        SND['defeat']  = _snd(_seq((330,0,0.2,0.4,'sine'),(262,0.18,0.2,0.4,'sine'),(196,0.36,0.4,0.4,'sine')))
        beat = 60/100
        seq_notes = []
        bass = [55, 55, 65.4, 49]
        for bar in range(2):
            for i, f in enumerate(bass):
                t0 = (bar*4 + i)*beat
                seq_notes.append((f, t0, beat*0.9, 0.5, 'sine'))
                seq_notes.append((f*2, t0, beat*0.25, 0.12, 'square'))
        MUSIC = _snd(_seq(*seq_notes))
    except Exception:
        pass

def play(name, vol=1.0):
    if MUTED: return
    s = SND.get(name)
    if s:
        try:
            s.set_volume(vol); s.play()
        except Exception:
            pass

def start_music():
    if MUSIC and not MUTED:
        try:
            MUSIC.set_volume(0.10); MUSIC.play(loops=-1)
        except Exception:
            pass

GLOWS = {}
def make_glow(col):
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    for r in range(32, 0, -1):
        pygame.draw.circle(s, (*col, int(150*(1-r/32)+12)), (32, 32), r)
    return s
def build_glows():
    for nm, col in [('cyan',C_CYAN),('orange',C_ORANGE),('red',C_RED),('yellow',C_YELLOW),
                    ('green',C_GREEN),('white',(255,255,255)),('magenta',C_MAGENTA),('mint',C_MINT),('blue',C_BLUE)]:
        GLOWS[nm] = make_glow(col)
def draw_glow(surf, x, y, size, name, alpha=255):
    g = GLOWS.get(name)
    if not g: return
    g.set_alpha(alpha)
    sc = pygame.transform.scale(g, (int(size), int(size)))
    surf.blit(sc, (int(x-size/2), int(y-size/2)))

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
   'legend': dict(n='OVERDRIVE CORE',  cost=0,    w=50, en=180, regen=35, desc='LEGENDARY: massive EN', unlock_campaign=True),
 },
}
SLOT_ORDER = ['r_arm', 'l_arm', 'legs', 'gen']
SLOT_LABEL = {'r_arm':'R-ARM', 'l_arm':'L-ARM', 'legs':'LEGS', 'gen':'GENERATOR'}
DEFAULT_PARTS = {'r_arm':'rifle', 'l_arm':'shotgun', 'legs':'biped', 'gen':'std'}

MISSIONS = [
 {'id':'m1','code':'MISSION 01','name':'HOSTILE SWEEP','reward':1000,'boss':True,'targets':0,'boss_id':'vindicta','waves':WAVES_M1,
  'obj':'Eliminate all MT waves. Defeat rival AC VINDICTA.',
  'brief':['Hostile MT squad detected in sector 7.','Commander-class units providing fire support.',
           'Rival AC signature confirmed - VINDICTA, a blade duelist.','It will dash at you with a blade. QB through it or clash.','Sweep the sector. Neutralize all hostiles.']},
 {'id':'m2','code':'MISSION 02','name':'PRIORITY TARGETS','reward':1800,'boss':False,'targets':3,'boss_id':None,'waves':None,
  'obj':'Destroy 3 marked GUNNER emplacements. Escorts are optional.',
  'brief':['Three gunner emplacements are shelling our positions.','They are marked as PRIORITY TARGETS.',
           'Escort screen will physically block your shots - they interpose themselves.',
           'Use AoE or piercing weapons, or strip the screen first.','Destroy all three targets. Extraction on completion.']},
 {'id':'m3','code':'MISSION 03','name':'SIEGEBREAK','reward':2500,'boss':True,'targets':0,'boss_id':'bastion','waves':WAVES_M3,
  'obj':'Breach the perimeter. Destroy fortress AC BASTION.',
  'brief':['The enemy has dug in behind a fortified perimeter.','Stationary mortar emplacements cover the approach.',
           'Fortress AC BASTION holds the center - its frontal shield blocks direct fire.',
           'Flank it, or build stagger to drop the shield. This is the final wall.','Breach it.']},
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

def draw_mech_shape(surf, cx, cy, ang, cfg, scale=1.0, body_col=None, ghost=False, thrust=False, dim=False, t=0):
    if body_col is None:
        body_col = (60,80,115) if ghost else ((105,110,120) if dim else (222,228,240))
    s = scale
    dark = tuple(max(0, c-70) for c in body_col)
    lite = tuple(min(255, c+25) for c in body_col)
    def poly(pts, col, width=0):
        pygame.draw.polygon(surf, col, rot_pts(cx, cy, [(x*s,y*s) for x,y in pts], ang), width)
    if thrust and not ghost:
        flick = random.randint(0, 6)
        for side in (-1, 1):
            poly([(-21, side*12), (-33-flick, side*10), (-21, side*8)], C_CYAN)
            poly([(-21, side*11), (-27-flick//2, side*10), (-21, side*9)], C_WHITE)
        draw_glow(surf, cx - math.cos(ang)*26*s, cy - math.sin(ang)*26*s, 30*s, 'cyan', 120)
    if cfg['legs'] == 'tank':
        for side in (-1,1):
            poly([(-22,side*20),(-2,side*20),(-2,side*10),(-22,side*10)], dark)
            poly([(-20,side*18),(-4,side*18),(-4,side*12),(-20,side*12)], (90,100,120) if not ghost else dark)
    elif cfg['legs'] == 'rjoint':
        for side in (-1,1):
            poly([(-18,side*16),(-4,side*16),(-8,side*8),(-20,side*8)], dark)
            pygame.draw.circle(surf, lite, rot_pts(cx,cy,[(-12,side*12)],ang)[0], int(2.5*s))
    else:
        for side in (-1,1):
            poly([(-20,side*18),(-6,side*18),(-6,side*9),(-20,side*9)], dark)
            pygame.draw.circle(surf, lite, rot_pts(cx,cy,[(-13,side*13)],ang)[0], int(2.5*s))
    torso = [(-18,-14),(12,-16),(26,0),(12,16),(-18,14)]
    poly(torso, dark)
    poly([(-16,-12),(10,-14),(23,0),(10,14),(-16,12)], body_col)
    poly([(-10,-8),(8,-9),(16,0),(8,9),(-10,8)], lite)
    poly(torso, (30,38,55) if not ghost else dark, 2)
    if not ghost:
        pulse = 0.7 + 0.3*math.sin(t*6)
        poly([(10,-5),(24,0),(10,5)], C_BLUE)
        draw_glow(surf, cx+math.cos(ang)*16*s, cy+math.sin(ang)*16*s, 22*s*pulse, 'cyan', 140)
    else:
        poly([(10,-5),(24,0),(10,5)], (40,70,110))
    ra = cfg['r_arm']
    if ra == 'cannon':
        poly([(4,7),(36,7),(36,16),(4,16)], (150,100,40) if not ghost else dark)
        poly([(30,8),(36,8),(36,15),(30,15)], C_ORANGE)
    elif ra == 'rail':
        poly([(2,8),(40,8),(40,13),(2,13)], (40,110,140) if not ghost else dark)
        poly([(36,9),(40,9),(40,12),(36,12)], C_CYAN)
    elif ra == 'pulse':
        poly([(6,7),(30,7),(30,12),(6,12)], (60,130,150) if not ghost else dark)
        poly([(26,8),(30,8),(30,11),(26,11)], C_CYAN)
    else:
        poly([(6,7),(30,7),(30,12),(6,12)], (150,160,180) if not ghost else dark)
        poly([(26,8),(30,8),(30,11),(26,11)], C_YELLOW)
    la = cfg['l_arm']
    if la == 'shield':
        poly([(14,-16),(20,-16),(20,-2),(14,-2)], (40,110,160) if not ghost else dark)
    elif la == 'grenade':
        poly([(4,-14),(22,-14),(22,-6),(4,-6)], (140,90,40) if not ghost else dark)
        pygame.draw.circle(surf, C_ORANGE, rot_pts(cx,cy,[(22,-10)],ang)[0], int(3*s))
    else:
        poly([(6,-12),(24,-12),(24,-7),(6,-7)], (120,50,50) if not ghost else dark)

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

class DangerZone:
    def __init__(self, x, y, radius, fuse, dmg):
        self.x, self.y, self.radius, self.dmg = x, y, radius, dmg
        self.fuse = fuse; self.max_fuse = fuse
    def update(self, dt):
        self.fuse -= dt
        return self.fuse <= 0
    def draw(self, surf, cam):
        x, y = self.x-cam[0], self.y-cam[1]
        prog = 1 - self.fuse/self.max_fuse
        pulse = 0.5 + 0.5*math.sin(pygame.time.get_ticks()/90)
        pygame.draw.circle(surf, C_RED, (int(x),int(y)), self.radius, 2)
        fill = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(fill, (255,60,40,int(35+90*prog*pulse)), (self.radius, self.radius), self.radius)
        surf.blit(fill, (int(x-self.radius), int(y-self.radius)))

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
        x, y = int(self.x-cam[0]), int(self.y-cam[1])
        gname = 'yellow' if self.col==C_YELLOW else ('cyan' if self.col==C_CYAN else ('orange' if self.col==C_ORANGE else 'red'))
        if self.owner == 'player':
            draw_glow(surf, x, y, self.sz*6, gname, 90)
        pygame.draw.circle(surf, self.col, (x, y), self.sz)
        pygame.draw.circle(surf, C_WHITE, (x, y), max(1, self.sz//2))

class Grenade(Bullet):
    def __init__(self, x, y, ang):
        super().__init__(x, y, ang, 420, 0, 0, C_ORANGE, 'player', 5)
        self.fuse = 0.9
    def update(self, dt):
        super().update(dt); self.fuse -= dt
    def draw(self, surf, cam):
        cx, cy = int(self.x-cam[0]), int(self.y-cam[1])
        draw_glow(surf, cx, cy, 24, 'orange', 100)
        pygame.draw.circle(surf, self.col, (cx, cy), self.sz)
        pygame.draw.circle(surf, C_YELLOW, (cx, cy), self.sz+3, 1)

class MortarShell(Bullet):
    def __init__(self, x, y, ang):
        super().__init__(x, y, ang, 210, 0, 0, C_MINT, 'enemy', 6)
        self.fuse = 2.4
    def update(self, dt):
        super().update(dt); self.fuse -= dt
    def draw(self, surf, cam):
        cx, cy = int(self.x-cam[0]), int(self.y-cam[1])
        r = self.sz + int(2*math.sin(pygame.time.get_ticks()/80))
        draw_glow(surf, cx, cy, 26, 'mint', 80)
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
    def __init__(self, x, y, is_boss=False, is_elite=False, is_target=False, force_type=None, boss_id=None):
        super().__init__()
        self.x, self.y, self.is_boss, self.is_elite, self.is_target = x, y, is_boss, is_elite, is_target
        self.ang = 0
        self.mtype = 'striker'
        self.boss_id = boss_id if is_boss else None
        if not is_boss and not is_elite:
            if force_type: self.mtype = force_type
            else:
                r = random.random()
                self.mtype = 'striker' if r < 0.35 else ('rusher' if r < 0.60 else ('gunner' if r < 0.85 else 'mortar'))
        if is_boss:
            self.duel_state = 'circle'
            self.duel_timer = 0
            self.dash_target = (0, 0)
            self.blade_active = False
            self.blade_hit_done = False
            if boss_id == 'bastion':
                self.max_ap, self.max_stagger, self.spd, self.w = 3000, 350, 95, 60
                self.bastion_shield = True
                self.bastion_beam_cd = 3.5
                self.bastion_mortar_cd = 2.0
                self.bastion_missile_cd = 4.0
                self.bastion_beam_telegraph = 0
                self.bastion_beam_ang = 0
                self.bastion_enraged = False
            else:
                self.max_ap, self.max_stagger, self.spd, self.w = 2000, 280, 250, 50
        elif is_elite:
            self.max_ap, self.max_stagger, self.spd, self.w = 260, 95, 215, 22
        elif self.mtype == 'rusher':
            self.max_ap, self.max_stagger, self.spd, self.w = 85, 45, 220, 16
        elif self.mtype == 'gunner':
            self.max_ap, self.max_stagger, self.spd, self.w = 130, 60, 110, 20
        elif self.mtype == 'mortar':
            self.max_ap, self.max_stagger, self.spd, self.w = 110, 55, 100, 19
        elif self.mtype == 'turret':
            self.max_ap, self.max_stagger, self.spd, self.w = 200, 80, 0, 24
        else:
            self.max_ap, self.max_stagger, self.spd, self.w = 100, 55, 145, 18
        if is_target: self.max_ap = 160
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
        self.spawn_flash = 0.8 if is_boss else (0.6 if is_elite else 0)
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
        self.boss_blade_cd = 1.5
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
    def take_damage(self, dmg, stag, game, col=C_YELLOW, bypass=False, src=None):
        if self.is_boss and self.boss_id=='bastion' and self.bastion_shield and self.stg_timer<=0 and src is not None:
            ang_to_src = math.atan2(src[1]-self.y, src[0]-self.x)
            diff = abs(ang_to_src - self.ang)
            if diff > math.pi: diff = 2*math.pi - diff
            if diff < 1.1:
                self.stagger += stag*0.5
                self.hit_flash = 0.05
                if game:
                    game.add_shake(2)
                    play('shield', 0.4)
                    for _ in range(4): game.particles.add(Particle(src[0], src[1], C_CYAN, 150))
                if self.stagger >= self.max_stagger:
                    self.stagger = 0; self.stg_timer = 2.5
                    if game:
                        game.stats['staggers'] += 1
                        game.add_float("ACS BREAK!", self.x, self.y-self.w-34, C_ORANGE, big=True)
                        game.add_shake(8)
                        game.slowmo_timer = max(game.slowmo_timer, 0.15)
                        play('stagger', 0.7)
                        for _ in range(20): game.particles.add(Particle(self.x, self.y, C_WHITE, 250))
                return
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
                    play('stagger', 0.5)
                    for _ in range(14): game.particles.add(Particle(self.x, self.y, C_CYAN, 220))
            return
        was_stg = self.stg_timer > 0
        self.ap -= dmg*(3.0 if was_stg else 1.0)
        self.stagger += stag
        self.hit_flash = 0.08
        if game:
            game.dmg_nums.add(DamageNumber(self.x, self.y-self.w-10, dmg*(3.0 if was_stg else 1.0), C_ORANGE if was_stg else col))
            game.add_shake(2 if not self.is_boss else 4)
            play('hit', 0.25)
            if self.guard_of is not None and self.guard_of.alive():
                for _ in range(3): game.particles.add(Particle(self.x, self.y, C_MINT, 100))
        if self.stagger >= self.max_stagger:
            self.stagger = 0; self.stg_timer = 2.5
            if game:
                game.stats['staggers'] += 1
                game.add_shake(8)
                game.slowmo_timer = max(game.slowmo_timer, 0.15)
                game.add_float("ACS BREAK!" if self.is_boss else "STAGGER!", self.x, self.y-self.w-34, C_ORANGE, big=True)
                play('stagger', 0.7)
                for _ in range(20): game.particles.add(Particle(self.x, self.y, C_WHITE, 250))
        if self.ap <= 0:
            self.kill()
            if game:
                game.combo += 1; game.combo_timer = 2.5
                game.add_shake(10 if self.is_boss else 6)
                game.rings.append({'x':self.x,'y':self.y,'r':10,'life':0.4,'col':C_ORANGE if not self.is_boss else C_RED})
                play('bigboom' if self.is_boss else 'explosion', 0.7)
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
    def boss_tick(self, dt, plr, bullets, game):
        for attr in ('hit_flash','boss_blade_cd','boss_missile_cd','boss_burst_cd','boss_shotgun_cd','boss_muzzle','dodge_cd'):
            if getattr(self, attr, 0) > 0: setattr(self, attr, getattr(self, attr)-dt)
        if self.spawn_flash > 0: self.spawn_flash -= dt
        self.boss_ghosts = [(x,y,a,t2-dt) for x,y,a,t2 in self.boss_ghosts if t2-dt > 0]
        self.boss_orbit_t -= dt
        if self.boss_orbit_t <= 0:
            self.boss_orbit *= -1; self.boss_orbit_t = random.uniform(1.5, 3.0)
        if self.duel_state not in ('blade_dash','reposition'):
            self.boss_en = min(self.boss_en_max, self.boss_en + 20*dt)
        if not self.phase2 and not self.phase2_trigger and self.ap < self.max_ap*0.5:
            self.phase2_trigger = True
            game.slowmo_timer = 2.0
            game.slowmo_text = "VINDICTA: LIMITER RELEASED"
            game.add_shake(12)
            play('warning', 0.7)
            self.ap = min(self.max_ap, self.ap + self.max_ap*0.08)
        if self.phase2_trigger and not self.phase2 and game.slowmo_timer <= 0:
            self.phase2 = True
            game.slowmo_text = ""
            game.add_float("DUELIST MODE", self.x, self.y-self.w-40, C_RED, big=True)
        dx, dy = plr.x-self.x, plr.y-self.y
        dist = math.hypot(dx,dy) or 1
        self.ang = math.atan2(dy, dx)
        cd_mult = 0.6 if self.phase2 else 1.0
        spd_mult = 1.3 if self.phase2 else 1.0
        player_vuln = plr.stalled or plr.scanning
        if self.stg_timer > 0:
            self.stg_timer -= dt
            self.vx = self.vy = 0
            if self.stg_timer <= 0 and self.boss_en >= 20:
                self.duel_state = 'reposition'
                self.duel_timer = 0.2
                self.dash_dir = (-dx/dist, -dy/dist)
                self.boss_en -= 20
        else:
            if self.duel_state == 'circle':
                spd = self.spd * spd_mult
                if dist > 420:
                    self.vx, self.vy = dx/dist*spd, dy/dist*spd
                elif dist < 280:
                    self.vx, self.vy = -dx/dist*spd*0.7, -dy/dist*spd*0.7
                else:
                    px, py = -dy/dist, dx/dist
                    self.vx, self.vy = px*spd*0.8*self.boss_orbit, py*spd*0.8*self.boss_orbit
                if self.boss_en >= 18 and self.dodge_cd <= 0:
                    for b in bullets:
                        if b.owner != 'player': continue
                        bdx, bdy = self.x-b.x, self.y-b.y
                        bd = math.hypot(bdx, bdy)
                        if bd < 170 and (b.vx*bdx + b.vy*bdy) > 0:
                            perp = (-b.vy, b.vx); m = math.hypot(*perp) or 1
                            side = random.choice([-1,1])
                            self.dash_dir = (perp[0]/m*side, perp[1]/m*side)
                            self.duel_state = 'reposition'; self.duel_timer = 0.18
                            self.boss_en -= 18; self.dodge_cd = 1.4
                            play('boost', 0.4)
                            break
                if self.duel_state == 'circle' and self.boss_en >= 18 and self.dodge_cd <= 0 and self.player_threat(plr) and dist < 300:
                    px, py = -dy/dist, dx/dist
                    side = random.choice([-1,1])
                    self.dash_dir = (px*side, py*side)
                    self.duel_state = 'reposition'; self.duel_timer = 0.2
                    self.boss_en -= 18; self.dodge_cd = 1.4
                    play('boost', 0.4)
                if self.duel_state == 'circle':
                    if self.boss_burst_cd <= 0 and dist < 620 and self.boss_burst_left <= 0:
                        self.boss_burst_cd = 1.2*cd_mult; self.boss_burst_left = 4
                    if self.boss_missile_cd <= 0 and self.boss_en >= 15 and dist > 420:
                        self.boss_missile_cd = 5.0*cd_mult; self.boss_en -= 15
                        for i in range(5):
                            bullets.add(Missile(self.x, self.y, self.ang+random.uniform(-0.6,0.6), [plr], 'enemy'))
                        play('missile', 0.5)
                    if self.boss_blade_cd <= 0 and self.boss_en >= 25:
                        if player_vuln and dist < 560:
                            self.duel_state = 'blade_windup'; self.duel_timer = 0.15
                            self.boss_blade_cd = 2.0*cd_mult
                        elif dist < (560 if self.phase2 else 460):
                            self.duel_state = 'blade_windup'; self.duel_timer = 0.25
                            self.boss_blade_cd = 2.4*cd_mult
            elif self.duel_state == 'blade_windup':
                self.vx = self.vy = 0
                self.duel_timer -= dt
                if self.duel_timer <= 0:
                    t = dist/920
                    self.dash_target = (plr.x + plr.pvx*t*0.7, plr.y + plr.pvy*t*0.7)
                    self.duel_state = 'blade_dash'
                    self.duel_timer = 0.32
                    self.boss_en -= 25
                    self.blade_active = True
                    self.blade_hit_done = False
                    self.boss_blade_anim = 0.32
                    play('blade', 0.7)
            elif self.duel_state == 'blade_dash':
                self.duel_timer -= dt
                tdx, tdy = self.dash_target[0]-self.x, self.dash_target[1]-self.y
                td = math.hypot(tdx,tdy) or 1
                self.vx, self.vy = tdx/td*920, tdy/td*920
                self.boss_ghosts.append((self.x, self.y, self.ang, 0.22))
                self.boss_blade_anim = max(self.boss_blade_anim, 0.1)
                if dist < 180 and not self.blade_hit_done:
                    self.blade_hit_done = True
                    if game.player.blade_timer > 0:
                        game.hitstop = max(game.hitstop, 0.12)
                        game.add_shake(8)
                        game.rings.append({'x':(self.x+plr.x)/2,'y':(self.y+plr.y)/2,'r':15,'life':0.35,'col':C_YELLOW})
                        for _ in range(20): game.particles.add(Particle((self.x+plr.x)/2,(self.y+plr.y)/2, C_YELLOW, 300))
                        self.duel_state = 'recover'; self.duel_timer = 0.45
                        self.blade_active = False
                    else:
                        game.hurt(35, self.x, self.y)
                        game.add_shake(6)
                if self.duel_timer <= 0 or td < 30:
                    self.blade_active = False
                    if self.duel_state == 'blade_dash':
                        self.duel_state = 'recover'; self.duel_timer = 0.35
            elif self.duel_state == 'recover':
                self.duel_timer -= dt
                self.vx *= 0.85; self.vy *= 0.85
                if self.duel_timer <= 0:
                    if dist < 250 and self.boss_en >= 15:
                        self.duel_state = 'reposition'; self.duel_timer = 0.2
                        px, py = -dy/dist, dx/dist
                        side = random.choice([-1,1])
                        self.dash_dir = (px*side, py*side)
                        self.boss_en -= 15
                    else:
                        self.duel_state = 'circle'
            elif self.duel_state == 'reposition':
                self.duel_timer -= dt
                if self.dash_dir:
                    self.vx, self.vy = self.dash_dir[0]*860, self.dash_dir[1]*860
                    self.boss_ghosts.append((self.x, self.y, self.ang, 0.18))
                if self.duel_timer <= 0:
                    self.dash_dir = None
                    self.duel_state = 'circle'
            if self.boss_burst_left > 0 and self.duel_state == 'circle':
                self.boss_burst_t -= dt
                if self.boss_burst_t <= 0:
                    self.boss_burst_t = 0.09
                    self.boss_burst_left -= 1
                    ang = self.aim_angle(plr, 560, 0.5) + random.uniform(-0.03,0.03)
                    bullets.add(Bullet(self.x, self.y, ang, 560, 8, 3, C_RED, 'enemy', 3))
                    self.boss_muzzle = 0.05
                    play('rifle', 0.3)
        self.x += self.vx*dt; self.y += self.vy*dt
        self.x = clamp(self.x, 40, MAP_W-40); self.y = clamp(self.y, 40, MAP_H-40)
        self.rect.center = (self.x, self.y)
    def boss_draw(self, surf, cam, scan_mode=False, t=0):
        cx, cy = self.x-cam[0], self.y-cam[1]
        s = 1.9
        flash = self.hit_flash > 0 or (self.stg_timer>0 and int(self.stg_timer*10)%2)
        p2 = self.phase2
        windup = self.duel_state == 'blade_windup'
        dashing = self.duel_state == 'blade_dash'
        recovering = self.duel_state == 'recover'
        body_col = (160,160,170) if flash else (100,60,60)
        if recovering: body_col = tuple(max(0,c-35) for c in body_col)
        dark = tuple(max(0,c-55) for c in body_col)
        accent = C_RED if p2 else C_ORANGE
        body = [(-22,-18),(14,-20),(30,0),(14,20),(-22,18)]
        def poly(pts, col, width=0):
            pygame.draw.polygon(surf, col, rot_pts(cx, cy, [(x*s,y*s) for x,y in pts], self.ang), width)
        for gx,gy,ga,gt in self.boss_ghosts:
            a = clamp(gt/0.22,0,1)
            pygame.draw.polygon(surf, (int(95*a),int(45*a),int(45*a)), rot_pts(gx-cam[0],gy-cam[1],[(x*s,y*s) for x,y in body], ga))
        if abs(self.vx)+abs(self.vy)>30 or dashing:
            for side in (-1,1):
                poly([(-24,side*13),(-36-random.randint(0,8),side*11),(-24,side*9)], accent)
            draw_glow(surf, cx-math.cos(self.ang)*40, cy-math.sin(self.ang)*40, 55, 'orange' if not p2 else 'red', 130)
        for side in (-1,1):
            poly([(-20,side*16),(-4,side*16),(-4,side*8),(-20,side*8)], dark)
        poly(body, dark)
        poly([(-20,-16),(12,-18),(27,0),(12,18),(-20,16)], body_col)
        poly([(-12,-10),(8,-11),(18,0),(8,11),(-12,10)], tuple(min(255,c+30) for c in body_col))
        poly(body, (40,25,25), 2)
        for side in (-1,1):
            poly([(-14,side*18),(2,side*18),(2,side*26),(-14,side*26)], dark)
            pygame.draw.circle(surf, accent, rot_pts(cx,cy,[(-6,side*22)],self.ang)[0], int(3*s))
        poly([(14,-6),(28,0),(14,6)], C_RED if p2 else C_YELLOW)
        draw_glow(surf, cx+math.cos(self.ang)*38, cy+math.sin(self.ang)*38, 30, 'red' if p2 else 'yellow', 120)
        poly([(16,6),(44,6),(44,12),(16,12)], (80,80,90))
        blade_col = C_CYAN if (windup or dashing) else (C_ORANGE if p2 else (180,190,210))
        blade = [(20,-14),(56,-10),(58,-4),(22,-6)]
        poly(blade, blade_col)
        if windup or dashing:
            poly(blade, C_WHITE, 1)
            draw_glow(surf, cx+math.cos(self.ang)*55, cy+math.sin(self.ang)*55, 50, 'cyan', 150)
            if windup:
                ex, ey = math.cos(self.ang)*300, math.sin(self.ang)*300
                pygame.draw.line(surf, C_CYAN, (cx,cy),(cx+ex,cy+ey), 2)
        if self.boss_muzzle > 0:
            gx, gy = rot_pts(cx,cy,[(46*s,9*s)],self.ang)[0]
            draw_glow(surf, gx, gy, 40, 'yellow', 180)
            pygame.draw.circle(surf, C_YELLOW, (int(gx),int(gy)), random.randint(4,7))
        if self.spawn_flash > 0:
            pygame.draw.circle(surf, C_RED, (int(cx),int(cy)), max(1,int((0.8-self.spawn_flash)*220)), 3)
        if scan_mode:
            pygame.draw.polygon(surf, C_RED, rot_pts(cx,cy,[(x*s*1.15,y*s*1.15) for x,y in body],self.ang), 3)
            if self.stg_timer>0:
                surf.blit(F_TINY.render("WEAK POINT", True, C_RED), (cx-42, cy-self.w-26))
        if self.boss_en < 20 and int(pygame.time.get_ticks()/200)%2:
            surf.blit(F_TINY.render("GUARD DOWN", True, C_YELLOW), (cx-44, cy-self.w-42))
        state_lbl = {'circle':'CIRCLE','blade_windup':'WINDUP','blade_dash':'BLADE DASH','recover':'RECOVER','reposition':'REPOSITION'}.get(self.duel_state,'')
        lbl = F_TINY.render(state_lbl + (" // LIMITER" if p2 else ""), True, C_RED if p2 else C_DIM)
        surf.blit(lbl, (cx-lbl.get_width()//2, cy+self.w+8))
    def fire_beam(self, game, plr):
        dx, dy = math.cos(self.bastion_beam_ang), math.sin(self.bastion_beam_ang)
        game.beams.append({'x1':self.x+dx*40,'y1':self.y+dy*40,'x2':self.x+dx*900,'y2':self.y+dy*900,'life':0.3,'ml':0.3,'col':C_RED,'wide':True})
        play('rail', 0.7)
        game.add_shake(8)
        ex, ey = plr.x-self.x, plr.y-self.y
        proj = ex*dx + ey*dy
        if 0 < proj < 900 and abs(ex*dy - ey*dx) < 45:
            game.hurt(45, self.x, self.y)
    def spawn_mortars(self, plr, game):
        play('grenade', 0.5)
        for i in range(4):
            tx = plr.x + plr.pvx*0.8 + random.uniform(-120,120)
            ty = plr.y + plr.pvy*0.8 + random.uniform(-120,120)
            game.zones.append(DangerZone(tx, ty, 90, 1.2, 30))
    def bastion_tick(self, dt, plr, bullets, game):
        for attr in ('hit_flash','bastion_beam_cd','bastion_mortar_cd','bastion_missile_cd'):
            if getattr(self, attr, 0) > 0: setattr(self, attr, getattr(self, attr)-dt)
        if self.spawn_flash > 0: self.spawn_flash -= dt
        if not self.bastion_enraged and self.ap < self.max_ap*0.4:
            self.bastion_enraged = True
            self.bastion_shield = False
            game.add_float("SHIELD DOWN", self.x, self.y-self.w-40, C_RED, big=True)
            game.slowmo_timer = max(game.slowmo_timer, 1.0)
            game.add_shake(12)
            play('warning', 0.8)
            for _ in range(30): game.particles.add(Particle(self.x, self.y, C_CYAN, 300))
        cd_mult = 0.6 if self.bastion_enraged else 1.0
        spd_mult = 1.5 if self.bastion_enraged else 1.0
        dx, dy = plr.x-self.x, plr.y-self.y
        dist = math.hypot(dx,dy) or 1
        self.ang = math.atan2(dy, dx)
        if self.bastion_beam_telegraph > 0:
            self.bastion_beam_telegraph -= dt
            self.bastion_beam_ang = self.ang
            self.vx = self.vy = 0
            if self.bastion_beam_telegraph <= 0:
                self.fire_beam(game, plr)
        elif self.stg_timer > 0:
            self.stg_timer -= dt
            self.vx = self.vy = 0
        else:
            spd = self.spd * spd_mult
            if dist > 420:
                self.vx, self.vy = dx/dist*spd, dy/dist*spd
            elif dist < 280:
                self.vx, self.vy = -dx/dist*spd*0.6, -dy/dist*spd*0.6
            else:
                self.vx, self.vy = 0, 0
            if self.bastion_mortar_cd <= 0:
                self.bastion_mortar_cd = 2.8*cd_mult
                self.spawn_mortars(plr, game)
            if self.bastion_missile_cd <= 0:
                self.bastion_missile_cd = 5.5*cd_mult
                for i in range(7):
                    bullets.add(Missile(self.x, self.y, self.ang+random.uniform(-0.7,0.7), [plr], 'enemy'))
                play('missile', 0.5)
            if self.bastion_beam_cd <= 0 and self.bastion_beam_telegraph <= 0:
                self.bastion_beam_cd = 4.5*cd_mult
                self.bastion_beam_telegraph = 0.8
                play('warning', 0.4)
            if dist < 160 and random.random() < dt*1.5:
                game.zones.append(DangerZone(self.x, self.y, 170, 0.55, 40))
        self.x += self.vx*dt; self.y += self.vy*dt
        self.x = clamp(self.x, 40, MAP_W-40); self.y = clamp(self.y, 40, MAP_H-40)
        self.rect.center = (self.x, self.y)
    def bastion_draw(self, surf, cam, scan_mode=False, t=0):
        cx, cy = self.x-cam[0], self.y-cam[1]
        s = 2.2
        ang = self.ang
        flash = self.hit_flash > 0 or (self.stg_timer>0 and int(self.stg_timer*10)%2)
        enraged = self.bastion_enraged
        body_col = (170,170,180) if flash else ((115,70,50) if enraged else (92,97,112))
        dark = tuple(max(0,c-50) for c in body_col)
        def poly(pts, col, width=0):
            pygame.draw.polygon(surf, col, rot_pts(cx, cy, [(x*s,y*s) for x,y in pts], ang), width)
        body = [(-24,-26),(16,-26),(28,-10),(28,10),(16,26),(-24,26)]
        if abs(self.vx)+abs(self.vy) > 20:
            draw_glow(surf, cx-math.cos(ang)*45, cy-math.sin(ang)*45, 60, 'orange' if enraged else 'yellow', 100)
        poly(body, dark)
        poly([(-22,-24),(14,-24),(26,-9),(26,9),(14,24),(-22,24)], body_col)
        poly(body, (30,35,45), 2)
        for side in (-1,1):
            poly([(-10, side*24),(20, side*24),(20, side*32),(-10, side*32)], dark)
            pygame.draw.circle(surf, C_ORANGE if enraged else C_YELLOW, rot_pts(cx,cy,[(20,side*28)],ang)[0], int(3*s))
        poly([(8,-8),(20,0),(8,8)], C_RED if enraged else C_YELLOW)
        draw_glow(surf, cx+math.cos(ang)*25, cy+math.sin(ang)*25, 40, 'red' if enraged else 'yellow', 130)
        for side in (-1,1):
            poly([(-26, side*14),(-14, side*14),(-14, side*20),(-26, side*20)], dark)
        if self.bastion_shield and self.stg_timer<=0:
            pts = []
            for i in range(11):
                a = ang - 1.1 + (i/10)*2.2
                pts.append((cx+math.cos(a)*(self.w+18), cy+math.sin(a)*(self.w+18)))
            pulse = 0.6+0.4*math.sin(t*5)
            pygame.draw.lines(surf, C_CYAN, False, pts, 4)
            draw_glow(surf, cx+math.cos(ang)*(self.w+10), cy+math.sin(ang)*(self.w+10), 60, 'cyan', int(80*pulse))
        if self.bastion_beam_telegraph > 0:
            ex, ey = math.cos(self.bastion_beam_ang)*900, math.sin(self.bastion_beam_ang)*900
            pygame.draw.line(surf, C_RED, (cx,cy),(cx+ex,cy+ey), 2)
            draw_glow(surf, cx+math.cos(self.bastion_beam_ang)*40, cy+math.sin(self.bastion_beam_ang)*40, 50, 'red', 150)
        if self.spawn_flash > 0:
            pygame.draw.circle(surf, C_RED, (int(cx),int(cy)), max(1,int((0.8-self.spawn_flash)*250)), 3)
        if scan_mode:
            pygame.draw.polygon(surf, C_RED, rot_pts(cx,cy,[(x*s*1.1,y*s*1.1) for x,y in body],ang), 3)
            if self.stg_timer>0:
                surf.blit(F_TINY.render("WEAK POINT", True, C_RED), (cx-42, cy-self.w-26))
        if enraged and int(t*5)%2:
            surf.blit(F_TINY.render("ENRAGED", True, C_RED), (cx-30, cy-self.w-42))
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
                    boost = 2.4; break
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
            if self.boss_id == 'bastion':
                self.bastion_tick(dt, plr, bullets, game)
            else:
                self.boss_tick(dt, plr, bullets, game)
            return
        if self.mtype == 'turret':
            self.ang = math.atan2(plr.y-self.y, plr.x-self.x)
            self.vx = self.vy = 0
            if self.stg_timer > 0:
                self.stg_timer -= dt
            else:
                self.shoot_cd -= dt
                d = math.hypot(plr.x-self.x, plr.y-self.y)
                if self.shoot_cd <= 0 and d < 800:
                    self.shoot_cd = 2.6
                    game.zones.append(DangerZone(plr.x+plr.pvx*0.7, plr.y+plr.pvy*0.7, 85, 1.3, 25))
                    play('grenade', 0.4)
            self.rect.center = (self.x, self.y)
            return
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
                        t2 = dist/900
                        px2 = plr.x + getattr(plr,'pvx',0)*t2*0.8
                        py2 = plr.y + getattr(plr,'pvy',0)*t2*0.8
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
                play('cannon', 0.4)
            else:
                for i in range(3):
                    bullets.add(Bullet(self.x, self.y, ang+(i-1)*0.08, 500, 14, 4, C_ORANGE, 'enemy', 3))
                self.shoot_cd = 1.3
                play('rifle', 0.35)
            if self.enraged: self.shoot_cd *= 0.8
            perp = (-math.sin(self.ang), math.cos(self.ang))
            side = random.choice([-1, 1])
            self.dash_dir = (perp[0]*side, perp[1]*side)
            self.qb_timer = 0.22
        elif self.mtype == 'gunner':
            bullets.add(Bullet(self.x, self.y, self.aim_ang, 540, 15, 4, C_RED, 'enemy', 4))
            self.burst_ang = self.aim_ang; self.burst_timer = 0.14
            self.shoot_cd = 2.4
            play('rifle', 0.3)
        elif self.mtype == 'mortar':
            bullets.add(MortarShell(self.x, self.y, self.aim_ang))
            self.shoot_cd = 3.2
            play('grenade', 0.4)
        else:
            ang = self.aim_angle(plr, 470, 0.55)
            bullets.add(Bullet(self.x, self.y, ang+random.uniform(-0.04,0.04), 470, 12, 3, C_RED, 'enemy', 3))
            self.shoot_cd = 1.6
            play('rifle', 0.25)
        if not self.is_elite and self.mtype != 'rusher':
            self.relocate = random.uniform(0.4, 0.8)
    def draw(self, surf, cam, scan_mode=False, t=0):
        if self.is_boss:
            if self.boss_id == 'bastion':
                self.bastion_draw(surf, cam, scan_mode, t)
            else:
                self.boss_draw(surf, cam, scan_mode, t)
            return
        cx, cy = self.x-cam[0], self.y-cam[1]
        flash_white = self.stg_timer > 0 and int(self.stg_timer*10) % 2
        if self.mtype == 'turret':
            col = C_WHITE if flash_white else (140,80,50)
            pygame.draw.circle(surf, (60,50,40), (int(cx),int(cy)), self.w+4)
            pygame.draw.circle(surf, col, (int(cx),int(cy)), self.w)
            pygame.draw.circle(surf, C_ORANGE, (int(cx),int(cy)), self.w-8, 2)
            bx, by = math.cos(self.ang)*(self.w+16), math.sin(self.ang)*(self.w+16)
            pygame.draw.line(surf, (100,90,80), (cx,cy),(cx+bx,cy+by), 6)
            draw_glow(surf, cx, cy, 20, 'orange', 80)
            if self.ap < self.max_ap:
                bw = self.w*2; bx2, by2 = cx-self.w, cy-self.w-14
                pygame.draw.rect(surf, (40,44,55), (bx2,by2,bw,4))
                pygame.draw.rect(surf, C_RED, (bx2,by2,bw*clamp(self.ap/self.max_ap,0,1),4))
            if scan_mode:
                pygame.draw.circle(surf, C_RED, (int(cx),int(cy)), self.w+6, 2)
            return
        if self.is_elite:
            col = C_WHITE if flash_white else C_ORANGE
            body = [(26,0),(10,-15),(-16,-11),(-16,11),(10,15)]
            pygame.draw.polygon(surf, (120,70,10), rot_pts(cx, cy, body, self.ang))
            pygame.draw.polygon(surf, col, rot_pts(cx, cy, [(x*0.8,y*0.8) for x,y in body], self.ang))
            for s in (-1,1):
                pygame.draw.line(surf, C_YELLOW, rot_pts(cx,cy,[(12,s*6)],self.ang)[0], rot_pts(cx,cy,[(26,s*16)],self.ang)[0], 2)
                pygame.draw.polygon(surf, col, rot_pts(cx,cy,[(-8,s*12),(-18,s*18),(-14,s*8)],self.ang))
            pygame.draw.circle(surf, C_RED if self.enraged else C_YELLOW, (int(cx),int(cy)), 5)
            draw_glow(surf, cx, cy, 26, 'red' if self.enraged else 'yellow', 120)
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
            pygame.draw.polygon(surf, (120,40,100), rot_pts(cx+jx, cy+jy, [(x*1.15,y*1.15) for x,y in [(18*sc,0),(-12*sc,-12*sc),(-6*sc,0),(-12*sc,12*sc)]], self.ang))
            pygame.draw.polygon(surf, col, rot_pts(cx+jx, cy+jy, [(18*sc,0),(-12*sc,-12*sc),(-6*sc,0),(-12*sc,12*sc)], self.ang))
            draw_glow(surf, cx-math.cos(self.ang)*14, cy-math.sin(self.ang)*14, 18, 'magenta', 100)
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
                pygame.draw.rect(surf, (100,35,35), (cx-self.w-2, cy-self.w-2, self.w*2+4, self.w*2+4))
                pygame.draw.rect(surf, col, (cx-self.w, cy-self.w, self.w*2, self.w*2))
                pygame.draw.line(surf, C_YELLOW, (cx,cy), (cx+math.cos(self.ang)*(self.w+14), cy+math.sin(self.ang)*(self.w+14)), 3)
                pygame.draw.circle(surf, C_YELLOW, (int(cx+math.cos(self.ang)*(self.w+14)), int(cy+math.sin(self.ang)*(self.w+14))), 3)
            elif self.mtype == 'mortar':
                pygame.draw.circle(surf, (30,90,60), (int(cx),int(cy)), self.w+2)
                pygame.draw.circle(surf, col, (int(cx),int(cy)), self.w)
                pygame.draw.circle(surf, C_MINT, (int(cx),int(cy)), self.w-6, 2)
            else:
                pygame.draw.rect(surf, (120,20,20), (cx-self.w-2, cy-self.w-2, self.w*2+4, self.w*2+4))
                pygame.draw.rect(surf, col, (cx-self.w, cy-self.w, self.w*2, self.w*2))
                pygame.draw.rect(surf, C_ORANGE, (cx-4, cy-4, 8, 8))
            draw_glow(surf, cx, cy, 16, 'red' if self.mtype!='mortar' else 'mint', 70)
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
            draw_glow(surf, cx, ty, 24, 'yellow', 80)
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
                    play('perfect', 0.8)
                    fx = self.x + math.cos(self.ang)*30; fy = self.y + math.sin(self.ang)*30
                    for _ in range(12): game.particles.add(Particle(fx, fy, C_CYAN, 250))
                    game.rings.append({'x':self.x,'y':self.y,'r':20,'life':0.3,'col':C_CYAN})
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
            play('shotgun', 0.7)
        elif la == 'grenade':
            if self.shotgun_cd > 0: return
            self.shotgun_cd = 1.6
            game.bullets.add(Grenade(self.x+math.cos(self.ang)*28, self.y+math.sin(self.ang)*28, self.ang))
            self.muzzle = 0.05; game.add_shake(3)
            play('grenade', 0.7)
    def fire_rail(self, game):
        game.add_shake(8)
        self.muzzle = 0.1
        play('rail', 0.8)
        dx, dy = math.cos(self.ang), math.sin(self.ang)
        game.beams.append({'x1':self.x+dx*30,'y1':self.y+dy*30,'x2':self.x+dx*900,'y2':self.y+dy*900,'life':0.25,'ml':0.25,'col':C_CYAN,'wide':False})
        for e in game.enemies:
            ex, ey = e.x-self.x, e.y-self.y
            proj = ex*dx + ey*dy
            if proj < 0 or proj > 900: continue
            if abs(ex*dy - ey*dx) < e.w + 12:
                e.take_damage(120, 60, game, C_CYAN, bypass=True, src=(self.x, self.y))
                game.hitstop = max(game.hitstop, 0.05)
        for _ in range(20):
            t2 = random.random()
            game.particles.add(Particle(self.x+dx*(30+870*t2), self.y+dy*(30+870*t2), C_CYAN, 120))
    def update(self, dt, keys, mpos, mbtn, cam, game):
        mx, my = mpos[0]+cam[0], mpos[1]+cam[1]
        self.ang = math.atan2(my-self.y, mx-self.x)
        if self.en <= 0 and not self.stalled:
            self.stalled = True; self.stall_timer = 1.6
            play('deny', 0.5)
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
        self.ghosts = [(x,y,a,t2-dt) for x,y,a,t2 in self.ghosts if t2-dt > 0]
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
                play('pulse' if self.cfg['r_arm']=='pulse' else ('cannon' if self.cfg['r_arm']=='cannon' else 'rifle'), 0.5 if self.cfg['r_arm']=='rifle' else 0.7)
                if self.rifle_knock > 0:
                    self.x -= math.cos(self.ang)*self.rifle_knock*dt*8
                    self.y -= math.sin(self.ang)*self.rifle_knock*dt*8
                    game.add_shake(3)
        if keys[pygame.K_q] and self.missile_cd <= 0 and self.en >= 20 and self.missile_ammo >= 4 and not self.stalled:
            self.missile_cd = 2.5; self.en -= 20; self.missile_ammo -= 4
            for i in range(4):
                game.bullets.add(Missile(self.x, self.y, self.ang+(i-1.5)*0.2, game.enemies, 'player'))
            play('missile', 0.7)
        if keys[pygame.K_e] and self.blade_cd <= 0 and self.en >= 45 and not self.stalled:
            self.blade_cd = 1.2; self.en -= 45; self.blade_timer = 0.2
            game.add_shake(5)
            play('blade', 0.7)
            for e in game.enemies:
                if math.hypot(e.x-self.x, e.y-self.y) < 160:
                    a_e = math.atan2(e.y-self.y, e.x-self.x)
                    diff = abs(a_e - self.ang)
                    if diff > math.pi: diff = 2*math.pi - diff
                    if diff < math.pi/2.5:
                        if e.is_boss and getattr(e, 'boss_blade_anim', 0) > 0:
                            game.add_float("CLASH!", (self.x+e.x)//2, min(self.y,e.y)-60, C_YELLOW, big=True)
                            game.hitstop = max(game.hitstop, 0.12)
                            game.add_shake(8)
                            e.boss_blade_pending = 0
                            game.rings.append({'x':(self.x+e.x)/2,'y':(self.y+e.y)/2,'r':15,'life':0.35,'col':C_YELLOW})
                            for _ in range(20): game.particles.add(Particle((self.x+e.x)/2, (self.y+e.y)/2, C_YELLOW, 300))
                        e.take_damage(200, 100, game, C_CYAN, bypass=True, src=(self.x, self.y))
                        game.hitstop = max(game.hitstop, 0.06)
                        for _ in range(15): game.particles.add(Particle(e.x, e.y, C_CYAN, 250))
        if keys[pygame.K_LSHIFT] and self.qb_cd <= 0 and self.en >= self.qb_cost() and not self.stalled and not self.scanning:
            self.qb_cd = 0.6; self.qb_timer = 0.2; self.en -= self.qb_cost(); self.i_frames = 0.25
            play('boost', 0.7)
        was_ab = self.ab_active
        self.ab_active = keys[pygame.K_SPACE] and self.en > 0 and not self.stalled and not self.scanning
        if self.ab_active and not was_ab:
            play('boost', 0.8)
        if self.ab_active:
            for e in game.enemies:
                if self.rect.colliderect(e.rect):
                    e.take_damage(80*dt, 30*dt, game, C_CYAN, bypass=True, src=(self.x, self.y))
    def draw(self, surf, cam, t=0):
        for x, y, a, gt in self.ghosts:
            draw_mech_shape(surf, x-cam[0], y-cam[1], a, self.cfg, 1.0, ghost=True)
        cx, cy = self.x-cam[0], self.y-cam[1]
        if self.i_frames > 0 and int(self.i_frames*20) % 2: return
        draw_mech_shape(surf, cx, cy, self.ang, self.cfg, 1.0, thrust=self.moving, dim=self.stalled, t=t)
        if self.muzzle > 0:
            gx, gy = self.x+math.cos(self.ang)*36-cam[0], self.y+math.sin(self.ang)*36-cam[1]
            draw_glow(surf, gx, gy, 34, 'yellow', 180)
            pygame.draw.circle(surf, C_YELLOW, (int(gx),int(gy)), random.randint(4,7))
        if self.shield_active:
            pygame.draw.polygon(surf, C_CYAN, rot_pts(cx, cy, [(26,-26),(34,-26),(34,26),(26,26)], self.ang), 3)
            draw_glow(surf, cx+math.cos(self.ang)*30, cy+math.sin(self.ang)*30, 50, 'cyan', 90)
        if self.blade_timer > 0:
            pygame.draw.polygon(surf, C_CYAN, rot_pts(cx, cy, [(0,-30),(120,-60),(120,60),(0,30)], self.ang), 3)
            draw_glow(surf, cx+math.cos(self.ang)*70, cy+math.sin(self.ang)*70, 90, 'cyan', 110)
        if self.stalled:
            surf.blit(F_TINY.render("EN STALL", True, C_RED), (cx-32, cy-40))

class Game:
    def __init__(self):
        self.config = dict(DEFAULT_PARTS)
        self.owned = set(DEFAULT_PARTS.values())
        self.credits = 0
        self.best_rank = {}
        self.rail_unlocked = False
        self.campaign_done = False
        self.mission_idx = 0
        self.garage_sel = 0
        self.garage_idx = {s: 0 for s in SLOT_ORDER}
        self.buy_flash = 0; self.deny_flash = 0
        self.save_flash = 0
        self.dust = [(random.randint(0, MAP_W), random.randint(0, MAP_H), random.uniform(0.3, 1.0)) for _ in range(60)]
        self.motes = [{'x':random.randint(0,W),'y':random.randint(0,H),'vx':random.uniform(-8,8),'vy':random.uniform(-12,-3),'a':random.randint(30,90)} for _ in range(40)]
        self.load()
        self.reset()
    def save(self):
        if WEB: return                 # BrowserFS нет — не пишем на диск
        try:
            data = {'credits':self.credits, 'owned':list(self.owned), 'config':self.config,
                    'best_rank':{str(k):v for k,v in self.best_rank.items()},
                    'rail_unlocked':self.rail_unlocked, 'campaign_done':self.campaign_done}
            with open(SAVE_FILE, 'w') as f: json.dump(data, f)
            self.save_flash = 1.5
        except Exception:
            pass
    def load(self):
        if WEB: return                 # и не читаем — стартуем с дефолтом
        try:
            with open(SAVE_FILE) as f: d = json.load(f)
            self.credits = d.get('credits', 0)
            self.owned = set(d.get('owned', list(DEFAULT_PARTS.values())))
            cfg = d.get('config', dict(DEFAULT_PARTS))
            for slot in SLOT_ORDER:
                if cfg.get(slot) not in PARTS[slot]:
                    cfg[slot] = DEFAULT_PARTS[slot]
            self.config = cfg
            self.best_rank = {int(k):v for k,v in d.get('best_rank', {}).items()}
            self.rail_unlocked = d.get('rail_unlocked', False)
            self.campaign_done = d.get('campaign_done', False)
        except Exception:
            pass
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
        self.rings = []
        self.zones = []
        if m['boss']:
            self.banner = "WAVE 1 INBOUND"
        elif m['targets'] > 0:
            self.banner = "LOCATE PRIORITY TARGETS"
        else:
            self.banner = "BREACH THE PERIMETER"
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
            play('stagger', 0.7)
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
            play('hurt', 0.6)
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
        m = MISSIONS[self.mission_idx]
        w = m['waves'][idx]
        for _ in range(w.get('turret', 0)):
            self.enemies.add(Enemy(*self.rand_far(), force_type='turret'))
        for _ in range(w.get('mt', 0)):
            self.enemies.add(Enemy(*self.rand_far()))
        for _ in range(w.get('elite', 0)):
            self.enemies.add(Enemy(*self.rand_far(), is_elite=True))
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
        if self.mission_idx == 2 and not self.campaign_done:
            self.campaign_done = True
            self.owned.add('legend')
        self.save()
        play('victory', 0.8)
    def finish_defeat(self):
        self.earned = int(MISSIONS[self.mission_idx]['reward']*0.2)
        self.credits += self.earned
        self.save()
        play('defeat', 0.8)
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
        std = [e for e in self.enemies if not e.is_boss and e.mtype not in ('rusher','turret') and not e.is_elite and not e.is_target and e.guard_of is None]
        for i, e in enumerate(std):
            e.slot_ang = (i/max(1,len(std)))*2*math.pi + self.flank_phase
        rushers = [e for e in self.enemies if e.mtype == 'rusher']
        for i, r in enumerate(rushers):
            r.hunt_ang = (i/max(1,len(rushers)))*2*math.pi + self.flank_phase*1.6
        self.flank_phase += dt*0.12
        if m['targets'] > 0:
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
                play('warning', 0.6)
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
        elif m['boss']:
            waves = m['waves']
            if not self.boss_spawned:
                if len(self.enemies) == 0:
                    if not self.wave_cleared:
                        self.wave_cleared = True; self.wave_delay = 1.6
                        if self.wave_idx >= 0:
                            self.add_float("WAVE CLEARED", self.player.x, self.player.y-70, C_GREEN, big=True)
                            self.player.en = min(self.player.max_en, self.player.en + 30)
                            self.add_float("+30 EN", self.player.x, self.player.y-100, C_BLUE)
                            play('confirm', 0.6)
                    self.wave_delay -= dt
                    if self.wave_delay <= 0:
                        self.wave_cleared = False
                        if self.wave_idx + 1 < len(waves):
                            self.wave_idx += 1
                            self.spawn_wave(self.wave_idx)
                            el = waves[self.wave_idx].get('elite', 0)
                            self.banner = f"WAVE {self.wave_idx+1} INBOUND" + (" // ELITE COMMANDER DETECTED" if el else "")
                            self.banner_timer = 2.2
                        else:
                            b = Enemy(MAP_W/2+500, MAP_H/2, is_boss=True, boss_id=m['boss_id'])
                            self.enemies.add(b)
                            self.boss_spawned = True
                            self.banner = "WARNING: " + ("FORTRESS AC BASTION" if m['boss_id']=='bastion' else "RIVAL AC VINDICTA")
                            self.banner_timer = 3.0
                            self.bosscard = 2.5
                            self.slowmo_timer = max(self.slowmo_timer, 0.6)
                            self.add_shake(8)
                            play('warning', 0.9)
                else:
                    self.wave_cleared = False
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
        for rg in self.rings: rg['life'] -= dt; rg['r'] += 300*dt
        self.rings = [rg for rg in self.rings if rg['life'] > 0]
        for z in list(self.zones):
            if z.update(dt):
                d = math.hypot(self.player.x-z.x, self.player.y-z.y)
                if d < z.radius:
                    self.hurt(z.dmg, z.x, z.y)
                for _ in range(15): self.particles.add(Particle(z.x, z.y, C_ORANGE, 250))
                self.rings.append({'x':z.x,'y':z.y,'r':10,'life':0.4,'col':C_ORANGE})
                self.add_shake(6)
                play('explosion', 0.5)
                self.zones.remove(z)
        self.player.update(dt, keys, mpos, mbtn, self.cam, self)
        for e in self.enemies:
            if e.is_elite or (e.mtype in ('striker','gunner','mortar') and e.guard_of is None):
                e.try_dodge(self.bullets)
        self.enemies.update(enemy_move_dt, self.player, self.bullets, self)
        boss = next((e for e in self.enemies if e.is_boss), None)
        if boss and getattr(boss, 'boss_ab', 0) > 0 and boss.rect.colliderect(self.player.rect):
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
                    self.rings.append({'x':b.x,'y':b.y,'r':10,'life':0.35,'col':C_MINT})
                    self.add_shake(5)
                    play('explosion', 0.4)
                    if d < 110: self.hurt(24, b.x, b.y)
                    b.kill()
            elif isinstance(b, Grenade):
                near = any(math.hypot(e.x-b.x, e.y-b.y) < e.w+20 for e in self.enemies)
                if b.fuse <= 0 or near:
                    for e in self.enemies:
                        if math.hypot(e.x-b.x, e.y-b.y) < 120:
                            e.take_damage(45, 30, self, C_ORANGE, src=(b.x, b.y))
                    for _ in range(20): self.particles.add(Particle(b.x, b.y, C_ORANGE, 280))
                    self.rings.append({'x':b.x,'y':b.y,'r':10,'life':0.35,'col':C_ORANGE})
                    self.add_shake(6)
                    play('explosion', 0.6)
                    b.kill()
        self.particles.update(dt)
        self.dmg_nums.update(dt)
        for b in list(self.bullets):
            if b.owner == 'player':
                for e in self.enemies:
                    if b.rect.colliderect(e.rect):
                        mult = clamp(1.0 - b.dist/380, 0.3, 1.0) if b.falloff else 1.0
                        e.take_damage(b.dmg*mult, b.stag, self, b.col, src=(b.x, b.y))
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
        if m['targets'] > 0:
            if self.m2_spawned and self.targets_remaining == 0:
                self.finish_victory(); return 'VICTORY'
        elif m['boss']:
            if self.boss_spawned and not any(e.is_boss for e in self.enemies):
                self.finish_victory(); return 'VICTORY'
        return 'PLAYING'
    def compute_rank(self):
        score = 10000 - self.stats['time']*60 - self.stats['dmg_taken']*12 + self.stats['staggers']*600
        self.final_rank = 'S' if score >= 7500 else 'A' if score >= 5500 else 'B' if score >= 3500 else 'C'
    def draw(self, surf, t=0):
        sx = random.uniform(-self.shake, self.shake) if self.shake else 0
        sy = random.uniform(-self.shake, self.shake) if self.shake else 0
        cam = [self.cam[0]+sx, self.cam[1]+sy]
        m = MISSIONS[self.mission_idx]
        surf.fill(C_BG)
        for step, par, col in ((200,0.5,(16,19,28)),(100,1.0,C_GRID)):
            ox = (-cam[0]*par) % step; oy = (-cam[1]*par) % step
            for x in range(int(ox), W, step): pygame.draw.line(surf, col, (x,0),(x,H))
            for y in range(int(oy), H, step): pygame.draw.line(surf, col, (0,y),(W,y))
        for dx, dy, sp in self.dust:
            pygame.draw.circle(surf, (55,65,85), (int((dx-cam[0]*sp)%W), int((dy-cam[1]*sp)%H)), 1)
        pygame.draw.rect(surf, C_RED, (-cam[0], -cam[1], MAP_W, MAP_H), 4)
        ov = pygame.Surface((W,H), pygame.SRCALPHA)
        drew = False
        for e in self.enemies:
            g = getattr(e, 'guard_of', None)
            if g is not None and g.alive():
                ex, ey = e.x-cam[0], e.y-cam[1]
                gx2, gy2 = g.x-cam[0], g.y-cam[1]
                pygame.draw.line(ov, (120,255,180,55), (ex,ey),(gx2,gy2), 1)
                pygame.draw.circle(ov, (120,255,180,110), (int(gx2),int(gy2)), g.w+8, 2)
                drew = True
        elites = [e for e in self.enemies if e.is_elite]
        for el in elites:
            ex, ey = el.x-cam[0], el.y-cam[1]
            pygame.draw.circle(ov, (255,140,0,70), (int(ex),int(ey)), el.w+14+int(3*math.sin(t*6)), 2)
            for o in self.enemies:
                if o is el or o.is_elite or o.is_boss: continue
                if math.hypot(o.x-el.x, o.y-el.y) < 450:
                    pygame.draw.line(ov, (255,140,0,45), (ex,ey), (o.x-cam[0],o.y-cam[1]), 1)
            drew = True
        if drew: surf.blit(ov, (0,0))
        for z in self.zones: z.draw(surf, cam)
        for p in self.particles: p.draw(surf, cam)
        for b in self.bullets: b.draw(surf, cam)
        for bm in self.beams:
            a = clamp(bm['life']/bm.get('ml',0.25), 0, 1)
            bcol = bm.get('col', C_CYAN)
            wide = bm.get('wide', False)
            gname = 'red' if bcol==C_RED else 'cyan'
            draw_glow(surf, (bm['x1']+bm['x2'])/2-cam[0], (bm['y1']+bm['y2'])/2-cam[1], 60, gname, int(120*a))
            pygame.draw.line(surf, bcol, (bm['x1']-cam[0],bm['y1']-cam[1]), (bm['x2']-cam[0],bm['y2']-cam[1]), (int(14*a)+2) if wide else (int(6*a)+1))
            pygame.draw.line(surf, C_WHITE, (bm['x1']-cam[0],bm['y1']-cam[1]), (bm['x2']-cam[0],bm['y2']-cam[1]), int(6*a) if wide else max(1,int(2*a)))
        for rg in self.rings:
            a = clamp(rg['life']/0.4, 0, 1)
            pygame.draw.circle(surf, rg['col'], (int(rg['x']-cam[0]), int(rg['y']-cam[1])), int(rg['r']), max(1,int(4*a)))
        for e in self.enemies: e.draw(surf, cam, self.scan_mode, t)
        self.player.draw(surf, cam, t)
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
            r = nearest.w + 12 + int(3*math.sin(t*6))
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
            pulse = (math.sin(t*8)+1)/2
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
            if m['boss_id'] == 'bastion':
                t1 = F_BIG.render("BASTION", True, C_YELLOW)
                t2 = F_SM.render("FORTRESS AC // IMMOVABLE WALL", True, C_RED)
            else:
                t1 = F_BIG.render("VINDICTA", True, C_YELLOW)
                t2 = F_SM.render("HEAVY CAVALRY // ACE DUELIST", True, C_RED)
            t1.set_alpha(int(255*a)); t2.set_alpha(int(255*a))
            surf.blit(t1, (W//2-t1.get_width()//2, cy0-30))
            surf.blit(t2, (W//2-t2.get_width()//2, cy0+30))
        pygame.draw.rect(surf, (15,17,24), (20,20,250,92))
        pygame.draw.rect(surf, C_CYAN, (20,20,3,92))
        surf.blit(F_TINY.render(m['code'] + " // " + m['name'], True, C_CYAN), (32, 26))
        if m['boss'] and self.boss_spawned:
            objtxt = "DEFEAT " + ("FORTRESS AC 'BASTION'" if m['boss_id']=='bastion' else "RIVAL AC 'VINDICTA'")
        else:
            objtxt = m['obj'][:34]
        surf.blit(F_SM.render("OBJ: " + objtxt, True, C_WHITE), (32, 46))
        if m['targets'] > 0:
            guarded = sum(1 for e in self.enemies if e.is_target and any(o.guard_of is e for o in self.enemies))
            surf.blit(F_TINY.render(f"TARGETS: {self.mission_targets - self.targets_remaining}/{self.mission_targets}   GUARDED: {guarded}   HOSTILES: {len(self.enemies)}", True, C_GOLD), (32, 72))
        else:
            surf.blit(F_TINY.render(f"HOSTILES: {len(self.enemies)}", True, C_YELLOW), (32, 72))
        if m['boss'] and not self.boss_spawned:
            surf.blit(F_TINY.render(f"WAVE {self.wave_idx+1}/{len(m['waves'])}", True, C_DIM), (140, 72))
            if len(self.enemies) == 0 and self.wave_idx + 1 < len(m['waves']):
                if int(t*3) % 2:
                    nxt = m['waves'][self.wave_idx+1]
                    surf.blit(F_TINY.render(f"INCOMING: {nxt.get('mt',0)}x MT  {nxt.get('turret',0)}x TURRET  {nxt.get('elite',0)}x ELITE", True, C_ORANGE), (32, 92))
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
        en_col = (255,80,80) if self.player.stalled else ((255,140,60) if low_en and int(t*4)%2 else C_BLUE)
        pygame.draw.rect(surf, en_col, (W-322,H-43,300*(self.player.en/self.player.max_en),20))
        surf.blit(F_SM.render("EN", True, C_WHITE), (W-315, H-70))
        if low_en and int(t*3) % 2:
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
            if boss.boss_id == 'bastion':
                if boss.bastion_shield:
                    pygame.draw.rect(surf, (35,38,48), (W//2-bw//2-2,51,bw+4,6))
                    pygame.draw.rect(surf, C_CYAN, (W//2-bw//2,52,bw*clamp(boss.stagger/boss.max_stagger,0,1),4))
                name = "BASTION // ENRAGED" if boss.bastion_enraged else "BASTION // FRONT SHIELD"
                surf.blit(F_SM.render(name, True, C_YELLOW), (W//2-bw//2, 60))
            else:
                pygame.draw.rect(surf, (35,38,48), (W//2-bw//2-2,51,bw+4,6))
                ben_col = (255,80,80) if boss.boss_en < 20 and int(t*5)%2 else C_BLUE
                pygame.draw.rect(surf, ben_col, (W//2-bw//2,52,bw*clamp(boss.boss_en/boss.boss_en_max,0,1),4))
                dsl = {'circle':'CIRCLE','blade_windup':'WINDUP','blade_dash':'BLADE DASH','recover':'RECOVER','reposition':'REPOSITION'}.get(boss.duel_state,'')
                surf.blit(F_SM.render("VINDICTA // " + ("LIMITER " if boss.phase2 else "") + dsl, True, C_YELLOW), (W//2-bw//2, 60))
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
                elif e.mtype == 'turret': col = C_ORANGE
                else: col = C_RED
                pygame.draw.circle(surf, col, (int(rx+math.cos(ang)*scale), int(ry+math.sin(ang)*scale)), 4 if e.is_boss else (3 if (e.is_elite or e.is_target or e.mtype=='turret') else 2))
        if self.show_fps:
            surf.blit(F_TINY.render(f"{clock.get_fps():.0f} FPS", True, C_GREEN), (W-70, 200))
        surf.blit(F_TINY.render(VERSION + ("  [MUTED]" if MUTED else ""), True, C_DIM), (W-160, H-20))
        surf.blit(VIG, (0,0)); surf.blit(SCANLINES, (0,0))
    def draw_help(self, surf):
        ov = pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,0,0,160))
        surf.blit(ov, (0,0))
        surf.blit(F_MED.render("CONTROLS", True, C_CYAN), (W//2-90, 110))
        lines = [
            "WASD ............ MOVE", "MOUSE ........... AIM",
            "LMB ............. R-ARM FIRE / CHARGE RAIL", "RMB ............. L-ARM (shotgun/grenade/shield)",
            "Q ............... MISSILES (4)", "E ............... ENERGY BLADE (clashes!)",
            "SHIFT ........... QUICK BOOST (i-frames)", "SPACE ........... ASSAULT BOOST (ram)",
            "C / TAB ......... SCAN MODE", "RMB (late) ...... PERFECT GUARD w/ shield",
            "F8 .............. MUTE", "ESC ............. PAUSE",
            "R ............... QUICK RESTART", "H ............... TOGGLE HELP",
        ]
        for i, ln in enumerate(lines):
            surf.blit(F_SM.render(ln, True, C_WHITE), (W//2-260, 165 + i*32))

def draw_title(surf, t, motes, campaign_done):
    surf.fill(C_BG)
    off = (t*40) % 100
    for x in range(int(-off), W, 100): pygame.draw.line(surf, C_GRID, (x,0),(x,H))
    for y in range(0, H, 100): pygame.draw.line(surf, C_GRID, (0,y),(W,y))
    for mo in motes:
        pygame.draw.circle(surf, (80,120,160), (int(mo['x']), int(mo['y'])), 1)
    mx, my = W//2, H//2 + 150
    draw_mech_shape(surf, mx, my, -math.pi/2, DEFAULT_PARTS, 6.0, body_col=(30,38,55), thrust=True, t=t)
    draw_glow(surf, mx, my-40, 200, 'cyan', 40)
    ex, ey, er = W//2, 150, 55
    hexpts = [(ex + er*math.cos(math.pi/6 + i*math.pi/3), ey + er*math.sin(math.pi/6 + i*math.pi/3)) for i in range(6)]
    pygame.draw.polygon(surf, (20,30,45), hexpts)
    pygame.draw.polygon(surf, C_CYAN, hexpts, 3)
    pygame.draw.polygon(surf, C_RED, [(ex, ey-28),(ex+24, ey+16),(ex-24, ey+16)])
    ttl = F_TITLE.render("ARMORED CORE", True, C_WHITE)
    surf.blit(ttl, (W//2 - ttl.get_width()//2, 230))
    sub = F_MED.render("2 D   //   T R U E   D U E L I S T", True, C_CYAN)
    surf.blit(sub, (W//2 - sub.get_width()//2, 340))
    pygame.draw.line(surf, C_CYAN, (W//2-320, 395),(W//2+320, 395), 2)
    if campaign_done:
        cd = F_SM.render("CAMPAIGN COMPLETE // LEGENDARY PILOT", True, C_GOLD)
        surf.blit(cd, (W//2 - cd.get_width()//2, 405))
    if int(t*2) % 2:
        pr = F_MED.render("PRESS SPACE TO ENTER GARAGE", True, C_YELLOW)
        surf.blit(pr, (W//2 - pr.get_width()//2, 440))
    surf.blit(F_TINY.render("SYNTHESIZED AUDIO // PROGRESS AUTO-SAVED // F8 MUTE", True, C_DIM), (W//2-240, 490))
    surf.blit(F_TINY.render(VERSION, True, C_DIM), (W//2-60, H-40))
    surf.blit(VIG, (0,0)); surf.blit(SCANLINES, (0,0))

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
    if game.save_flash > 0:
        sv = F_TINY.render("PROGRESS SAVED", True, C_GREEN)
        sv.set_alpha(clamp(int(255*game.save_flash), 0, 255))
        surf.blit(sv, (W-60-sv.get_width(), 115))
    px, py = 300, 400
    pygame.draw.circle(surf, (20,40,60), (px, py+90), 70)
    pygame.draw.circle(surf, C_BLUE, (px, py+90), 70, 2)
    draw_glow(surf, px, py+40, 160, 'cyan', 50)
    draw_mech_shape(surf, px, py+math.sin(t*2)*6, -math.pi/2, game.config, 3.0, thrust=True, t=t)
    slot = SLOT_ORDER[game.garage_sel]
    parts = list(PARTS[slot].keys())
    preview_cfg = dict(game.config)
    preview_cfg[slot] = parts[game.garage_idx[slot]]
    st = loadout_preview(preview_cfg)
    stats = [('AP', st['ap']/600), ('SPEED', st['spd']/420), ('EN', st['en']/180),
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
        locked = (p.get('unlock') and not game.rail_unlocked) or (p.get('unlock_campaign') and not game.campaign_done)
        owned = cpid in game.owned
        equipped = game.config[sl] == cpid
        y = 210 + i*95
        col = C_YELLOW if active else C_WHITE
        marker = ">>" if active else "  "
        pulse = int(4*math.sin(t*6)) if active else 0
        surf.blit(F_TINY.render(SLOT_LABEL[sl], True, C_DIM), (bx+pulse, y))
        name_col = C_GOLD if p.get('unlock_campaign') and not locked else (C_DIM if locked else col)
        surf.blit(F_MED.render(f"{marker} {p['n']}", True, name_col), (bx+pulse, y+18))
        surf.blit(F_TINY.render(p['desc'] + f"   [{p['w']}kg]", True, (140,150,170)), (bx+40, y+52))
        if locked:
            lock_txt = "LOCKED - complete CAMPAIGN" if p.get('unlock_campaign') else "LOCKED - complete MISSION 02"
            surf.blit(F_TINY.render(lock_txt, True, C_RED), (bx+400, y+22))
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
    surf.blit(F_BIG.render("MISSION SELECT", True, C_WHITE), (W//2-330, 50))
    for i, m in enumerate(MISSIONS):
        locked = (i > 0 and game.best_rank.get(i-1) is None)
        active = (i == sel)
        y = 150 + i*175
        col = C_YELLOW if active else (C_DIM if locked else C_WHITE)
        pygame.draw.rect(surf, (18,20,28), (W//2-420, y, 840, 150))
        pygame.draw.rect(surf, col, (W//2-420, y, 840, 150), 3 if active else 1)
        surf.blit(F_MED.render(m['code'] + "  " + m['name'], True, col), (W//2-390, y+15))
        surf.blit(F_SM.render(m['obj'], True, (160,170,190) if not locked else C_DIM), (W//2-390, y+55))
        surf.blit(F_TINY.render(f"REWARD: {m['reward']} CR (rank bonus x2.0 S)", True, C_GOLD if not locked else C_DIM), (W//2-390, y+92))
        best = game.best_rank.get(i)
        if best:
            surf.blit(F_TINY.render(f"BEST RANK: {best}", True, C_CYAN), (W//2-390, y+115))
        if locked:
            surf.blit(F_MED.render("LOCKED - complete previous mission", True, C_RED), (W//2+40, y+55))
        elif active:
            surf.blit(F_TINY.render(">> ENTER: BRIEFING", True, C_YELLOW), (W//2+220, y+115))
    surf.blit(F_SM.render("UP/DOWN select   ENTER briefing   ESC garage", True, C_BLUE), (W//2-320, H-40))
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
            surf.blit(F_SM.render("> " + ln, True, C_WHITE), (100, 290 + i*42))
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
    surf.blit(F_TINY.render("ESC resume   R restart   H help   F8 mute", True, C_DIM), (W//2-200, 520))

def main():
    try:
        print('[AC2D] boot  WEB =', WEB, ' pygame', pygame.ver)
        build_audio();  print('[AC2D] audio ok')
        build_glows();  print('[AC2D] glows ok')
        state = 'START'
        game = Game();  print('[AC2D] game constructed')
        pause_sel = 0
        mission_sel = 0
        brief_t = 0.0
        running = True
        gt = 0.0
        boot_played = False
        music_started = False
        print('[AC2D] entering main loop')
        while running:
            dt = clock.tick(60) / 1000.0
            gt += dt
            if game.save_flash > 0: game.save_flash -= dt
            if state == 'START' and not boot_played:
                play('boot', 0.9)
                boot_played = True
            if state == 'PLAYING' and not music_started:
                start_music()
                music_started = True
            if state != 'PLAYING' and music_started:
                if MUSIC: MUSIC.stop()
                music_started = False
            if state == 'START':
                for mo in game.motes:
                    mo['x'] += mo['vx']*dt; mo['y'] += mo['vy']*dt
                    if mo['y'] < -5: mo['y'] = H+5; mo['x'] = random.randint(0, W)
                    if mo['x'] < -5: mo['x'] = W+5
                    if mo['x'] > W+5: mo['x'] = -5
            if game.buy_flash > 0: game.buy_flash -= dt
            if game.deny_flash > 0: game.deny_flash -= dt
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            mouse_btn = pygame.mouse.get_pressed()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    game.save()
                    running = False
                if _WIN_EVENT is not None and e.type == _WIN_EVENT and getattr(e,'event',None) == _WIN_FOCUS_LOST and state == 'PLAYING':
                    state = 'PAUSED'; pause_sel = 0
                elif _ACTIVE_EVENT is not None and e.type == _ACTIVE_EVENT and getattr(e,'gain',1) == 0 and state == 'PLAYING':
                    state = 'PAUSED'; pause_sel = 0
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_F8:
                        MUTED = not MUTED
                        if MUTED and MUSIC: MUSIC.stop()
                        elif not MUTED and state == 'PLAYING': start_music()
                    if state == 'START' and e.key == pygame.K_SPACE:
                        state = 'GARAGE'
                        play('confirm', 0.7)
                    elif state == 'GARAGE':
                        slot = SLOT_ORDER[game.garage_sel]
                        parts = list(PARTS[slot].keys())
                        if e.key == pygame.K_UP:
                            game.garage_sel = (game.garage_sel-1) % 4; play('ui', 0.5)
                        elif e.key == pygame.K_DOWN:
                            game.garage_sel = (game.garage_sel+1) % 4; play('ui', 0.5)
                        elif e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            ni = (game.garage_idx[slot] + (1 if e.key == pygame.K_RIGHT else -1)) % len(parts)
                            game.garage_idx[slot] = ni
                            npid = parts[ni]
                            np = PARTS[slot][npid]
                            lk = (np.get('unlock') and not game.rail_unlocked) or (np.get('unlock_campaign') and not game.campaign_done)
                            if npid in game.owned and not lk:
                                game.config[slot] = npid
                            play('ui', 0.5)
                        elif e.key == pygame.K_RETURN:
                            pid = parts[game.garage_idx[slot]]
                            p = PARTS[slot][pid]
                            locked = (p.get('unlock') and not game.rail_unlocked) or (p.get('unlock_campaign') and not game.campaign_done)
                            if pid not in game.owned and not locked:
                                if game.credits >= p['cost']:
                                    game.credits -= p['cost']
                                    game.owned.add(pid)
                                    game.config[slot] = pid
                                    game.buy_flash = 1.0
                                    game.save()
                                    play('confirm', 0.8)
                                else:
                                    game.deny_flash = 1.0
                                    play('deny', 0.7)
                            elif pid in game.owned:
                                game.config[slot] = pid
                                play('confirm', 0.6)
                        elif e.key == pygame.K_m:
                            state = 'MISSIONS'; mission_sel = 0
                            play('confirm', 0.7)
                    elif state == 'MISSIONS':
                        if e.key == pygame.K_UP:
                            mission_sel = (mission_sel-1) % len(MISSIONS); play('ui', 0.5)
                        elif e.key == pygame.K_DOWN:
                            mission_sel = (mission_sel+1) % len(MISSIONS); play('ui', 0.5)
                        elif e.key == pygame.K_ESCAPE:
                            state = 'GARAGE'; play('ui', 0.5)
                        elif e.key == pygame.K_RETURN:
                            if not (mission_sel > 0 and game.best_rank.get(mission_sel-1) is None):
                                game.mission_idx = mission_sel
                                state = 'BRIEFING'; brief_t = 0.0
                                play('confirm', 0.8)
                            else:
                                play('deny', 0.7)
                    elif state == 'BRIEFING':
                        if e.key == pygame.K_RETURN:
                            game.reset(); state = 'PLAYING'
                            play('warning', 0.5)
                        elif e.key == pygame.K_ESCAPE:
                            state = 'MISSIONS'; play('ui', 0.5)
                    elif state == 'PLAYING':
                        if e.key == pygame.K_ESCAPE:
                            state = 'PAUSED'; pause_sel = 0; play('ui', 0.5)
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
                            play('ui', 0.5)
                    elif state == 'PAUSED':
                        if e.key == pygame.K_ESCAPE:
                            state = 'PLAYING'; play('ui', 0.5)
                        elif e.key in (pygame.K_UP, pygame.K_w):
                            pause_sel = (pause_sel-1) % 3; play('ui', 0.5)
                        elif e.key in (pygame.K_DOWN, pygame.K_s):
                            pause_sel = (pause_sel+1) % 3; play('ui', 0.5)
                        elif e.key == pygame.K_r:
                            game.reset(); state = 'PLAYING'
                        elif e.key == pygame.K_h:
                            game.show_help = not game.show_help
                        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if pause_sel == 0: state = 'PLAYING'
                            elif pause_sel == 1: game.reset(); state = 'PLAYING'
                            else: state = 'GARAGE'
                            play('confirm', 0.6)
                    elif state in ('VICTORY', 'GAME_OVER'):
                        if e.key == pygame.K_SPACE:
                            state = 'GARAGE'; play('ui', 0.6)
                        elif e.key == pygame.K_r:
                            game.reset(); state = 'PLAYING'
                if state == 'PLAYING' and e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    game.player.fire_larm(game)
            if state == 'BRIEFING':
                brief_t += dt
            screen.fill(C_BG)
            if state == 'START':
                draw_title(screen, gt, game.motes, game.campaign_done)
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
                game.draw(screen, gt)
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
                screen.blit(F_BIG.render("MISSION COMPLETE", True, C_GREEN), (W//2-420, H//2-220))
                rank_col = {'S':C_YELLOW,'A':C_GREEN,'B':C_BLUE,'C':C_RED}.get(game.final_rank, C_WHITE)
                screen.blit(F_HUGE.render(game.final_rank or "?", True, rank_col), (W//2-40, H//2-140))
                st = game.stats
                screen.blit(F_SM.render(f"TIME {st['time']:.1f}s   DMG TAKEN {int(st['dmg_taken'])}   STAGGERS {st['staggers']}", True, C_WHITE), (W//2-300, H//2+40))
                screen.blit(F_MED.render(f"EARNED: +{game.earned} CR", True, C_GOLD), (W//2-180, H//2+85))
                if game.mission_idx == 1 and game.rail_unlocked:
                    screen.blit(F_SM.render("UNLOCKED: RAILGUN (garage)", True, C_CYAN), (W//2-200, H//2+130))
                if game.mission_idx == 2 and game.campaign_done:
                    screen.blit(F_BIG.render("CAMPAIGN COMPLETE", True, C_GOLD), (W//2-420, H//2+130))
                    screen.blit(F_SM.render("UNLOCKED: OVERDRIVE CORE (garage)", True, C_CYAN), (W//2-240, H//2+180))
                screen.blit(F_SM.render("R: RETRY   |   SPACE: GARAGE", True, C_YELLOW), (W//2-200, H//2+225))
                screen.blit(VIG, (0,0)); screen.blit(SCANLINES, (0,0))
            elif state == 'GAME_OVER':
                screen.blit(F_BIG.render("MISSION FAILED", True, C_RED), (W//2-380, H//2-100))
                screen.blit(F_SM.render(f"SALVAGE: +{game.earned} CR", True, C_GOLD), (W//2-160, H//2))
                screen.blit(F_SM.render("R: RETRY   |   SPACE: GARAGE", True, C_YELLOW), (W//2-200, H//2+60))
                screen.blit(VIG, (0,0)); screen.blit(SCANLINES, (0,0))
            pygame.display.flip()
        pygame.quit()
        sys.exit()
    except Exception:
        traceback.print_exc()
        try:
            screen.fill((10,0,0))
            tb = traceback.format_exc().splitlines()[-6:]
            y = 40
            for ln in tb:
                screen.blit(pygame.font.Font(None, 22).render(ln[:110], True, (255,90,90)), (20, y))
                y += 26
            pygame.display.flip()
        except Exception:
            pass
        import time; time.sleep(30)

if __name__ == '__main__':
    main()