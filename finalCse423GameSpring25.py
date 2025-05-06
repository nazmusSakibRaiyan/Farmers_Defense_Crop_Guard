from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLUT.fonts import GLUT_BITMAP_HELVETICA_18
from OpenGL.GLU import *
import random, math, time

GRID_LENGTH = 300
FOV_Y = 90

game_start_time = time.time()
score = 0
crow_spawn_interval = 30
next_crow_spawn = game_start_time + crow_spawn_interval

camera_pos = (0, 500, 500)
camera_mode = "third_person"
farmer_speed = 5

farmer_pos = [0, 0, 30]
farmer_angle = 0
arm_mode = "plant"

clouds = []
for _ in range(10):
    clouds.append([
        random.uniform(-GRID_LENGTH*1.5, GRID_LENGTH*1.5),
        random.uniform(-GRID_LENGTH*1.5, GRID_LENGTH*1.5),
        random.uniform(250, 350),
        random.uniform(30, 50), 0 ])

shed_pos = [-200, -200, 0]
shed_size = [60, 60, 50]
shed_door_open = False
storage_capacity = 0
max_storage = 100

tractor_pos = [200, 200, 0]
tractor_angle = 0
using_tractor = False

crop_types = ["wheat", "rice", "corn", "sugarcane"]
crop_colors = {
    "wheat": (0.9, 0.8, 0.2),
    "rice": (0.7, 0.9, 0.7),
    "corn": (0.9, 0.7, 0.0),
    "sugarcane": (0.5, 0.8, 0.2)
}
crop_growth_time = 5
crop_health = 100
quadrants = [
    (-GRID_LENGTH, 0, 0, GRID_LENGTH),
    (0, 0, GRID_LENGTH, GRID_LENGTH),
    (-GRID_LENGTH, -GRID_LENGTH, 0, 0),
    (0, -GRID_LENGTH, GRID_LENGTH, 0)
]
quadrant_crops = {
    0: "wheat",
    1: "rice",
    2: "corn",
    3: "sugarcane"
}

plant_spots = []
for q_idx, (x1, z1, x2, z2) in enumerate(quadrants):
    crop_type = quadrant_crops[q_idx]
    for i in range(4):
        for j in range(4):
            x = x1 + (x2 - x1) * (i + 0.5) / 4
            z = z1 + (z2 - z1) * (j + 0.5) / 4
            plant_spots.append([x, z, crop_type, 0, crop_health, 0])

bullets = []
bullet_speed = 10
bullet_size = 5
bullet_lifetime = 100
crows = []
crow_speed = 0.1
crow_max_health = 20
crow_damage = 10

keys_pressed = {
    b'w': False,
    b's': False,
    b'a': False,
    b'd': False
}


farmer_inventory = 0  
mature_crops_count = 0 
crop_collision_radius = 5.0 
farmer_collision_radius = 10.0 

def getzone(x_start, y_start, x_end, y_end):
    delta_x = x_end - x_start
    delta_y = y_end - y_start
    if delta_x >= 0:
        if delta_y >= 0:
            return 0 if abs(delta_x) > abs(delta_y) else 1
        else:
            return 7 if abs(delta_x) > abs(delta_y) else 6
    else:
        if delta_y >= 0:
            return 3 if abs(delta_x) > abs(delta_y) else 2
        else:
            return 4 if abs(delta_x) > abs(delta_y) else 5


def convert_to_zone0(x_coord, y_coord, original_zone):
    if original_zone == 0:
        return (x_coord, y_coord)
    elif original_zone == 1:
        return (y_coord, x_coord)
    elif original_zone == 2:
        return (y_coord, -x_coord)
    elif original_zone == 3:
        return (-x_coord, y_coord)
    elif original_zone == 4:
        return (-x_coord, -y_coord)
    elif original_zone == 5:
        return (-y_coord, -x_coord)
    elif original_zone == 6:
        return (-y_coord, x_coord)
    elif original_zone == 7:
        return (x_coord, -y_coord)


def convert_to_original_zone(x_coord, y_coord, original_zone):
    if original_zone == 0:
        return (x_coord, y_coord)
    elif original_zone == 1:
        return (y_coord, x_coord)
    elif original_zone == 2:
        return (-y_coord, x_coord)
    elif original_zone == 3:
        return (-x_coord, y_coord)
    elif original_zone == 4:
        return (-x_coord, -y_coord)
    elif original_zone == 5:
        return (-y_coord, -x_coord)
    elif original_zone == 6:
        return (y_coord, -x_coord)
    elif original_zone == 7:
        return (x_coord, -y_coord)


def drawpixel(x, y, original_zone):
    glPointSize(1)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


def MidpointLine(x_start, y_start, x_end, y_end, color):
    zone = getzone(x_start, y_start, x_end, y_end)
    x_start, y_start = convert_to_zone0(x_start, y_start, zone)
    x_end, y_end = convert_to_zone0(x_end, y_end, zone)
    glColor3f(*color)

    delta_x = x_end - x_start
    delta_y = y_end - y_start
    decision_param = 2 * delta_y - delta_x
    incrE = 2 * delta_y
    incrNE = 2 * (delta_y - delta_x)

    current_x = x_start
    current_y = y_start

    while current_x < x_end:
        if decision_param <= 0: #east
            decision_param += incrE
            current_x += 1
        else:
            decision_param += incrNE #north-east
            current_x += 1
            current_y += 1

        original_x, original_y = convert_to_original_zone(
            current_x, current_y, zone)
        drawpixel(original_x, original_y, zone)



