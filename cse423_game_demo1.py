import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Initialize GLUT window and OpenGL settings
def setup_window():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutCreateWindow(b"Farmer Game")
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.5, 0.7, 0.5, 1)  # Light green background
    gluPerspective(45, 1, 1, 100)  # Set perspective projection
    glTranslatef(0.0, -5.0, -20.0)  # Move the camera back for better view

# Camera and movement variables
camera_position = np.array([0, 5, 20])
camera_angle = 0
first_person_mode = False

# Gun control variables
gun_rotation = 0  # Gun's rotation angle (in degrees)
farmer_position = np.array([0, 0, 0])

# Bullet class
class Bullet:
    def __init__(self, x, y, z, velocity, direction):
        self.position = np.array([x, y, z])  # Starting position of the bullet
        self.velocity = velocity  # Speed of bullet
        self.direction = direction  # Direction in which the bullet moves

    def move(self):
        self.position += self.direction * self.velocity  # Update position based on direction and velocity

    def render(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glColor3f(1, 0, 0)  # Red color for bullets
        glutSolidCube(0.2)  # Bullet represented as a small cube
        glPopMatrix()

# List of bullets
bullets = []

def shoot_bullet():
    global bullets
    bullet_velocity = 0.3  # Speed of the bullet
    direction = np.array([np.sin(np.radians(gun_rotation)), 0, np.cos(np.radians(gun_rotation))])  # Bullet direction based on gun rotation
    new_bullet = Bullet(farmer_position[0], farmer_position[1] + 1.5, farmer_position[2], bullet_velocity, direction)
    bullets.append(new_bullet)

# Crow class (enemy)
class Crow:
    def __init__(self, x, y, z):
        self.position = np.array([x, y, z])  # Position of the crow
        self.size = 1  # Initial size of the crow

    def move(self):
        # Random movement logic
        self.position[0] += np.random.uniform(-0.1, 0.1)
        self.position[2] += np.random.uniform(-0.1, 0.1)

    def render(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glColor3f(0, 0, 0)  # Black color for crows
        glutSolidSphere(self.size, 20, 20)  # Crow represented as a sphere
        glPopMatrix()

# List of crows
crows = []

def spawn_crow():
    x = np.random.uniform(-5, 5)
    y = 0
    z = np.random.uniform(-5, 5)
    crows.append(Crow(x, y, z))

# Crop class (planting and harvesting)
class Crop:
    def __init__(self, x, z, type_of_crop):
        self.position = np.array([x, 0, z])  # Position of the crop
        self.type = type_of_crop  # Type of the crop (e.g., wheat, corn, etc.)
        self.is_planted = False  # Initially, the crop is not planted

    def plant(self):
        self.is_planted = True  # Plant the crop at the position

    def harvest(self):
        self.is_planted = False  # Harvest the crop (remove it)

    def render(self):
        if self.is_planted:
            glPushMatrix()
            glTranslatef(self.position[0], self.position[1], self.position[2])
            glColor3f(0, 1, 0)  # Green color for plants
            glutSolidCube(0.5)  # Crop represented as a small cube
            glPopMatrix()

# List of crops
crops = []

def plant_crop(x, z, type_of_crop):
    new_crop = Crop(x, z, type_of_crop)
    new_crop.plant()
    crops.append(new_crop)

# Function to check bullet collision with crows
def check_collision(bullet, enemy):
    distance = np.linalg.norm(bullet.position - enemy.position)
    if distance < 1.0:  # Collision threshold (adjust as needed)
        return True
    return False

# Toggle camera mode (first-person/third-person)
def toggle_camera_mode(button, state, x, y):
    global first_person_mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_mode = not first_person_mode

# Special key input for camera control
def special_key_input_camera(key, x, y):
    global camera_position, camera_angle
    if key == GLUT_KEY_UP:
        camera_position[1] += 1  # Move camera up
    elif key == GLUT_KEY_DOWN:
        camera_position[1] -= 1  # Move camera down
    elif key == GLUT_KEY_LEFT:
        camera_angle -= 5  # Rotate camera left
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5  # Rotate camera right

# Special key input for gun movement
def special_key_input(key, x, y):
    global gun_rotation
    if key == GLUT_KEY_LEFT:
        gun_rotation -= 5  # Rotate gun to the left
    elif key == GLUT_KEY_RIGHT:
        gun_rotation += 5  # Rotate gun to the right

# Render scene
def render_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Set the camera view based on first-person or third-person mode
    if first_person_mode:
        gluLookAt(farmer_position[0], farmer_position[1] + 1.5, farmer_position[2],  # Camera position
                  farmer_position[0] + np.sin(np.radians(gun_rotation)), farmer_position[1] + 1.5, farmer_position[2] + np.cos(np.radians(gun_rotation)),  # Target point
                  0, 1, 0)  # Up vector
    else:
        # Third-person view (camera behind the farmer)
        gluLookAt(camera_position[0], camera_position[1], camera_position[2],
                  farmer_position[0], farmer_position[1] + 1.5, farmer_position[2],
                  0, 1, 0)

    # Render bullets
    for bullet in bullets:
        bullet.move()
        bullet.render()

    # Render crows (enemies)
    for crow in crows:
        crow.move()
        crow.render()

    # Render crops
    for crop in crops:
        crop.render()

    glutSwapBuffers()

# Main function
def main():
    setup_window()

    # Set up GLUT functions for input and rendering
    glutDisplayFunc(render_scene)
    glutIdleFunc(render_scene)
    glutSpecialFunc(special_key_input_camera)  # Special keys for camera control
    glutKeyboardFunc(special_key_input)  # Special keys for gun control
    glutMouseFunc(toggle_camera_mode)  # Right mouse button to toggle camera view
    glutMainLoop()

# Start the game
if __name__ == "__main__":
    main()
