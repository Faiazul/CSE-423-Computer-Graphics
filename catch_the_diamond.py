from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random as rnd
import time as t
prev_time = t.time()
v=-100
dy=0
speed=0.5
score= 0
play= True
stop= False
r=rnd.random()
g=rnd.random()
b=rnd.random()
x=rnd.randint(0, 470)
cr=1
cg=1
cb=1
dx=175  
def draw_points(x, y):
    glPointSize(2)
    glBegin(GL_POINTS)
    glVertex2f(x,y) 
    glEnd()



def find_zone(dx,dy):
    if abs(dx) >= abs(dy):
        if dx >= 0 and dy >= 0:
            return 0
        elif dx < 0 and dy >= 0:
            return 3
        elif dx < 0 and dy < 0:
            return 4
        else:
            return 7
    else:
        if dx >= 0 and dy >= 0:
            return 1
        elif dx < 0 and dy >= 0:
            return 2
        elif dx < 0 and dy < 0:
            return 5
        else:
            return 6   

def convert_to_zone0(x, y, zone):
    if zone == 0:
        return (x, y)
    elif zone == 1:
        return (y, x)
    elif zone == 2:
        return (y, -x)
    elif zone == 3:
        return (-x, y)
    elif zone == 4:
        return (-x, -y)
    elif zone == 5:
        return (-y, -x)
    elif zone == 6:
        return (-y, x)
    elif zone == 7:
        return (x, -y)
    

def revert_to_OGzone(x, y, zone):
    if zone == 0:
        return (x, y)
    elif zone == 1:
        return (y, x)
    elif zone == 2:
        return (-y, x)
    elif zone == 3:
        return (-x, y)
    elif zone == 4:
        return (-x, -y)
    elif zone == 5:
        return (-y, -x)
    elif zone == 6:
        return (y, -x)
    elif zone == 7:
        return (x, -y)


def draw_line(x1, y1,x2,y2):
    x1=x1
    y1=y1
    x2=x2
    y2=y2
    dx= x2 - x1
    dy= y2 - y1
    zone = find_zone(dx, dy)
    if zone!=0:
        x1,y1= convert_to_zone0(x1, y1, zone)
        x2,y2= convert_to_zone0(x2, y2, zone)
        dx= x2 - x1
        dy= y2 - y1
    d=(dy+dy)-dx
    e=dy+dy
    ne=(dy-dx)+(dy-dx)
    x,y= x1, y1
    while x <= x2:
        xf,yf=revert_to_OGzone(x, y, zone)
        draw_points(xf, yf)
        if d < 0:
            d += e
        else:
            y += 1
            d += ne
        x += 1



def main():
    #left arrow
    glColor3f(0, 0.5, 0.5)
    draw_line(30, 490, 10, 470)
    draw_line(10, 470, 30, 450)
    draw_line(10, 470, 50, 470)
    
    glColor3f(1.0, 0.75, 0)
    if play:
        #pause button
        draw_line(240, 490, 240, 450)
        draw_line(260, 490, 260, 450)
    else:
        draw_line(240, 490, 240, 450)
        draw_line(240, 490, 270, 470)
        draw_line(270, 470, 240, 450)

    #cross
    glColor3f(1.0, 0, 0)
    draw_line(460, 490, 490, 450)
    draw_line(490, 490, 460, 450)


def diamond():
    global dy,r,g,b,x
    glColor3f(r, g, b)
    draw_line(15+x, 450+dy, 5+x, 435+dy)
    draw_line(5+x, 435+dy, 15+x, 420+dy)
    draw_line(15+x, 420+dy, 25+x, 435+dy)
    draw_line(25+x, 435+dy, 15+x, 450+dy)

def get_aabb(x, y, width, height):
    return {
        'x': x,
        'y': y,
        'width': width,
        'height': height
    }

def has_collided(box1, box2):
    return (
        box1['x'] < box2['x'] + box2['width'] and
        box1['x'] + box1['width'] > box2['x'] and
        box1['y'] < box2['y'] + box2['height'] and
        box1['y'] + box1['height'] > box2['y']
    )

def collision():
    global dy,dx,x
    diamond_x1 = 5 + x
    diamond_x2 = 25 + x
    diamond_y1 = 420 + dy
    diamond_y2 = 450 + dy
    diamond_box = get_aabb(diamond_x1, diamond_y1, diamond_x2 - diamond_x1, diamond_y2 - diamond_y1)
    catcher_x1 = 1 + dx
    catcher_x2 = 110 + dx   
    catcher_y1 = 5
    catcher_y2 = 20 
    catcher_box = get_aabb(catcher_x1, catcher_y1, catcher_x2 - catcher_x1, catcher_y2 - catcher_y1)
    

    return has_collided(diamond_box, catcher_box)
    
def animation():
    global  play,dy,r,g,b,x,prev_time,v,stop,score,cr,cg,cb
    if not play or stop:
        return

    cur_time=t.time()
    dt=cur_time-prev_time
    prev_time = cur_time
    v-=5*dt
    dy+=v*dt
    
    if collision():
            score += 1
            print("Score: ", score)
            dy=0
            r=rnd.random()
            g=rnd.random()
            b=rnd.random()
            x=rnd.randint(0, 470)
    elif 420+dy <= 20:
            cr=1
            cg=0
            cb=0
            print("Game Over! Score: ", score)
            stop = True
            return    
        
        
    
    glutPostRedisplay()    


def catcher():
    global dx
    draw_line(10+dx, 5, 100+dx, 5)
    draw_line(1+dx, 20, 110+dx, 20)
    draw_line(100+dx, 5, 110+dx, 20)
    draw_line(1+dx, 20, 10+dx, 5)
    glutPostRedisplay()

def pause():
    global play,prev_time
    prev_time = t.time()
    play = not play
    return

def  restart():
    global play, prev_time, v, dy, speed, score, stop,r,g,b,x,cr,cg,cb,dx
    dx=175
    prev_time = t.time()
    v=-100
    dy=0
    speed=0.5
    score= 0
    play= True
    stop= False
    r=rnd.random()
    g=rnd.random()
    b=rnd.random()
    x=rnd.randint(0, 470)
    cr=1
    cg=1
    cb=1
    print("Starting Over")
    return

def mouseListener(button, state , x,y):
    y = 500 - y 
    if button==GLUT_LEFT_BUTTON:
        if(state == GLUT_DOWN):
            if 460 <= x <= 490 and 450 <= y <= 490:
                print("Goodbye! Score: ", score)
                glutLeaveMainLoop()
            elif 235 <= x <= 265 and 450 <= y <= 490:
                pause()   
            elif 10 <= x <= 50 and 450 <= y <= 490:
                restart()    

def specialKeyListener(key, x, y):
    global dx
    if not play or stop:
        return
    if key==GLUT_KEY_RIGHT:
        dx= min(dx + 5, 390)
        
    if key==GLUT_KEY_LEFT:  
        dx= max(dx - 5, 0)

def iterate():
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    glMatrixMode (GL_MODELVIEW)
    glLoadIdentity()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    iterate()
    glColor3f(cr, cg, cb) 
    catcher()
    main()
    if not stop:
        diamond()
    glutSwapBuffers()
    



glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(500, 500) #window size
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"Catch the diamond") #window name
glutDisplayFunc(showScreen)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)
glutIdleFunc(animation)
glutMainLoop()