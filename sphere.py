# sphere.py

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import numpy as np

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 25
NUM_PARTICLES = 1
SPHERE_RADIUS = 1.3
PARTICLE_SIZE = 50
COLOR_CHANGE_SPEED = 0.5

# Constants
NUM_PARTICLES_FILE = "num_particles.txt"

# Read the current NUM_PARTICLES from the file or set it to 1 if the file doesn't exist
try:
    with open(NUM_PARTICLES_FILE, "r") as file:
        NUM_PARTICLES = int(file.read().strip())
except FileNotFoundError:
    NUM_PARTICLES = 1

# Increment the NUM_PARTICLES for the next run
with open(NUM_PARTICLES_FILE, "w") as file:
    file.write(str(NUM_PARTICLES + 1))

# Particle class
class Particle:
    def __init__(self, theta, phi):
        self.theta = theta
        self.phi = phi
        self.animation_speed = np.random.uniform(0.005, 0.02)
        self.color = np.random.rand(3)

    def update(self):
        self.theta += self.animation_speed
        self.phi += self.animation_speed
        self.color = np.array([math.sin(self.theta), math.cos(self.phi), math.sin(self.phi)])

    def get_position(self):
        x = SPHERE_RADIUS * math.sin(self.theta) * math.cos(self.phi)
        y = SPHERE_RADIUS * math.sin(self.theta) * math.sin(self.phi)
        z = SPHERE_RADIUS * math.cos(self.theta)
        return x, y, z


# Sphere class
class Sphere:
    def __init__(self, num_particles=NUM_PARTICLES):
        self.num_particles = num_particles
        self.particles = self.generate_particles(self.num_particles)

    def generate_particles(self, num_particles):
        particles = []
        for _ in range(num_particles):
            theta = np.random.uniform(0, np.pi)
            phi = np.random.uniform(0, 2 * np.pi)
            particles.append(Particle(theta, phi))
        return particles

    def update_particles(self):
        for particle in self.particles:
            particle.update()

    def draw_particles(self):
        glBegin(GL_POINTS)
        for particle in self.particles:
            x, y, z = particle.get_position()
            glColor3fv(particle.color)
            glVertex3f(x, y, z)
        glEnd()
    
    # Add this method to Sphere class
    def get_particles_data(self):
        data = []
        for particle in self.particles:
            x, y, z = particle.get_position()
            color = particle.color.tolist()
            data.append({'x': x, 'y': y, 'z': z, 'color': color})
        return data



# Main class
class MainVisualizer:
    def __init__(self):
        pygame.init()
        pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("BAE visualiser")
        gluPerspective(45, (WIDTH / HEIGHT), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)

        self.sphere = Sphere()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_POINT_SMOOTH)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            self.sphere.update_particles()
            self.sphere.draw_particles()

            pygame.display.flip()
            clock.tick(FPS)


if __name__ == "__main__":
    visualizer = MainVisualizer()
    visualizer.run()

