#task1
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
width,height= 500,500
r=g=b=0
rains=[]
num=80
bend=0

def main():
    
    glBegin(GL_TRIANGLES)
    #sky
    glColor3f(r,g,b)
    glVertex2f(0,500)
    glVertex2f(500,500)
    glVertex2f(0,280)
    glVertex2f(500,500)
    glVertex2f(0,280)
    glVertex2f(500,280)
    #ground
    glColor3f(0,.4,0)
    glVertex2f(0,0)
    glVertex2f(0,280)
    glVertex2f(500,280)
    glVertex2f(500,280)
    glVertex2f(0,0)
    glVertex2f(500,0)
    #roof
    glColor3f(.7,.5,0)
    glVertex2f(150,300) #a
    glVertex2f(350,300) #b
    glVertex2f(250,350) #c
    #body
    glColor3f(1,1,.7)
    glVertex2f(330,300) #right
    glVertex2f(330,200)
    glVertex2f(170,200)
    glVertex2f(170,300) #left
    glVertex2f(170,200)
    glVertex2f(330,300)
    # door
    glColor3f(0.5,0.2,0) 
    glVertex2f(230,200) #left
    glVertex2f(230,270)
    glVertex2f(270,270)
    glVertex2f(270,200) #right
    glVertex2f(270,270)
    glVertex2f(230,200)
    glEnd()

def init():
    global rains

    for k in range(num):
        x= random.uniform(0,width)
        y=random.uniform(0,height)
        speed=random.uniform(2,5)
        rains.append([x,y,speed]) 

def rain_drawing():
    global rains, bend
    glColor3f(0.6, 0.6, .8)
    glBegin(GL_LINES)
    for drops in rains:
        x,y,speed=drops
        glVertex2f(x,y)
        glVertex2f(x+bend,y-15)
    glEnd() 

def rain_animation():
    global rains
    for drop in rains:
        drop[1] -= drop[2]
        if drop[1] < 0:
            drop[1] = height
            drop[0] = random.uniform(0, width)
    glutPostRedisplay()


def keyboardListener(key,x,y):
    global r,g,b
    if key==b'd':
        r=min(r+0.1,1)
        g=min(g+.1,1)
        b=min(b+0.1,1)
        if r!=1:
            print("color Increased")
    if key==b'a':
        r=max(r-0.1,0)
        g=max(g-0.1,0)
        b=max(b-0.1,0)
        if r!=0:
            print("color Decreased")
    glutPostRedisplay()    

def specialKeyListener(key, x, y):
    global bend
    if key==GLUT_KEY_RIGHT:
        bend = min(bend + 1, 10)
        if bend!=10:    
            print("Bend right")
    if key==GLUT_KEY_LEFT:  
        bend = max(bend - 1, -10)
        if bend!=-10:
            print("Bend left")  


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
    glColor3f(1.0, 1.0, 0.0) 
    main()
    rain_drawing()
    glutSwapBuffers()



glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(width, height)
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"Building a House in Rainfall") 
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutIdleFunc(rain_animation)
glutDisplayFunc(showScreen)
init()
glutMainLoop()