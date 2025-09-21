# Planet Guardian 3D 

# menu, controls
# player movement 
# cam control
# cheat mode
# game over and restart
# aliens - follow player 
# aliens - shoot player
# meteos - crashes on planet
# player shoot to kill enemies
# only aliens drop items
# planet shield
# nova
# ship life & planet life
# health & nova restore from drops
# 3D/free cam
# player can collide with enemies to kill costing 1 life
# score
# explosion effect
# pause game


from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math, random, time, sys


# config
WIN_W, WIN_H = 1200, 800
ASPECT = WIN_W / WIN_H
FOVY = 70.0

# planet/player
PLANET_R = 120.0
PLAYER_INIT_R = 240.0
PLAYER_SIZE = 14.0
BULLET_SPEED = 220.0  
BULLET_LIFE = 3     
BULLET_AS_POINTS = True
POINT_SIZE = 5

# enemies
NUM_METEORS = 5
NUM_ALIENS = 5
METEOR_SPEED = 60.0
ALIEN_BASE_SPEED = 40.0

# shield
SHIELD_MAX = 6.0      
SHIELD_COOLDOWN = 10.0

# alien weapons / player-planet lives
ALIEN_BULLET_SPEED = 100.0
ALIEN_FIRE_COOLDOWN = 2  
SHIP_LIFE_MAX = 50
PLANET_LIFE_MAX = 5

# pickups from aliens
PICKUP_LIFE_SHIP = 5   
PICKUP_LIFE_PLANET = 1 
PICKUP_EXPIRE_SECS = 12.0

# nova powerup - only from aliens
NOVA_MAX_CHARGES = 3
NOVA_RESPAWN_MIN = 12.0
NOVA_RESPAWN_MAX = 20.0
NOVA_LIFE_SECS   = 12.0


# state

# enemy bullets & alien/meteor drops : list of dicts
enemy_bullets = []  # {pos:[x,y,z], vel:[vx,vy,vz]}
pickups = []        # {pos:[x,y,0], type:'nova'|'ship'|'planet'}

# player orbit params
orbit_theta = 0.0    # angle around +Z axis (planet at origin)
orbit_r = PLAYER_INIT_R
planet_life = PLANET_LIFE_MAX
ship_life = SHIP_LIFE_MAX
player_score = 0

# bullets: list of dicts
bullets = []  # {pos:[x,y,z], vel:[vx,vy,vz]}

# meteors / aliens
meteors = []  # {pos:[x,y,z], vel:[vx,vy,vz]}
aliens = []   # {pos:[x,y,z], dir_theta:float, radius:float, speed:float, shoot_t:float}

# explosions: {pos:[x,y,z], r:float, born:t, life:float}
explosions = []

# shield state
shield_active = False
shield_time_left = 0.0
shield_last_used = -999.0

# nova powerup state
nova_charges = NOVA_MAX_CHARGES
nova_pickup_active = False
nova_pickup_pos = [0.0, 0.0, 0.0]
nova_spawn_at = 0.0
nova_expires_at = 0.0

# camera
free_cam = False   # False = third-person follow; True = free/orbit cam
cam_yaw = 45.0
cam_pitch = 25.0
cam_dist = 520.0

# cheat
cheat = False
cheat_fire_timer = 0.0

# timing
_last_time = time.time()

# flags / game state
paused = False
GAME_MENU = 0
GAME_CONTROLS = 1
GAME_PLAYING = 2
GAME_OVER = 3

game_state = GAME_MENU  # start at Main Menu


# utility

def clamp(x, lo, hi):
    return lo if x < lo else (hi if x > hi else x)


def length3(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])


def norm3(v):
    L = length3(v)
    if L == 0: return [0.0, 0.0, 0.0]
    return [v[0]/L, v[1]/L, v[2]/L]


def now():
    return time.time()

# Scene helpers

def player_pos():
    # player orbits planet on XY plane at radius orbit_r, angle orbit_theta
    x = orbit_r * math.cos(math.radians(orbit_theta))
    y = orbit_r * math.sin(math.radians(orbit_theta))
    z = 0.0
    return [x, y, z]


def player_tangent_dir():
    # tangent direction (perpendicular to radius): clockwise along orbit
    rad = math.radians(orbit_theta)
    tx = -math.sin(rad)
    ty =  math.cos(rad)
    tz = 0.0
    return [tx, ty, tz]


