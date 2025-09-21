



#task2
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random as rnd
import time as t
width,height=500,500

points=[]
speed=.1
freeze=False
blink=False
blink_timing=.5
blink_on= True

def point(x,y):
    global speed
    dx=rnd.choice([-1,1])*speed
    dy=rnd.choice([-1,1])*speed
    r=rnd.random()
    g=rnd.random()
    b=rnd.random()
    return [x,y,dx,dy,r,g,b ]

def points_drawing():
    global blink
    glPointSize(5)
    glBegin(GL_POINTS)
    for dot in points:
        if not blink or(blink and blink_on):
            glColor3f(dot[4],dot[5],dot[6])
            glVertex2d(dot[0],dot[1])
    glEnd()

def animation():
    global blink_on, blink_timing
    if not freeze:
        for dot in points:
            dot[0]+=dot[2]
            dot[1]+=dot[3]
            if dot[0]>=width or dot[0]<= 0:
                dot[2]*=-1
            if dot[1]>=height  or dot[1]<=0:
                dot[3]*=-1
        if blink:
            cur=t.time()
            if cur-blink_timing > .2:
                blink_timing=cur
                blink_on= not blink_on
    glutPostRedisplay()


def mouseListener(button, state , x,y):
    global blink
    if freeze == True or state != GLUT_DOWN:
        return
    if button==GLUT_RIGHT_BUTTON:
        if state == GLUT_DOWN: 
            points.append(point(x,height-y))
    if button==GLUT_LEFT_BUTTON:
        if(state == GLUT_DOWN):        
            blink= not blink

def specialKeyListener(key,x,y):
    global speed
    if key==GLUT_KEY_UP:
        speed =min(speed+.1,1)
        if speed!=1:
            print("Speed Increased")
        for dot in points:
            dot[2]= (dot[2]/abs(dot[2]))*speed
            dot[3]= (dot[3]/abs(dot[3]))*speed
    if key== GLUT_KEY_DOWN:		
        speed=max(speed-.1,.1)
        if speed!=.1:    
            print("Speed Decreased")
        for dot in points:
            dot[2]= (dot[2]/abs(dot[2]))*speed
            dot[3]= (dot[3]/abs(dot[3]))*speed

def keyboardListener(key,x,y):
    global freeze
    if key==b" ":
        freeze= not freeze

def iterate():
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, width, 0.0, height, 0.0, 1.0)
    glMatrixMode (GL_MODELVIEW)
    glLoadIdentity()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    iterate()
    points_drawing()
    glutSwapBuffers()

glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(width, height) 
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"Magic box") 
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)
glutIdleFunc(animation)
glutDisplayFunc(showScreen)

glutMainLoop()