def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_sky():
    glPushMatrix()
    glColor3f(0.4, 0.7, 1.0)  
    radius = GRID_LENGTH * 2
    glTranslatef(0, 0, -50)
    for i in range(0, 180, 10):
        for j in range(0, 361, 10):
            angle1 = math.radians(j)
            angle2 = math.radians(j + 10)
            y1 = radius * math.sin(angle1)
            z1 = radius * math.cos(angle1)
            y2 = radius * math.sin(angle2)
            z2 = radius * math.cos(angle2)
            MidpointLine(int(y1), int(z1), int(y2), int(z2), (0.4, 0.7, 1.0))
    glPopMatrix()

def draw_clouds():
    for cloud in clouds:
        x, y, z, size, phase = cloud
        cloud[0] += 0.2
        cloud[4] += 0.01
        if cloud[0] > GRID_LENGTH * 1.5:
            cloud[0] = -GRID_LENGTH * 1.5
            cloud[1] = random.uniform(-GRID_LENGTH*1.5, GRID_LENGTH*1.5)
            cloud[2] = random.uniform(250, 350)
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(1.0, 1.0, 1.0) 
        gluSphere(gluNewQuadric(), size, 12, 12)
        offsets = [(size*0.7, 0, 0), (-size*0.7, 0, 0),
                   (0, size*0.7, 0), (0, -size*0.7, 0),
                   (size*0.5, size*0.5, 0), (-size*0.5, -size*0.5, 0)]
        for dx, dy, dz in offsets:
            glPushMatrix()
            glTranslatef(dx, dy, dz)
            gluSphere(gluNewQuadric(), size * 0.6, 8, 8)
            glPopMatrix()
        glPopMatrix()

def draw_farmer():
    glPushMatrix()
    glTranslatef(farmer_pos[0], farmer_pos[1], farmer_pos[2])
    glRotatef(farmer_angle, 0, 0, 1)

    glColor3f(0.8, 0.6, 0.5)  
    glTranslatef(0, 0, 60)
    gluSphere(gluNewQuadric(), 15, 16, 16) 

    glColor3f(0.8, 0.3, 0.1) 
    glPushMatrix()
    glTranslatef(0, 0, 10)
    glRotatef(-90, 1, 0, 0)
    glutSolidCone(18, 15, 16, 4)
    glPopMatrix()

    glTranslatef(0, 0, -30)
    glColor3f(0.2, 0.4, 0.8)  
    gluCylinder(gluNewQuadric(), 20, 15, 45, 16, 4)

    glPushMatrix()
    glTranslatef(0, 25, 30)
    glRotatef(90, 1, 0, 0)
    if arm_mode == "plant":
        glColor3f(0.8, 0.6, 0.5)  
    else:
        glColor3f(0.2, 0.4, 0.8)  
    gluCylinder(gluNewQuadric(), 5, 5, 30, 8, 2)

    glTranslatef(0, 0, 30)
    if arm_mode == "plant":
        glColor3f(0.6, 0.3, 0.1)  
        gluSphere(gluNewQuadric(), 7, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, -25, 30)
    glRotatef(90, 1, 0, 0)
    if arm_mode == "shoot":
        glColor3f(0.3, 0.3, 0.3)
    else:
        glColor3f(0.2, 0.4, 0.8) 
    gluCylinder(gluNewQuadric(), 5, 5, 30, 8, 2)

    if arm_mode == "shoot":
        glTranslatef(0, 0, 30)
        glColor3f(0.1, 0.1, 0.1)  
        gluCylinder(gluNewQuadric(), 3, 7, 15, 8, 2)
    glPopMatrix()

    # Legs
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.5)  
    glTranslatef(10, 0, -30)
    leg_positions = [(5, 0, -15), (-5, 0, -15)]  
    for lx, ly, lz in leg_positions:
        glPushMatrix()
        glTranslatef(lx, ly, lz)
        glColor3f(0.1, 0.1, 0.5) 
        glutSolidCube(10) 
        glPopMatrix()
    glutSolidCube(1)
    glTranslatef(-2, 0, 0)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()

