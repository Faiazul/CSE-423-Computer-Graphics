from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Game state management
class GameState:
    def __init__(self):
        self.viewer_position = [0, 500, 500]
        self.field_of_view = 120
        self.grid_dimension = 600
        self.cell_dimension = self.grid_dimension * 2 / 13
        self.player_x, self.player_y = 0, 0
        self.player_rotation = 0
        self.enemies = []
        self.bullets = []
        self.missed_shots = 0
        self.life = 5
        self.points = 0
        self.game_ended = False
        self.cheat_active = False
        self.fpp = False
        self.tpp = True
        self.last_camera_focus = [0, 0, 0]

game = GameState()

def display_text(x, y, content, font_style=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for character in content:
        glutBitmapCharacter(font_style, ord(character))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def render_bullets():
    glColor3f(1, 0, 0)
    for projectile in game.bullets:
        glPushMatrix()
        glTranslatef(projectile[0], projectile[1], projectile[2])
        glutSolidCube(10)
        glPopMatrix()

def update_bullets():
    global game
    
    active_bullets = []
    for proj_x, proj_y, proj_z, vel_x, vel_y, vel_z in game.bullets:
        new_x, new_y = proj_x + vel_x * 10, proj_y + vel_y * 10
        
        if abs(new_x) > game.grid_dimension or abs(new_y) > game.grid_dimension:
            if not game.cheat_active and not game.fpp:
                game.missed_shots += 1
                print("Bullet Missed:", game.missed_shots)
            continue
            
        active_bullets.append([new_x, new_y, proj_z, vel_x, vel_y, vel_z])
    
    game.bullets = active_bullets
    
    if game.missed_shots >= 10 or game.life <= 0:
        game.game_ended = True
        game.enemies = []

def check_collisions():
    global game
    
    remaining_bullets = []
    updated_enemies = []
    
    for adv in game.enemies:
        adv_x, adv_y, adv_z, scale, pulse = adv
        hit_detected = False
        
        for proj in game.bullets:
            proj_x, proj_y, proj_z = proj[0], proj[1], proj[2]
            
            if (proj_x - adv_x) ** 2 + (proj_y - adv_y) ** 2 < 30**2:
                hit_detected = True
                game.points += 1
                break
                
        if hit_detected:
            updated_enemies.append(generate_enemy())
        else:
            updated_enemies.append([adv_x, adv_y, adv_z, scale, pulse])
    
    for proj in game.bullets:
        collision = False
        for adv in updated_enemies:
            if (proj[0] - adv[0])**2 + (proj[1] - adv[1])**2 < 30**2:
                collision = True
                break
        if not collision:
            remaining_bullets.append(proj)
    
    game.bullets = remaining_bullets
    game.enemies = updated_enemies

def draw_player_character():
    glPushMatrix()
    glScalef(0.7, 0.7, 0.7)
    
    # Draw feet
    glColor3f(0, 0, 1)
    glTranslatef(0, -20, -100)
    glRotatef(180, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 16, 8, 100, 10, 10)
    
    glTranslatef(0, -80, 0)
    gluCylinder(gluNewQuadric(), 16, 8, 100, 10, 10)
    
    # Draw torso
    glColor3f(0.4, 0.5, 0)
    glTranslatef(0, 40, -30)
    glutSolidCube(80)
    
    # Draw weapon
    glColor3f(0.5, 0.5, 0.5)
    glTranslatef(0, 0, 40)
    glTranslatef(30, 0, -90)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 20, 5, 120, 10, 10)
    
    # Draw arms
    glColor3f(1, 0.7, 0.6)
    glTranslatef(0, -25, 0)
    gluCylinder(gluNewQuadric(), 15, 6, 60, 10, 10)
    
    glTranslatef(0, 50, 0)
    gluCylinder(gluNewQuadric(), 15, 6, 60, 10, 10)
    
    # Draw head
    glColor3f(0, 0, 0)
    glTranslatef(40, -25, -25)
    gluSphere(gluNewQuadric(), 30, 10, 10)
    
    glPopMatrix()