def spawn_meteor():
    # Spawn on an XY ring (z=0) 
    R = 900.0
    th = random.uniform(0, 2*math.pi)
    x = R*math.cos(th)
    y = R*math.sin(th)
    z = 0.0
    dir_to_origin = norm3([-x, -y, -z])  # z=0 - velocity lies in the XY plane
    v = [dir_to_origin[0]*METEOR_SPEED, dir_to_origin[1]*METEOR_SPEED, dir_to_origin[2]*METEOR_SPEED]
    return {"pos":[x,y,z], "vel":v}


def spawn_alien():
    # Spawn aliens in the same shooting plane (z=0) so they are always hittable
    r = random.uniform(420.0, 640.0)
    a = random.uniform(0, 360)
    x = r * math.cos(math.radians(a))
    y = r * math.sin(math.radians(a))
    z = 0.0  # keep on XY plane
    return {"pos": [x, y, z], "dir_theta": random.uniform(0, 360), "radius": r, "speed": ALIEN_BASE_SPEED, "shoot_t": random.uniform(0, ALIEN_FIRE_COOLDOWN)}


# Drawing

def draw_text_2d(x, y, s, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()
    glColor3f(0.95, 0.95, 1.0)
    glRasterPos2f(x, y)
    for ch in s: glutBitmapCharacter(font, ord(ch))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)


def draw_sphere(r, color=(1,1,1), slices=24, stacks=24, wire=False, alpha=1.0):
    glColor4f(color[0], color[1], color[2], alpha)
    quad = gluNewQuadric()
    if wire:
        gluQuadricDrawStyle(quad, GLU_LINE)
    gluSphere(quad, r, slices, stacks)


def draw_player():
    pos = player_pos()
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    # orient a tiny body
    glColor3f(0.2, 0.8, 1.0)
    glutSolidSphere(PLAYER_SIZE, 16, 16)
    # small nose cone towards tangent dir
    t = player_tangent_dir()
    glRotatef(math.degrees(math.atan2(t[1], t[0])), 0,0,1)
    glTranslatef(PLAYER_SIZE+4, 0, 0)
    glColor3f(1.0, 1.0, 0.3)
    glutSolidSphere(6, 12, 12)
    glPopMatrix()


def draw_planet_and_shield():
    # planet
    glPushMatrix()
    glColor3f(0.2, 0.6, 0.2)
    draw_sphere(PLANET_R, (0.2,0.6,0.2))
    glPopMatrix()

    # shield
    if shield_active and shield_time_left > 0.0:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.3, 0.7, 1.0, 0.28)
        draw_sphere(PLANET_R+12, (0.3,0.7,1.0), alpha=0.28)
        glDisable(GL_BLEND)


def draw_bullets():
    if BULLET_AS_POINTS:
        glPointSize(POINT_SIZE)
        glBegin(GL_POINTS)
        glColor3f(1.0, 0.4, 0.2)
        for b in bullets:
            glVertex3f(b["pos"][0], b["pos"][1], b["pos"][2])
        glEnd()
    else:
        glColor3f(1.0, 0.4, 0.2)
        for b in bullets:
            glPushMatrix(); glTranslatef(b["pos"][0], b["pos"][1], b["pos"][2])
            glutSolidSphere(4, 10, 10)
            glPopMatrix()


def draw_meteors():
    glColor3f(0.6, 0.5, 0.4)
    for m in meteors:
        glPushMatrix(); glTranslatef(m["pos"][0], m["pos"][1], m["pos"][2])
        glutSolidSphere(12, 12, 12)
        glPopMatrix()


def draw_aliens():
    glColor3f(1.0, 0.2, 0.2)
    for a in aliens:
        glPushMatrix(); glTranslatef(a["pos"][0], a["pos"][1], a["pos"][2])
        glutSolidSphere(14, 14, 14)
        glPopMatrix()