def draw_tractor():
    global tractor_pos, tractor_angle, using_tractor
    if using_tractor:
        tractor_pos[0] = farmer_pos[0]
        tractor_pos[1] = farmer_pos[1]
        tractor_angle = farmer_angle 

    glPushMatrix()
    glTranslatef(tractor_pos[0], tractor_pos[1], tractor_pos[2]) 
    glRotatef(tractor_angle, 0, 0, 1)
    body_height = 15
    body_width = 30
    body_depth = 15 # 
    half_body_w = body_width / 2
    half_body_d = body_depth / 2

    glColor3f(0.7, 0.1, 0.3) 
    glPushMatrix()
    glTranslatef(0, 0, body_height / 2) 
    glBegin(GL_QUADS)

    glVertex3f( half_body_w, -half_body_d, -body_height/2)
    glVertex3f( half_body_w,  half_body_d, -body_height/2)
    glVertex3f( half_body_w,  half_body_d,  body_height/2)
    glVertex3f( half_body_w, -half_body_d,  body_height/2)

    glVertex3f(-half_body_w, -half_body_d, -body_height/2)
    glVertex3f(-half_body_w,  half_body_d, -body_height/2)
    glVertex3f(-half_body_w,  half_body_d,  body_height/2)
    glVertex3f(-half_body_w, -half_body_d,  body_height/2)

    glVertex3f(-half_body_w, -half_body_d,  body_height/2)
    glVertex3f( half_body_w, -half_body_d,  body_height/2)
    glVertex3f( half_body_w,  half_body_d,  body_height/2)
    glVertex3f(-half_body_w,  half_body_d,  body_height/2)

    glVertex3f(-half_body_w, -half_body_d, -body_height/2)
    glVertex3f( half_body_w, -half_body_d, -body_height/2)
    glVertex3f( half_body_w,  half_body_d, -body_height/2)
    glVertex3f(-half_body_w,  half_body_d, -body_height/2)

    glVertex3f(-half_body_w,  half_body_d, -body_height/2)
    glVertex3f( half_body_w,  half_body_d, -body_height/2)
    glVertex3f( half_body_w,  half_body_d,  body_height/2)
    glVertex3f(-half_body_w,  half_body_d,  body_height/2)

    glVertex3f(-half_body_w, -half_body_d, -body_height/2)
    glVertex3f( half_body_w, -half_body_d, -body_height/2)
    glVertex3f( half_body_w, -half_body_d,  body_height/2)
    glVertex3f(-half_body_w, -half_body_d,  body_height/2)
    glEnd()
    glPopMatrix()
    cabin_height = 15
    cabin_width = 15
    cabin_depth = 15
    half_cabin_w = cabin_width / 2
    half_cabin_d = cabin_depth / 2

    glColor3f(0.1, 0.5, 0.1) 
    glPushMatrix()

    glTranslatef(-5, 0, body_height + cabin_height/2) 
    glBegin(GL_QUADS)


    glVertex3f( half_cabin_w, -half_cabin_d, -cabin_height/2)
    glVertex3f( half_cabin_w,  half_cabin_d, -cabin_height/2)
    glVertex3f( half_cabin_w,  half_cabin_d,  cabin_height/2)
    glVertex3f( half_cabin_w, -half_cabin_d,  cabin_height/2)

    glVertex3f(-half_cabin_w, -half_cabin_d, -cabin_height/2)
    glVertex3f(-half_cabin_w,  half_cabin_d, -cabin_height/2)
    glVertex3f(-half_cabin_w,  half_cabin_d,  cabin_height/2)
    glVertex3f(-half_cabin_w, -half_cabin_d,  cabin_height/2)

    glEnd()
    glPopMatrix()

    glColor3f(0.1, 0.1, 0.1) 
    wheel_radius_rear = 10
    wheel_radius_front = 7
    wheel_width = 5 


    wheel_positions = [
        (15, -15, wheel_radius_front), 
        (15,  15, wheel_radius_front), 
        (-10, -15, wheel_radius_rear),  
        (-10,  15, wheel_radius_rear)   
    ]

    for wx, wy, radius in wheel_positions:
        glPushMatrix()
        glTranslatef(wx, wy, radius)
        q = gluNewQuadric() 
        gluCylinder(q, radius, radius, wheel_width, 12, 2)

        glTranslatef(0, 0, 0) 
        gluDisk(q, 0, radius, 12, 1) 

        glTranslatef(0, 0, wheel_width) 
        glBegin(GL_POINTS)
        for angle in range(0, 360, 1):
            rad = math.radians(angle)
            x = radius * math.cos(rad)
            y = radius * math.sin(rad)
            glVertex3f(x, y, 0)
        glEnd()
        glBegin(GL_POINTS)
        for angle in range(0, 360, 1):
            rad = math.radians(angle)
            x = radius * math.cos(rad)
            y = radius * math.sin(rad)
            glVertex3f(x, y, wheel_width)
        glEnd()
        glBegin(GL_QUADS)
        for angle in range(0, 360, 1):
            rad1 = math.radians(angle)
            rad2 = math.radians(angle + 1)
            x1 = radius * math.cos(rad1)
            y1 = radius * math.sin(rad1)
            x2 = radius * math.cos(rad2)
            y2 = radius * math.sin(rad2)

            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y2, 0)
            glVertex3f(x2, y2, wheel_width)
            glVertex3f(x1, y1, wheel_width)
        glEnd()

        glBegin(GL_POINTS)
        for angle in range(0, 360, 1):
            rad = math.radians(angle)
            x = radius * math.cos(rad)
            y = radius * math.sin(rad)
            glVertex3f(x, y, 0)
        glEnd()
        glBegin(GL_POINTS)
        for angle in range(0, 360, 1):
            rad = math.radians(angle)
            x = radius * math.cos(rad)
            y = radius * math.sin(rad)
            glVertex3f(x, y, wheel_width)
        glEnd()
        glBegin(GL_QUADS)
        for angle in range(0, 360, 1):
            rad1 = math.radians(angle)
            rad2 = math.radians(angle + 1)
            x1 = radius * math.cos(rad1)
            y1 = radius * math.sin(rad1)
            x2 = radius * math.cos(rad2)
            y2 = radius * math.sin(rad2)

            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y2, 0)
            glVertex3f(x2, y2, wheel_width)
            glVertex3f(x1, y1, wheel_width)
        glEnd()

        pass  

        glPopMatrix()

    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()

    glTranslatef(-10, 5, body_height) 
    glRotatef(-90, 1, 0, 0) 
    pipe_radius = 2
    pipe_height = 15
    gluCylinder(gluNewQuadric(), pipe_radius, pipe_radius, pipe_height, 8, 2)
    glPopMatrix()

    glPopMatrix()