def render_enemy(enemy):
    glPushMatrix()
    glTranslatef(enemy[0], enemy[1], enemy[2])
    glScalef(enemy[3], enemy[3], enemy[3])
    
    glColor3f(1, 0, 0)
    glTranslatef(0, 0, 40)
    gluSphere(gluNewQuadric(), 40, 21, 21)
    
    glColor3f(0, 0, 0)
    glTranslatef(0, 0, 45)
    gluSphere(gluNewQuadric(), 20, 10, 10)
    
    glPopMatrix()

def generate_enemy():
    while True:
        x_pos = random.randint(-game.grid_dimension + 50, game.grid_dimension - 100)
        y_pos = random.randint(-game.grid_dimension + 50, game.grid_dimension - 100)
        if abs(x_pos) > 190 or abs(y_pos) > 190:
            break
    scale_factor = 1.0
    scale_change = 0.002
    return [x_pos, y_pos, 0, scale_factor, scale_change]

for _ in range(5):
    game.enemies.append(generate_enemy())

def update_enemies():
    global game
    
    for i in range(len(game.enemies)):
        adv_x, adv_y, adv_z, scale, pulse = game.enemies[i]
        
        dx, dy = game.player_x - adv_x, game.player_y - adv_y
        distance_squared = dx * dx + dy * dy
        
        if distance_squared > 1:
            inv_distance = 0.05 / math.sqrt(distance_squared)
            adv_x += dx * inv_distance
            adv_y += dy * inv_distance
        
        scale += pulse
        if scale > 1.4 or scale < 0.6:
            pulse = -pulse
        
        game.enemies[i] = [adv_x, adv_y, adv_z, scale, pulse]
    
    if not game.game_ended:
        collision_index = -1
        for i, (adv_x, adv_y, adv_z, _, _) in enumerate(game.enemies):
            if abs(game.player_x - adv_x) < 100 and abs(game.player_y - adv_y) < 100:
                collision_index = i
                break
        
        if collision_index != -1:
            if game.life > 0:
                game.life -= 1
                print("Remaining Player Life:", game.life)
                game.enemies[collision_index] = generate_enemy()
            else:
                game.game_ended = True
                game.enemies = []

def activate_cheat_features():
    global game
    
    if not game.cheat_active or game.game_ended:
        return
    
    game.player_rotation = (game.player_rotation + 0.5) % 360
    angle_rad = math.radians(game.player_rotation)
    
    aim_x = -math.cos(angle_rad)
    aim_y = -math.sin(angle_rad)
    
    weapon_length, side_offset, height = 140, 50, 10
    muzzle_x = game.player_x + side_offset * math.sin(angle_rad) + aim_x * weapon_length
    muzzle_y = game.player_y - side_offset * math.cos(angle_rad) + aim_y * weapon_length
    muzzle_z = height
    
    for target in list(game.enemies):
        dx, dy = target[0] - muzzle_x, target[1] - muzzle_y
        distance_2d = math.hypot(dx, dy)
        if distance_2d == 0:
            continue
        
        alignment = (aim_x * dx + aim_y * dy) / distance_2d
        if alignment > 0.995 and distance_2d <= 450:
            dz = target[2] - muzzle_z
            magnitude = math.sqrt(dx**2 + dy**2 + dz**2)
            if magnitude == 0:
                continue
            direction = (dx / magnitude, dy / magnitude, dz / magnitude)
            
            game.bullets.append([muzzle_x, muzzle_y, muzzle_z, *direction])
            
            game.points += 1
            
            game.enemies.remove(target)
            game.enemies.append(generate_enemy())
            break
    
    glutPostRedisplay()