def draw_pickups():
    global pickups
    if not pickups: return
    for pk in pickups:
        glPushMatrix(); glTranslatef(pk["pos"][0], pk["pos"][1], 0.0)
        if pk["type"] == 'nova':
            glColor3f(1.0, 0.85, 0.1)  # gold
        elif pk["type"] == 'ship':
            glColor3f(0.3, 1.0, 0.3)  # green
        else:
            glColor3f(0.3, 0.7, 1.0)  # blue
        glutSolidSphere(10, 14, 14)
        glPopMatrix()


def draw_enemy_bullets():
    if not enemy_bullets: return
    glPointSize(4)
    glBegin(GL_POINTS)
    glColor3f(1.0, 0.9, 0.2)
    for eb in enemy_bullets:
        glVertex3f(eb["pos"][0], eb["pos"][1], eb["pos"][2])
    glEnd()


def draw_pickups():
    if not pickups: return
    for pk in pickups:
        glPushMatrix(); glTranslatef(pk["pos"][0], pk["pos"][1], 0.0)
        if pk["type"] == 'nova':
            glColor3f(1.0, 0.85, 0.1)
        elif pk["type"] == 'ship':
            glColor3f(0.3, 1.0, 0.3)
        else:
            glColor3f(0.3, 0.7, 1.0)
        glutSolidSphere(10, 14, 14)
        glPopMatrix()


def draw_explosions():
    if not explosions: return
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for e in explosions:
        age = now() - e["born"]
        t = age / e["life"]
        alpha = max(0.0, 1.0 - t)
        glPushMatrix(); glTranslatef(e["pos"][0], e["pos"][1], e["pos"][2])
        draw_sphere(e["r"]*(1.0 + 2.0*t), (1.0,0.7,0.2), alpha=alpha, slices=14, stacks=14)
        glPopMatrix()
    glDisable(GL_BLEND)


def draw_nova_pickup():
    if not nova_pickup_active: return
    glPushMatrix(); glTranslatef(nova_pickup_pos[0], nova_pickup_pos[1], 0.0)
    glColor3f(1.0, 0.85, 0.1)
    glutSolidSphere(10, 14, 14)
    glColor3f(1.0, 0.3, 0.9)
    glutWireSphere(14, 10, 10)
    glPopMatrix()


# Menus & Overlays  