def draw_storage_shed():
    global shed_pos, shed_size, shed_door_open, storage_capacity, max_storage
    width = shed_size[0]
    depth = shed_size[1] 
    height = shed_size[2]
    half_width = width / 2
    half_depth = depth / 2

    glPushMatrix()
    glTranslatef(shed_pos[0], shed_pos[1], shed_pos[2]) 

    glColor3f(0.6, 0.4, 0.2) 
    glBegin(GL_QUADS)
    glVertex3f(-half_width, -half_depth, 0)      
    glVertex3f( half_width, -half_depth, 0)     
    glVertex3f( half_width, -half_depth, height) 
    glVertex3f(-half_width, -half_depth, height) 
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(-half_width, -half_depth, 0)      
    glVertex3f(-half_width,  half_depth, 0)      
    glVertex3f(-half_width,  half_depth, height) 
    glVertex3f(-half_width, -half_depth, height) 
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(half_width, -half_depth, 0)      
    glVertex3f(half_width,  half_depth, 0)     
    glVertex3f(half_width,  half_depth, height)
    glVertex3f(half_width, -half_depth, height) 
    glEnd()

    door_width = width * 0.4 
    door_height = height * 0.7 
    half_door_width = door_width / 2

    glBegin(GL_QUADS)
    glVertex3f(-half_width, half_depth, 0)         
    glVertex3f(-half_door_width, half_depth, 0)     
    glVertex3f(-half_door_width, half_depth, height)
    glVertex3f(-half_width, half_depth, height)    
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(half_door_width, half_depth, 0)     
    glVertex3f(half_width, half_depth, 0)          
    glVertex3f(half_width, half_depth, height)     
    glVertex3f(half_door_width, half_depth, height) 
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(-half_door_width, half_depth, door_height) 
    glVertex3f( half_door_width, half_depth, door_height) 
    glVertex3f( half_door_width, half_depth, height)      
    glVertex3f(-half_door_width, half_depth, height)      
    glEnd()

    glColor3f(0.5, 0.3, 0.1) 
    glPushMatrix()

    if shed_door_open:
        glTranslatef(-half_door_width, half_depth, 0) 
        glRotatef(-90, 0, 0, 1) 
        glTranslatef(half_door_width, -half_depth, 0) 

        glBegin(GL_QUADS)
        glVertex3f(-half_door_width, 0, 0)           
        glVertex3f( half_door_width, 0, 0)           
        glVertex3f( half_door_width, 0, door_height) 
        glVertex3f(-half_door_width, 0, door_height) 
        glEnd()

    else:
        glBegin(GL_QUADS)
        glVertex3f(-half_door_width, half_depth, 0)           
        glVertex3f( half_door_width, half_depth, 0)           
        glVertex3f( half_door_width, half_depth, door_height) 
        glVertex3f(-half_door_width, half_depth, door_height) 
        glEnd()

    glPopMatrix()

    glColor3f(0.7, 0.3, 0.1)
    roof_overhang = 5
    roof_peak_height = height + height * 0.4
    MidpointLine(-half_width - roof_overhang, half_depth + roof_overhang,
                 half_width + roof_overhang, half_depth + roof_overhang, (0.7, 0.3, 0.1))  
    MidpointLine(-half_width - roof_overhang, half_depth + roof_overhang,
                 0, half_depth + roof_overhang, (0.7, 0.3, 0.1))  
    MidpointLine(half_width + roof_overhang, half_depth + roof_overhang,
                 0, half_depth + roof_overhang, (0.7, 0.3, 0.1))  

    MidpointLine(-half_width - roof_overhang, -half_depth - roof_overhang,
                 half_width + roof_overhang, -half_depth - roof_overhang, (0.7, 0.3, 0.1))  
    MidpointLine(-half_width - roof_overhang, -half_depth - roof_overhang,
                 0, -half_depth - roof_overhang, (0.7, 0.3, 0.1))  
    MidpointLine(half_width + roof_overhang, -half_depth - roof_overhang,
                 0, -half_depth - roof_overhang, (0.7, 0.3, 0.1))  


    glBegin(GL_QUADS)
    glVertex3f(-half_width - roof_overhang, -half_depth - roof_overhang, height) 
    glVertex3f(-half_width - roof_overhang,  half_depth + roof_overhang, height) 
    glVertex3f(0,  half_depth + roof_overhang, roof_peak_height)                 
    glVertex3f(0, -half_depth - roof_overhang, roof_peak_height)                 

    glVertex3f(half_width + roof_overhang, -half_depth - roof_overhang, height) 
    glVertex3f(half_width + roof_overhang,  half_depth + roof_overhang, height) 
    glVertex3f(0,  half_depth + roof_overhang, roof_peak_height)                
    glVertex3f(0, -half_depth - roof_overhang, roof_peak_height)               
    glEnd()

    if storage_capacity > 0 and max_storage > 0:
        fill_ratio = storage_capacity / max_storage
        indicator_height = height * 0.9 * fill_ratio
        indicator_width = width * 0.8
        indicator_depth = depth * 0.8
        half_ind_width = indicator_width / 2
        half_ind_depth = indicator_depth / 2

        glColor3f(0.9, 0.8, 0.2) 
        glPushMatrix()

        glBegin(GL_QUADS)
    
        glVertex3f(-half_ind_width, -half_ind_depth, indicator_height)
        glVertex3f( half_ind_width, -half_ind_depth, indicator_height)
        glVertex3f( half_ind_width,  half_ind_depth, indicator_height)
        glVertex3f(-half_ind_width,  half_ind_depth, indicator_height)

        glVertex3f(-half_ind_width, half_ind_depth, 0)
        glVertex3f( half_ind_width, half_ind_depth, 0)
        glVertex3f( half_ind_width, half_ind_depth, indicator_height)
        glVertex3f(-half_ind_width, half_ind_depth, indicator_height)

        glVertex3f(-half_ind_width, -half_ind_depth, 0)
        glVertex3f( half_ind_width, -half_ind_depth, 0)
        glVertex3f( half_ind_width, -half_ind_depth, indicator_height)
        glVertex3f(-half_ind_width, -half_ind_depth, indicator_height)

        glVertex3f(-half_ind_width, -half_ind_depth, 0)
        glVertex3f(-half_ind_width,  half_ind_depth, 0)
        glVertex3f(-half_ind_width,  half_ind_depth, indicator_height)
        glVertex3f(-half_ind_width, -half_ind_depth, indicator_height)

        glVertex3f(half_ind_width, -half_ind_depth, 0)
        glVertex3f(half_ind_width,  half_ind_depth, 0)
        glVertex3f(half_ind_width,  half_ind_depth, indicator_height)
        glVertex3f(half_ind_width, -half_ind_depth, indicator_height)

        glEnd()
        glPopMatrix()

    glPopMatrix()