def handle_keyboard_input(key, x, y):
    global game
    
    if key == b'w':
        angle_rad = math.radians(game.player_rotation)
        dx = 5 * math.cos(angle_rad)
        dy = 5 * math.sin(angle_rad)
        game.player_x = max(min(game.player_x - dx, game.grid_dimension - 20), -game.grid_dimension + 20)
        game.player_y = max(min(game.player_y - dy, game.grid_dimension - 20), -game.grid_dimension + 20)
        
    if key == b's':
        angle_rad = math.radians(game.player_rotation)
        dx = 5 * math.cos(angle_rad)
        dy = 5 * math.sin(angle_rad)
        game.player_x = max(min(game.player_x + dx, game.grid_dimension - 20), -game.grid_dimension + 20)
        game.player_y = max(min(game.player_y + dy, game.grid_dimension - 20), -game.grid_dimension + 20)
        
    if key == b'a':
        game.player_rotation += 5
        if game.player_rotation >= 360:
            game.player_rotation -= 360
            
    if key == b'd':
        game.player_rotation -= 5
        if game.player_rotation < 0:
            game.player_rotation += 360
            
    if key == b'c':
        game.cheat_active = not game.cheat_active
        if not game.cheat_active:
            game.fpp = True
            
    if key == b'v':
        if not game.tpp and game.cheat_active:
            game.fpp = not game.fpp
        else:
            game.fpp = False
            
    if key == b'r':
        game.bullets = []
        game.enemies = []
        for _ in range(5):
            game.enemies.append(generate_enemy())
            
        game.points = 0
        game.missed_shots = 0
        game.life = 5
        game.game_ended = False
        game.player_x, game.player_y = 0, 0
        game.player_rotation = 0
        print("Game Restarted!")
        
        glutPostRedisplay()

def handle_special_keys(key, x, y):
    global game
    
    x, y, z = game.viewer_position
    radius = math.hypot(x, y)
    angle = math.atan2(y, x)
    
    if key == GLUT_KEY_UP:
        z += 1
        
    if key == GLUT_KEY_DOWN:
        z -= 1
        
    if key == GLUT_KEY_LEFT:
        angle -= math.radians(1)
        
    if key == GLUT_KEY_RIGHT:
        angle += math.radians(1)
        
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    game.viewer_position = (x, y, z)

def handle_mouse_actions(button, state, x, y):
    global game
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        angle_rad = math.radians(game.player_rotation)
        dx = -math.cos(angle_rad)
        dy = -math.sin(angle_rad)
        
        weapon_length = 140
        weapon_side = 50
        weapon_height = 10
        
        proj_x = game.player_x + weapon_side * math.sin(angle_rad) + dx * weapon_length
        proj_y = game.player_y - weapon_side * math.cos(angle_rad) + dy * weapon_length
        proj_z = weapon_height
        
        magnitude = math.hypot(dx, dy)
        if magnitude == 0:
            return
        dx /= magnitude
        dy /= magnitude
        
        game.bullets.append([proj_x, proj_y, proj_z, dx, dy, 0])
        print("Player Bullet Fired!")
        
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        game.tpp = not game.tpp

def setup_camera():
    global game
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(game.field_of_view, 1.25, 0.1, 2000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if game.tpp:
        x, y, z = game.viewer_position
        gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)
    else:
        angle_rad = math.radians(game.player_rotation)
        forward_offset = 50
        side_offset = 30
        height_offset = 40
        
        cam_x = game.player_x + side_offset * math.sin(angle_rad) - math.cos(angle_rad) * forward_offset
        cam_y = game.player_y - side_offset * math.cos(angle_rad) - math.sin(angle_rad) * forward_offset
        cam_z = height_offset
        
        if game.cheat_active and game.fpp:
            look_x = cam_x + (-math.cos(angle_rad)) * 100
            look_y = cam_y + (-math.sin(angle_rad)) * 100
            look_z = cam_z
            game.last_camera_focus = [look_x, look_y, look_z]
        elif game.cheat_active:
            cam_x, cam_y, cam_z = 30, 10, 10
            look_x, look_y, look_z = game.last_camera_focus
        else:
            look_x = cam_x + (-math.cos(angle_rad)) * 100
            look_y = cam_y + (-math.sin(angle_rad)) * 100
            look_z = cam_z
            game.last_camera_focus = [look_x, look_y, look_z]
            
        gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 0, 1)