def draw_centered_line(y, text):
    x = max(10, WIN_W//2 - int(len(text)*9/2))
    draw_text_2d(x, y, text)


def draw_main_menu():
    draw_centered_line(WIN_H//2 + 80, "PLANET GUARDIAN 3D")
    draw_centered_line(WIN_H//2 + 40, "Press G to Start")
    draw_centered_line(WIN_H//2 + 10, "Press Z for Controls")
    draw_centered_line(WIN_H//2 - 20, "Press Q to Quit")


def draw_controls_page():
    y = WIN_H - 120
    draw_centered_line(WIN_H - 60, "CONTROLS")
    lines = [
        "A/D: Orbit left/right",
        "W/S: Change orbit radius",
        "Left Mouse: Shoot",
        "Right Mouse: Toggle Camera (Follow/Free)",
        "Arrow Keys: Free Camera orbit/tilt",
        "E: Activate Shield (protects planet only)",
        "F: Nova Bomb (uses 1 charge; charges drop from killed aliens)",
        "Alien drops: GOLD = +1 Nova, GREEN = +5 Ship, BLUE = +1 Planet (shoot to collect)",
        "Meteors hurt Planet on impact; colliding with them costs Ship 1 life",
        "Aliens aggro & shoot the Ship; collision kills alien",
        "C: Toggle Cheat",
        "P: Pause/Unpause",
        "R: Restart (after Game Over)",
        "Z: Back to Menu   |   G: Start Game   |   Q: Quit"
    ]
    for line in lines:
        draw_centered_line(y, line); y -= 28


# Camera

def setup_camera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(FOVY, ASPECT, 0.1, 4000.0)

    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if game_state in (GAME_MENU, GAME_CONTROLS):
        gluLookAt(0, -800, 320, 0, 0, 0, 0, 0, 1)
        return

    if free_cam:
        r = cam_dist
        yaw = math.radians(cam_yaw); pitch = math.radians(cam_pitch)
        cx = r*math.cos(pitch)*math.cos(yaw)
        cy = r*math.cos(pitch)*math.sin(yaw)
        cz = r*math.sin(pitch)
        gluLookAt(cx, cy, cz, 0,0,0, 0,0,1)
    else:
        pos = player_pos(); t = player_tangent_dir()
        behind = [-t[0]*80, -t[1]*80, 60]
        eye = [pos[0]+behind[0], pos[1]+behind[1], behind[2]]
        center = [pos[0]+t[0]*100, pos[1]+t[1]*100, 20]
        gluLookAt(eye[0], eye[1], eye[2], center[0], center[1], center[2], 0,0,1)


# physics & game Logic

def fire_bullet():
    global bullets
    if game_state != GAME_PLAYING or paused: return
    pos = player_pos(); t = player_tangent_dir()
    v = [t[0]*BULLET_SPEED, t[1]*BULLET_SPEED, t[2]*BULLET_SPEED]
    bullets.append({"pos":[pos[0], pos[1], pos[2]], "vel":v, "born":now()})


def schedule_nova_next():
    global nova_pickup_active, nova_spawn_at, nova_expires_at
    nova_pickup_active = False
    t = now()
    nova_spawn_at = t + random.uniform(NOVA_RESPAWN_MIN, NOVA_RESPAWN_MAX)
    nova_expires_at = 0.0


def update_nova_pickup(dt):
    global nova_pickup_active, nova_pickup_pos, nova_expires_at
    t = now()
    if not nova_pickup_active and t >= nova_spawn_at and game_state == GAME_PLAYING and not paused:
        # spawn a pickup on an in-plane ring
        r = random.uniform(300.0, 700.0)
        a = random.uniform(0, 360)
        nova_pickup_pos = [r*math.cos(math.radians(a)), r*math.sin(math.radians(a)), 0.0]
        nova_pickup_active = True
        nova_expires_at = t + NOVA_LIFE_SECS
    elif nova_pickup_active and t >= nova_expires_at:
        schedule_nova_next()


def activate_nova():
    global nova_charges, player_score
    if game_state != GAME_PLAYING or paused: return
    if nova_charges <= 0: return
    nova_charges -= 1
    # explode all current enemies and award score
    for m in meteors:
        explosions.append({"pos":m["pos"][:], "r":20, "born":now(), "life":0.5})
        player_score += 1
    for a in aliens:
        explosions.append({"pos":a["pos"][:], "r":24, "born":now(), "life":0.6})
        player_score += 2
    reset_enemies()  # keep challenge constant


def update_bullets(dt):
    global bullets, player_score, nova_charges, ship_life, planet_life
    i = 0
    while i < len(bullets):
        b = bullets[i]
        b["pos"][0] += b["vel"][0]*dt
        b["pos"][1] += b["vel"][1]*dt
        b["pos"][2] += b["vel"][2]*dt
        if now() - b["born"] > BULLET_LIFE:
            bullets.pop(i); continue

        # pickups (shoot to collect)
        j = 0; picked = False
        while j < len(pickups):
            pk = pickups[j]
            if length3([b["pos"][0]-pk["pos"][0], b["pos"][1]-pk["pos"][1], 0.0]) < 16:
                if pk["type"] == 'nova':
                    nova_charges = min(NOVA_MAX_CHARGES, nova_charges + 1)
                elif pk["type"] == 'ship':
                    ship_life = min(SHIP_LIFE_MAX, ship_life + PICKUP_LIFE_SHIP)
                else:
                    planet_life = min(PLANET_LIFE_MAX, planet_life + PICKUP_LIFE_PLANET)
                explosions.append({"pos": pk["pos"][:], "r": 18, "born": now(), "life": 0.4})
                pickups.pop(j)
                picked = True
                break
            j += 1
        if picked:
            bullets.pop(i); continue

        # meteors
        hit = False
        for m in meteors:
            if length3([b["pos"][0]-m["pos"][0], b["pos"][1]-m["pos"][1], b["pos"][2]-m["pos"][2]]) < 16:
                spawn = spawn_meteor(); m["pos"] = spawn["pos"]; m["vel"] = spawn["vel"]
                explosions.append({"pos":m["pos"][:], "r":16, "born":now(), "life":0.6})
                player_score += 1
                hit = True
                break
        if hit: bullets.pop(i); continue

        # aliens
        hit = False
        for a in aliens:
            if length3([b["pos"][0]-a["pos"][0], b["pos"][1]-a["pos"][1], b["pos"][2]-a["pos"][2]]) < 18:
                spawn_alien_drop(a["pos"])
                newa = spawn_alien(); a.update(newa)
                explosions.append({"pos":a["pos"][:], "r":18, "born":now(), "life":0.6})
                player_score += 2
                hit = True
                break
        if hit: bullets.pop(i); continue

        i += 1


def update_meteors(dt):
    global planet_life, ship_life
    pp = player_pos()
    for m in meteors:
        m["pos"][0] += m["vel"][0]*dt
        m["pos"][1] += m["vel"][1]*dt
        m["pos"][2] += m["vel"][2]*dt
        # Planet impact
        d = length3(m["pos"])  # z=0 planar
        collide_r = PLANET_R + (12 if (shield_active and shield_time_left>0) else 0)
        if d <= collide_r:
            if shield_active and shield_time_left>0:
                explosions.append({"pos":m["pos"][:], "r":20, "born":now(), "life":0.5})
            else:
                planet_hit()
            s = spawn_meteor(); m["pos"], m["vel"] = s["pos"], s["vel"]
            continue
        # Player collision destroys meteor, costs ship 1 life
        if length3([m["pos"][0]-pp[0], m["pos"][1]-pp[1], 0.0]) < (PLAYER_SIZE + 12):
            ship_life = max(0, ship_life - 1)
            explosions.append({"pos":m["pos"][:], "r":20, "born":now(), "life":0.5})
            s = spawn_meteor(); m["pos"], m["vel"] = s["pos"], s["vel"]


def update_aliens(dt):
    # Aliens aggro the player only and shoot
    pp = player_pos()
    for a in aliens:
        a["dir_theta"] += 30.0 * dt
        rad = math.radians(a["dir_theta"])
        desired = [a["radius"] * math.cos(rad), a["radius"] * math.sin(rad), 0.0]
        to_des = [desired[0] - a["pos"][0], desired[1] - a["pos"][1], 0.0]
        to_player = [pp[0] - a["pos"][0], pp[1] - a["pos"][1], 0.0]
        v = norm3([to_des[0] * 0.4 + to_player[0] * 0.6, to_des[1] * 0.4 + to_player[1] * 0.6, 0.0])
        a["pos"][0] += v[0] * a["speed"] * dt
        a["pos"][1] += v[1] * a["speed"] * dt
        a["pos"][2]  = 0.0

        # fire toward ship
        a["shoot_t"] += dt
        if a["shoot_t"] >= ALIEN_FIRE_COOLDOWN:
            a["shoot_t"] = 0.0
            dirv = norm3([pp[0]-a["pos"][0], pp[1]-a["pos"][1], 0.0])
            enemy_bullets.append({"pos": a["pos"][:], "vel": [dirv[0]*ALIEN_BULLET_SPEED, dirv[1]*ALIEN_BULLET_SPEED, 0.0]})

        # collision with ship kills alien (no ship damage)
        if length3([a["pos"][0]-pp[0], a["pos"][1]-pp[1], 0.0]) < (PLAYER_SIZE + 14):
            spawn_alien_drop(a["pos"])
            explosions.append({"pos":a["pos"][:], "r":18, "born":now(), "life":0.6})
            newa = spawn_alien(); a.update(newa)

        # collide with player ship
        if length3([a["pos"][0]-pp[0], a["pos"][1]-pp[1], 0.0]) < (PLAYER_SIZE+14):
            explosions.append({"pos":a["pos"][:], "r":18, "born":now(), "life":0.5})
            # drop a pickup
            drop_type = random.choice(['nova','ship','planet'])
            pickups.append({"pos":a["pos"][:], "type":drop_type, "born":now()})
            newa = spawn_alien(); a.update(newa)

def update_enemy_bullets(dt):
    global enemy_bullets, player_life
    pp = player_pos()
    i = 0
    while i < len(enemy_bullets):
        eb = enemy_bullets[i]
        eb["pos"][0] += eb["vel"][0]*dt
        eb["pos"][1] += eb["vel"][1]*dt
        # check hit player
        if length3([eb["pos"][0]-pp[0], eb["pos"][1]-pp[1], 0.0]) < PLAYER_SIZE+6:
            player_life -= 1
            explosions.append({"pos":pp[:], "r":12, "born":now(), "life":0.3})
            enemy_bullets.pop(i); continue
        # remove if too far
        if length3(eb["pos"]) > 1200:
            enemy_bullets.pop(i); continue
        i += 1

def update_enemy_bullets(dt):
    global ship_life
    pp = player_pos()
    i = 0
    while i < len(enemy_bullets):
        eb = enemy_bullets[i]
        eb["pos"][0] += eb["vel"][0] * dt
        eb["pos"][1] += eb["vel"][1] * dt
        if abs(eb["pos"][0]) > 1500 or abs(eb["pos"][1]) > 1500:
            enemy_bullets.pop(i); continue
        if length3([eb["pos"][0]-pp[0], eb["pos"][1]-pp[1], 0.0]) < (PLAYER_SIZE + 6):
            ship_life = max(0, ship_life - 1)
            explosions.append({"pos":pp[:], "r":12, "born":now(), "life":0.25})
            enemy_bullets.pop(i); continue
        i += 1


def spawn_alien_drop(pos):
    # Random drop: nova / ship life / planet life
    kind = random.choice(['nova','ship','planet'])
    pickups.append({"pos":[pos[0], pos[1], 0.0], "type":kind, "born":now()})


def update_pickups():
    t = now(); i = 0
    while i < len(pickups):
        if t - pickups[i]["born"] > PICKUP_EXPIRE_SECS:
            pickups.pop(i)
        else:
            i += 1


def update_explosions():
    i = 0
    t = now()
    while i < len(explosions):
        if t - explosions[i]["born"] > explosions[i]["life"]:
            explosions.pop(i)
        else:
            i += 1


def planet_hit():
    global planet_life, game_state
    if planet_life > 0:
        planet_life -= 1
        explosions.append({"pos":[0,0,0], "r":PLANET_R, "born":now(), "life":0.45})
        if planet_life <= 0:
            game_state = GAME_OVER


def activate_shield():
    global shield_active, shield_time_left, shield_last_used
    t = now()
    if t - shield_last_used < SHIELD_COOLDOWN: return
    shield_active = True
    shield_time_left = SHIELD_MAX
    shield_last_used = t


def update_shield(dt):
    global shield_active, shield_time_left
    if shield_active:
        shield_time_left -= dt
        if shield_time_left <= 0:
            shield_active = False


def update_cheat(dt):
    global orbit_theta, cheat_fire_timer
    if not (cheat and game_state == GAME_PLAYING) or paused: return
    orbit_theta = (orbit_theta + 60.0*dt) % 360
    cheat_fire_timer += dt
    if cheat_fire_timer >= 0.12:
        fire_bullet(); cheat_fire_timer = 0.0


# GLUT callbacks

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WIN_W, WIN_H)

    setup_camera()
    
    draw_planet_and_shield()  # always draw planet 

    if game_state == GAME_MENU:
        draw_main_menu(); glutSwapBuffers(); return

    if game_state == GAME_CONTROLS:
        draw_controls_page(); glutSwapBuffers(); return

    # enemies & pickups
    draw_meteors()
    draw_aliens()
    draw_pickups()

    # player, bullets & explosions
    draw_player()
    draw_bullets()
    draw_enemy_bullets()
    draw_explosions()

    # HUD
    if game_state == GAME_OVER:
        draw_text_2d(10, WIN_H-24, f"GAME OVER — Score: {player_score}   Press R to Restart   |   Z: Menu")
    else:
        line1 = f"Planet: {planet_life}/{PLANET_LIFE_MAX}   Ship: {ship_life}/{SHIP_LIFE_MAX}   Score: {player_score}   Shield: {'ON' if (shield_active and shield_time_left>0) else 'OFF'}   Nova: {nova_charges}/{NOVA_MAX_CHARGES}"
        line2 = f"Camera: {'Free' if free_cam else 'Follow'}   Cheat: {'ON' if cheat else 'OFF'}   {'PAUSED' if paused else ''}"
        draw_text_2d(10, WIN_H-24, line1)
        draw_text_2d(10, WIN_H-48, line2)
        if paused:
            draw_centered_line(WIN_H//2, "PAUSED")

    glutSwapBuffers()


def compute_dt():
    global _last_time
    t = now(); dt = t - _last_time; _last_time = t
    return dt


def idle():
    dt = compute_dt()

    if game_state == GAME_PLAYING and not paused:
        update_bullets(dt)
        update_meteors(dt)
        update_aliens(dt)
        update_enemy_bullets(dt)
        update_shield(dt)
        update_cheat(dt)

    update_pickups()
    update_explosions()
    glutPostRedisplay()


def keyboard(key, x, y):
    global orbit_theta, orbit_r, free_cam, cheat, paused
    global planet_life, player_score, game_state, nova_charges, ship_life

    k = key.lower() if isinstance(key, bytes) else key

    # Global shortcuts
    if k == b'q':
        try:
            glutLeaveMainLoop()
        except Exception:
            sys.exit(0)
        return

    if game_state == GAME_MENU:
        if k == b'g':
            soft_reset(); game_state = GAME_PLAYING
        elif k == b'z':
            game_state = GAME_CONTROLS
        return

    if game_state == GAME_CONTROLS:
        if k == b'z':
            game_state = GAME_MENU
        elif k == b'g':
            soft_reset(); game_state = GAME_PLAYING
        return

    if game_state == GAME_OVER:
        if k == b'r':
            soft_reset(); game_state = GAME_PLAYING
        elif k == b'z':
            game_state = GAME_MENU
        return

    # --- GAME_PLAYING ---
    if k == b'p':
        paused = not paused
        return

    if k == b'f':
        activate_nova(); return

    if paused:
        if k == b'c':
            cheat = not cheat
        return

    if k == b'a':
        orbit_theta = (orbit_theta + 4.0) % 360
    elif k == b'd':
        orbit_theta = (orbit_theta - 4.0) % 360
    elif k == b'w':
        orbit_r = clamp(orbit_r + 6.0, PLANET_R + 40.0, 720.0)
    elif k == b's':
        orbit_r = clamp(orbit_r - 6.0, PLANET_R + 40.0, 720.0)
    elif k == b'e':
        activate_shield()
    elif k == b'c':
        cheat = not cheat

    glutPostRedisplay()


def special(key, x, y):
    global cam_yaw, cam_pitch
    if key == GLUT_KEY_LEFT:
        cam_yaw += 2.0
    elif key == GLUT_KEY_RIGHT:
        cam_yaw -= 2.0
    elif key == GLUT_KEY_UP:
        cam_pitch = clamp(cam_pitch + 1.5, -80, 80)
    elif key == GLUT_KEY_DOWN:
        cam_pitch = clamp(cam_pitch - 1.5, -80, 80)
    glutPostRedisplay()


def mouse(button, state, x, y):
    global free_cam
    if state != GLUT_DOWN: return
    if game_state != GAME_PLAYING: return
    if button == GLUT_LEFT_BUTTON:
        fire_bullet()
    elif button == GLUT_RIGHT_BUTTON:
        free_cam = not free_cam
    glutPostRedisplay()


# Setup / Reset

def init_gl():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_POINT_SMOOTH)
    glClearColor(0.02, 0.02, 0.04, 1.0)


def soft_reset():
    global planet_life, ship_life, player_score, orbit_r, orbit_theta
    global bullets, explosions, shield_active, shield_time_left
    global meteors, aliens, paused, nova_charges, enemy_bullets, pickups
    planet_life = PLANET_LIFE_MAX
    ship_life = SHIP_LIFE_MAX
    player_score = 0
    orbit_r = PLAYER_INIT_R
    orbit_theta = 0.0
    bullets.clear(); explosions.clear(); enemy_bullets.clear(); pickups.clear()
    shield_active = False; shield_time_left = 0.0
    reset_enemies()
    paused = False
    nova_charges = NOVA_MAX_CHARGES
    schedule_nova_next()


def reset_enemies():
    meteors[:] = [spawn_meteor() for _ in range(NUM_METEORS)]
    aliens[:] = [spawn_alien() for _ in range(NUM_ALIENS)]


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(80, 50)
    glutCreateWindow(b"Planet Guardian 3D")

    init_gl()
    # Start at Main Menu backdrop
    reset_enemies()
    schedule_nova_next()

    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special)
    glutMouseFunc(mouse)

    glutMainLoop()


if __name__ == "__main__":
    main()