def draw_crops():
    for spot in plant_spots:
        x, z, crop_type, growth_stage, health, _ = spot
        if growth_stage > 0:
            glPushMatrix()
            glTranslatef(x, z, 0)
            base_color = crop_colors[crop_type]
            health_factor = max(0.3, health / crop_health)
            glColor3f(base_color[0] * health_factor,
                      base_color[1] * health_factor,
                      base_color[2] * health_factor)
            height = growth_stage * 10

            if crop_type == "wheat":
                for i in range(3):
                    glPushMatrix()
                    glTranslatef(-5 + i*5, -5 + i*5, 0)
                    gluCylinder(gluNewQuadric(), 1, 0.5, height, 8, 1)
                    glPopMatrix()

            elif crop_type == "rice":
                for i in range(5):
                    angle = i * 72
                    glPushMatrix()
                    glTranslatef(3*math.cos(math.radians(angle)),
                                 3*math.sin(math.radians(angle)), 0)
                    gluCylinder(gluNewQuadric(), 1, 0.2, height, 8, 1)
                    glPopMatrix()

            elif crop_type == "corn":
                gluCylinder(gluNewQuadric(), 2, 1.5, height, 8, 1)
                if growth_stage >= 2:
                    glPushMatrix()
                    glTranslatef(0, 0, height*0.7)
                    glRotatef(90, 1, 0, 0)
                    gluCylinder(gluNewQuadric(), 3, 3, 8, 8, 1)
                    glPopMatrix()

            elif crop_type == "sugarcane":
                segments = min(3, growth_stage)
                for i in range(segments):
                    glPushMatrix()
                    glTranslatef(0, 0, i * height/segments)
                    gluCylinder(gluNewQuadric(), 2, 1.8, height/segments, 8, 1)
                    glPopMatrix()

            glPopMatrix()

def draw_bullets():
    for bullet in bullets:
        x, y, z, angle, _ = bullet
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(0.9, 0.1, 0.1)
        glutSolidCube(bullet_size)
        glPopMatrix()