def update_game_state():
    update_bullets()
    check_collisions()
    update_enemies()
    activate_cheat_features()
    glutPostRedisplay()

def render_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    setup_camera()
    
    # Draw boundary walls
    glBegin(GL_QUADS)
    # Bottom wall
    glColor3f(0, 1, 1)
    glVertex3f(-game.grid_dimension, -game.grid_dimension, 0)
    glVertex3f(game.grid_dimension, -game.grid_dimension, 0)
    glVertex3f(game.grid_dimension, -game.grid_dimension, 80)
    glVertex3f(-game.grid_dimension, -game.grid_dimension, 80)
    
    # Left wall
    glColor3f(0, 1, 0)
    glVertex3f(-game.grid_dimension, -game.grid_dimension, 0)
    glVertex3f(-game.grid_dimension, game.grid_dimension, 0)
    glVertex3f(-game.grid_dimension, game.grid_dimension, 80)
    glVertex3f(-game.grid_dimension, -game.grid_dimension, 80)
    
    # Right wall
    glColor3f(0, 0, 1)
    glVertex3f(game.grid_dimension, -game.grid_dimension, 0)
    glVertex3f(game.grid_dimension, game.grid_dimension, 0)
    glVertex3f(game.grid_dimension, game.grid_dimension, 80)
    glVertex3f(game.grid_dimension, -game.grid_dimension, 80)
    
    # Top wall
    glColor3f(1, 1, 1)
    glVertex3f(-game.grid_dimension, game.grid_dimension, 0)
    glVertex3f(game.grid_dimension, game.grid_dimension, 0)
    glVertex3f(game.grid_dimension, game.grid_dimension, 80)
    glVertex3f(-game.grid_dimension, game.grid_dimension, 80)
    glEnd()
    
    # Draw grid
    glBegin(GL_QUADS)
    for i in range(13):
        for j in range(13):
            if (i + j) % 2 == 0:
                glColor3f(1, 1, 1)
            else:
                glColor3f(0.7, 0.5, 0.95)
                
            x = -game.grid_dimension + i * game.cell_dimension
            y = -game.grid_dimension + j * game.cell_dimension
            
            glVertex3f(x, y, 0)
            glVertex3f(x + game.cell_dimension, y, 0)
            glVertex3f(x + game.cell_dimension, y + game.cell_dimension, 0)
            glVertex3f(x, y + game.cell_dimension, 0)
    glEnd()
    
    # Display game information
    if not game.game_ended:
        display_text(10, 770, f"Player Life Remaining: {game.life}")
        display_text(10, 740, f"Game Score: {game.points}")
        display_text(10, 710, f"Player Bullet Missed: {game.missed_shots}")
    else:
        display_text(10, 770, f"Game is Over. Your Score is {game.points}.")
        display_text(10, 740, "Press 'R' to restart the game.")
    
    # Draw game objects
    glPushMatrix()
    glTranslatef(game.player_x, game.player_y, 0)
    if not game.game_ended:
        glRotatef(game.player_rotation, 0, 0, 1)
    else:
        glRotatef(90, 0, 1, 0)
    draw_player_character()
    glPopMatrix()
    
    render_bullets()
    
    if not game.game_ended:
        for enemy in game.enemies:
            render_enemy(enemy)
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Action Game")
    
    glutDisplayFunc(render_scene)
    glutKeyboardFunc(handle_keyboard_input)
    glutSpecialFunc(handle_special_keys)
    glutMouseFunc(handle_mouse_actions)
    glutIdleFunc(update_game_state)
    
    glutMainLoop()

if __name__ == "__main__":
    main()