def draw_crows():
    for crow in crows:
        x, y, z, size, phase, health = crow[0], crow[1], crow[2], crow[3], crow[4], crow[5]
        health_percentage = health / crow_max_health
        glPushMatrix()
        glTranslatef(x, y, z)
        actual_size = size * (0.8 + 0.2 * math.sin(phase))

        if health_percentage > 0.7:
            glColor3f(0.1, 0.1, 0.1)
        elif health_percentage > 0.3:
            glColor3f(0.3, 0.1, 0.1)
        else:
            glColor3f(0.5, 0.1, 0.1)

        gluSphere(gluNewQuadric(), actual_size, 16, 16)
        wing_flap = math.sin(phase * 3) * 30

        glPushMatrix()
        glRotatef(wing_flap, 1, 0, 0)
        glTranslatef(0, actual_size, 0)
        glBegin(GL_QUADS)
        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)

        glVertex3f(actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glEnd()
        glutSolidCube(1)
        glPopMatrix()

        glPushMatrix()
        glRotatef(-wing_flap, 1, 0, 0)
        glTranslatef(0, -actual_size, 0)
        glBegin(GL_QUADS)

        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)

        glVertex3f(actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, actual_size * 0.1, actual_size * 0.5)

        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, -actual_size * 0.5)
        glVertex3f(actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glVertex3f(-actual_size * 0.75, -actual_size * 0.1, actual_size * 0.5)
        glEnd()
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(0.9, 0.6, 0.1)
        glPushMatrix()
        glTranslatef(actual_size*1.2, 0, 0)
        glRotatef(90, 0, 1, 0)
        glutSolidCone(actual_size*0.3, actual_size*0.8, 8, 2)
        glPopMatrix()

        glColor3f(1.0, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(actual_size*0.8, actual_size*0.4, actual_size*0.5)
        gluSphere(gluNewQuadric(), actual_size*0.15, 8, 8)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(actual_size*0.8, -actual_size*0.4, actual_size*0.5)
        gluSphere(gluNewQuadric(), actual_size*0.15, 8, 8)
        glPopMatrix()

        glPopMatrix()

def draw_ground():
    glBegin(GL_QUADS)
    glColor3f(0.7, 0.7, 0.4)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)
    glColor3f(0.5, 0.7, 0.5)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glColor3f(0.7, 0.6, 0.3)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, -GRID_LENGTH, 0)
    glColor3f(0.3, 0.5, 0.3)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(0, -GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(GRID_LENGTH, 0, 0)

    glEnd()

def get_quadrant(x, z):
    if x < 0 and z > 0:
        return 0
    elif x >= 0 and z > 0:
        return 1
    elif x < 0 and z <= 0:
        return 2
    else:
        return 3

def find_nearest_spot(x, z, max_distance=50):
    nearest = None
    min_dist = max_distance
    for i in range(len(plant_spots)):
        spot_x, spot_z = plant_spots[i][0], plant_spots[i][1]
        dist = math.sqrt((x - spot_x)**2 + (z - spot_z)**2)
        if dist < min_dist:
            min_dist = dist
            nearest = i
    return nearest

def near_shed(x, z, max_distance=70):
    dist = math.sqrt((x - shed_pos[0])**2 + (z - shed_pos[1])**2)
    return dist < max_distance

def near_tractor(x, z, max_distance=50):
    dist = math.sqrt((x - tractor_pos[0])**2 + (z - tractor_pos[1])**2)
    return dist < max_distance

def find_nearest_crop_for_crow(crow_x, crow_y):
    nearest = None
    min_dist = float('inf') 

    for i in range(len(plant_spots)):
        spot = plant_spots[i]
        spot_x = spot[0]
        spot_z = spot[1]
        growth_stage = spot[3]
        if growth_stage > 1:
            dist = math.sqrt((crow_x - spot_x)**2 + (crow_y - spot_z)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = i

    if nearest is not None:
        return plant_spots[nearest][0], plant_spots[nearest][1]
    else:
        return 0, 0

def spawn_crow():
    edge = random.randint(0, 3)
    if edge == 0:
        x = random.uniform(-GRID_LENGTH, GRID_LENGTH)
        y = GRID_LENGTH
    elif edge == 1:
        x = GRID_LENGTH
        y = random.uniform(-GRID_LENGTH, GRID_LENGTH)
    elif edge == 2:
        x = random.uniform(-GRID_LENGTH, GRID_LENGTH)
        y = -GRID_LENGTH
    else:
        x = -GRID_LENGTH
        y = random.uniform(-GRID_LENGTH, GRID_LENGTH)
    target_x = random.uniform(-GRID_LENGTH/2, GRID_LENGTH/2)
    target_y = random.uniform(-GRID_LENGTH/2, GRID_LENGTH/2)
    crows.append([x, y, 50 + random.uniform(20, 40), 15, 0, crow_max_health, target_x, target_y])


def fire_bullet():
    global farmer_angle
    if arm_mode == "shoot":
        angle_rad = math.radians(farmer_angle)

        gun_offset_x = -30 * math.sin(angle_rad)
        gun_offset_y = 30 * math.cos(angle_rad)

        bullet_x = farmer_pos[0] + gun_offset_x
        bullet_y = farmer_pos[1] + gun_offset_y
        bullet_z = farmer_pos[2] + 30
        bullets.append([bullet_x, bullet_y, bullet_z, farmer_angle, 0])


def check_collisions():
    global score, storage_capacity
    bullets_to_remove = []
    crows_to_remove = []
    spots_to_reset = [] 

    for b_idx, bullet in enumerate(bullets):
        bullet_x, bullet_y, bullet_z = bullet[0], bullet[1], bullet[2]

        if b_idx in bullets_to_remove:
            continue

        for c_idx, crow in enumerate(crows):
            if c_idx in crows_to_remove:
                continue

            crow_x, crow_y, crow_z, crow_size = crow[0], crow[1], crow[2], crow[3]
            actual_crow_size = crow_size * (0.8 + 0.2 * math.sin(crow[4])) 

            distance = math.sqrt((bullet_x - crow_x)**2 +
                                 (bullet_y - crow_y)**2 +
                                 (bullet_z - crow_z)**2)

            if distance < (actual_crow_size + bullet_size / 2):
                if b_idx not in bullets_to_remove:
                    bullets_to_remove.append(b_idx)

                crow[5] -= 25 

                if crow[5] <= 0 and c_idx not in crows_to_remove:
                    crows_to_remove.append(c_idx)
                    score += 10 

    for idx in sorted(bullets_to_remove, reverse=True):
        del bullets[idx]

    for c_idx, crow in enumerate(crows):
        if c_idx in crows_to_remove:
            continue

        crow_x, crow_y, crow_z, crow_size = crow[0], crow[1], crow[2], crow[3]
        actual_crow_size = crow_size * (0.8 + 0.2 * math.sin(crow[4]))


        for spot_idx, spot in enumerate(plant_spots):
            spot_x, spot_z, crop_type, growth_stage, health, harvest_timer = spot
            if growth_stage > 1:
                distance_to_crop = math.sqrt((crow_x - spot_x)**2 + (crow_y - spot_z)**2)
                if distance_to_crop < (actual_crow_size + 5):
                    spot[4] -= crow_damage * 0.01
                    if spot[4] <= 0 and spot_idx not in spots_to_reset:
                        spots_to_reset.append(spot_idx)

    for idx in spots_to_reset:
        plant_spots[idx][3] = 0
        plant_spots[idx][4] = crop_health
        plant_spots[idx][5] = 0

    for idx in sorted(crows_to_remove, reverse=True):
        del crows[idx]




def update_game_state():
    global farmer_pos, farmer_angle, camera_pos, camera_mode, arm_mode
    global bullets, crows, plant_spots, score, next_crow_spawn, game_start_time
    global keys_pressed, using_tractor, farmer_speed, shed_door_open, storage_capacity
    global mature_crops_count 
    global crop_collision_radius, farmer_collision_radius 

    current_time = time.time()
    delta_time = 0.016 # 60 FPS


    count = 0
    for spot in plant_spots:
        if spot[3] == 3: 
            count += 1
    mature_crops_count = count

    move_speed = farmer_speed * 2 if using_tractor else farmer_speed
    angle_rad = math.radians(farmer_angle)
    move_dx = math.cos(angle_rad) * move_speed
    move_dy = math.sin(angle_rad) * move_speed

    potential_x, potential_y = farmer_pos[0], farmer_pos[1]
    if keys_pressed.get(b'w', False):
        potential_x += move_dx
        potential_y += move_dy
    if keys_pressed.get(b's', False):
        potential_x -= move_dx
        potential_y -= move_dy

    can_move_x = True
    can_move_y = True
    if not using_tractor:
        for spot in plant_spots:
            if spot[3] > 0:
                spot_x, spot_z = spot[0], spot[1]
                dist_sq = (potential_x - spot_x)**2 + (farmer_pos[1] - spot_z)**2

                if dist_sq < (farmer_collision_radius + crop_collision_radius)**2:
                    can_move_x = False


                dist_sq = (farmer_pos[0] - spot_x)**2 + (potential_y - spot_z)**2
                if dist_sq < (farmer_collision_radius + crop_collision_radius)**2:
                    can_move_y = False
                if not can_move_x and not can_move_y:
                    break

    final_x, final_y = farmer_pos[0], farmer_pos[1]
    if can_move_x:
        final_x = potential_x
    if can_move_y:
        final_y = potential_y

    farmer_pos[0] = max(-GRID_LENGTH, min(GRID_LENGTH, final_x))
    farmer_pos[1] = max(-GRID_LENGTH, min(GRID_LENGTH, final_y))

    if keys_pressed.get(b'a', False):
        farmer_angle += 3 
    if keys_pressed.get(b'd', False):
        farmer_angle -= 3 
    farmer_angle %= 360

    bullets_to_remove = []
    for i, bullet in enumerate(bullets):
        bullet_angle_rad = math.radians(bullet[3])
        bullet[0] += math.cos(bullet_angle_rad) * bullet_speed
        bullet[1] += math.sin(bullet_angle_rad) * bullet_speed
        bullet[4] += 1
        if bullet[4] > bullet_lifetime or \
           abs(bullet[0]) > GRID_LENGTH * 1.5 or \
           abs(bullet[1]) > GRID_LENGTH * 1.5:
            bullets_to_remove.append(i)
    for idx in sorted(bullets_to_remove, reverse=True):
        del bullets[idx]



    crows_to_remove = []
    for i, crow in enumerate(crows):

        crow_x, crow_y, crow_z, size, phase, health, target_x, target_y = crow
        nearest_crop_x, nearest_crop_y = find_nearest_crop_for_crow(crow_x, crow_y)
        current_target_x, current_target_y = target_x, target_y
        if nearest_crop_x is not None:
            current_target_x, current_target_y = nearest_crop_x, nearest_crop_y
        target_angle = math.atan2(current_target_y - crow_y, current_target_x - crow_x)
        crow[0] += math.cos(target_angle) * crow_speed
        crow[1] += math.sin(target_angle) * crow_speed
        crow[2] = 50 + 10 * math.sin(phase * 1.5)
        crow[4] = (crow[4] + delta_time * 5) % (2 * math.pi)
        if abs(crow[0]) > GRID_LENGTH * 1.5 or abs(crow[1]) > GRID_LENGTH * 1.5:
             crows_to_remove.append(i)
    for idx in sorted(crows_to_remove, reverse=True):
        del crows[idx]

    for spot in plant_spots:
        if 0 < spot[3] < 3:
            spot[5] += delta_time
            if spot[5] >= crop_growth_time:
                spot[3] += 1
                spot[5] = 0


    if current_time > next_crow_spawn:
        spawn_crow()
        global crow_spawn_interval
        crow_spawn_interval = max(5, crow_spawn_interval * 0.98)
        next_crow_spawn = current_time + crow_spawn_interval

    shed_door_open = near_shed(farmer_pos[0], farmer_pos[1])
    check_collisions()


    if camera_mode == "third_person":
        offset_dist = 150 if using_tractor else 100
        cam_offset_x = -offset_dist * math.cos(angle_rad)
        cam_offset_y = -offset_dist * math.sin(angle_rad)
        cam_height = 80 if using_tractor else 60
        look_target_z = farmer_pos[2] + (30 if not using_tractor else 20)
        camera_pos = (farmer_pos[0] + cam_offset_x,
                      farmer_pos[1] + cam_offset_y,
                      look_target_z + cam_height)
    elif camera_mode == "first_person":
        head_height = 60
        forward_offset = 5
        cam_x = farmer_pos[0] + forward_offset * math.cos(angle_rad)
        cam_y = farmer_pos[1] + forward_offset * math.sin(angle_rad)
        cam_z = farmer_pos[2] + head_height
        camera_pos = (cam_x, cam_y, cam_z)


def display():
    global camera_pos, farmer_pos, farmer_angle, camera_mode, arm_mode, score
    global storage_capacity, max_storage, using_tractor
    global mature_crops_count, farmer_inventory 
    glClearColor(0.4, 0.7, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    try:
        global width, height
        aspect = width / height if height > 0 else 1
    except Exception:
        aspect = 1000 / 800
    gluPerspective(FOV_Y, aspect, 1.0, GRID_LENGTH * 4)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_mode == "first_person":
        angle_rad = math.radians(farmer_angle)
        look_offset = 20
        target_x = camera_pos[0] + look_offset * math.cos(angle_rad)
        target_y = camera_pos[1] + look_offset * math.sin(angle_rad)
        target_z = camera_pos[2]
    else: # Third person
        target_x = farmer_pos[0]
        target_y = farmer_pos[1]
        target_z = farmer_pos[2] + (30 if not using_tractor else 20)
    try:
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  target_x, target_y, target_z,              
                  0, 0, 1)                                  
    except Exception as e:
        print(f"Error during gluLookAt: {e}")
        gluLookAt(0, -100, 100, 0, 0, 0, 0, 0, 1) 

    draw_clouds()
    draw_ground()
    draw_crops()
    draw_bullets()
    draw_crows()
    draw_storage_shed()
    draw_tractor()

    if not using_tractor and camera_mode != "first_person":
        draw_farmer()

    draw_text(10, 770, f"Score: {score}")
    mode_text = f"Mode: {arm_mode.upper()}"
    if using_tractor:
        mode_text += " (IN TRACTOR)"
    draw_text(10, 740, mode_text)
    draw_text(10, 710, f"Storage: {storage_capacity}/{max_storage}")
    draw_text(10, 680, f"Inventory: {farmer_inventory}")
    draw_text(10, 650, f"Mature Crops: {mature_crops_count}")

    prompt_y = 620 
    if not using_tractor:
        if near_shed(farmer_pos[0], farmer_pos[1]):
            draw_text(10, prompt_y, "[E] Store from Inventory") 
        elif near_tractor(farmer_pos[0], farmer_pos[1]):
            draw_text(10, prompt_y, "[T] Enter Tractor")
        else:
             spot_idx = find_nearest_spot(farmer_pos[0], farmer_pos[1], max_distance=35)
             if spot_idx is not None and plant_spots[spot_idx][3] == 3:
                 draw_text(10, prompt_y, "[H] Harvest Crop")

    elif using_tractor:
         draw_text(10, prompt_y, "[T] Exit Tractor")

    draw_text(10, 10, f"Camera: {camera_mode.upper()}")


    glutSwapBuffers()


def keyboard(key, x, y):
    global keys_pressed, arm_mode, farmer_pos, plant_spots, score, using_tractor
    global storage_capacity, max_storage, crop_health
    global farmer_inventory 

    keys_pressed[key.lower()] = True
    if key == b' ': 
        if arm_mode == "plant" and not using_tractor:
            spot_idx = find_nearest_spot(farmer_pos[0], farmer_pos[1], max_distance=40)
            if spot_idx is not None:
                if plant_spots[spot_idx][3] == 0:
                    plant_spots[spot_idx][3] = 1 
                    plant_spots[spot_idx][4] = crop_health
                    plant_spots[spot_idx][5] = 0
                    print(f"Planted {plant_spots[spot_idx][2]} at spot {spot_idx}")
                else:
                    print(f"Spot {spot_idx} is already planted (Stage: {plant_spots[spot_idx][3]})")
            else:
                print("No suitable spot nearby to plant.")

    elif key.lower() == b'm': 
        arm_mode = "shoot" if arm_mode == "plant" else "plant"
        print(f"Switched mode to: {arm_mode}")

    elif key.lower() == b'h': 
         if arm_mode == "plant" and not using_tractor:
             spot_idx = find_nearest_spot(farmer_pos[0], farmer_pos[1], max_distance=35)
             if spot_idx is not None:
                 if plant_spots[spot_idx][3] == 3:
                     print(f"Harvested {plant_spots[spot_idx][2]} from spot {spot_idx} into inventory.")
                     plant_spots[spot_idx][3] = 0
                     plant_spots[spot_idx][4] = crop_health
                     plant_spots[spot_idx][5] = 0
                     farmer_inventory += 1
                 else:
                    print(f"Cannot harvest spot {spot_idx} with [H] - Stage: {plant_spots[spot_idx][3]}")
             else:
                 print("No mature crop nearby to harvest with [H]")
    elif key.lower() == b'e':
        if near_shed(farmer_pos[0], farmer_pos[1]) and not using_tractor:
            if farmer_inventory > 0:
                can_store = max_storage - storage_capacity
                amount_to_store = min(farmer_inventory, can_store)

                if amount_to_store > 0:
                    storage_capacity += amount_to_store
                    farmer_inventory -= amount_to_store
                    score += amount_to_store 
                    print(f"Stored {amount_to_store} units. Inventory: {farmer_inventory}. Storage: {storage_capacity}/{max_storage}")
                else:
                    print("Shed is full! Cannot store.")
            else:
                print("Inventory is empty. Harvest crops first [H].")
        elif using_tractor:
            print("Cannot interact with shed while in the tractor.")
        elif not near_shed(farmer_pos[0], farmer_pos[1]):
             print("You are not near the shed.")

    elif key.lower() == b't':
        if not using_tractor and near_tractor(farmer_pos[0], farmer_pos[1]):
            using_tractor = True
            print("Entered Tractor")
        elif using_tractor:
            using_tractor = False
            angle_rad = math.radians(farmer_angle)
            farmer_pos[0] += 15 * math.cos(angle_rad + math.pi/2)
            farmer_pos[1] += 15 * math.sin(angle_rad + math.pi/2)
            print("Exited Tractor")

    elif key.lower() == b'c':

        global camera_mode
        camera_mode = "first_person" if camera_mode == "third_person" else "third_person"
        print(f"Switched camera to: {camera_mode}")

def keyboardUp(key, x, y):
    """ Handles key release events. """
    global keys_pressed
    keys_pressed[key.lower()] = False



def mouse(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if arm_mode == "shoot":
            fire_bullet()


def idle():
    update_game_state()
    glutPostRedisplay()


def reshape(w, h):
    global width, height
    width = w
    height = h
    if h == 0:
        h = 1
    glViewport(0, 0, w, h)

def main():
    glutInit() 
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Farmer's Defense: Crop Guard")
    glutDisplayFunc(display)
    global width, height
    width, height = 1000, 800
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboardUp)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)

    print("Game Started!")
    print("Controls:")
    print(" W/S: Move Forward/Backward")
    print(" A/D: Rotate Left/Right")
    print(" M: Toggle Mode (Plant/Shoot)")
    print(" Space: Plant seed (Plant mode)")
    print(" H: Harvest nearby mature crop (Plant mode)")
    print(" Mouse Left Click: Shoot (Shoot mode)")
    print(" E: Store nearby mature crops in Shed (Plant mode, near Shed)")
    print(" T: Enter/Exit Tractor (near Tractor)")
    print(" C: Toggle Camera (Third/First Person)")

    glutMainLoop()


if __name__ == "__main__":
    main()