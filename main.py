import pygame
import math
import random

pygame.init()

# Konstanta & Setup
WIDTH, HEIGHT = 1912 / 2, 1200 / 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orb")
clock = pygame.time.Clock()

G = 2.0
px_per_AU = 27
dt = 0.09
softening = 1e-4

BLACK = (5, 5, 10)
WHITE = (240, 240, 240)
YELLOW = (255, 230, 60)
PLANET_COLORS = [
    (200, 190, 170),
    (220, 180, 100),
    (100, 149, 237),
    (255, 120, 120),
    (200, 150, 120),
    (200, 180, 120),
    (160, 220, 220),
    (120, 160, 240),
]

planet_data = [
    ("Mercury", 2.387, 1.66e-7, 2),
    ("Venus", 2.723, 2.45e-6, 4),
    ("Earth", 4.000, 3.00e-6, 5),
    ("Mars", 4.524, 3.23e-7, 3),
    ("Jupiter", 8.203, 9.54e-4, 10),
    ("Saturn", 12.537, 2.86e-4, 8),
    ("Uranus", 14.191, 4.36e-5, 7),
    ("Neptune", 20.07, 5.15e-5, 6),
]
num_meteors = 120
for _ in range(num_meteors):
    dist = random.uniform(6.0, 8.0)
    angle = random.uniform(0, 2 * math.pi)

    name = f"meteor-{_}"
    mass = random.uniform(0.1e-7, 0.5e-7)
    radius = random.randint(1, 2)
    planet_data.append((name, dist, mass, radius))
mass_sun = 1.0


class Body:
    def __init__(self, name, x, y, mass, color, radius=5):
        self.name = name
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.ax = 0
        self.ay = 0
        self.mass = mass
        self.color = color
        self.radius = radius * 2
        self.trail = []

    def apply_gravity(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        r2 = dx * dx + dy * dy + softening
        r = math.sqrt(r2)
        f = G * self.mass * other.mass / r2
        fx = f * dx / r
        fy = f * dy / r
        self.ax += fx / self.mass
        self.ay += fy / self.mass

    def leapfrog_update(self, dt):
        self.vx += 0.5 * self.ax * dt
        self.vy += 0.5 * self.ay * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.ax = 0
        self.ay = 0

    def finalize_velocity(self, dt):
        self.vx += 0.5 * self.ax * dt
        self.vy += 0.5 * self.ay * dt

    def draw(self, screen, bx, by):
        sx = WIDTH / 2 + (self.x - bx) * px_per_AU
        sy = HEIGHT / 2 + (self.y - by) * px_per_AU
        pygame.draw.circle(screen, self.color, (int(sx), int(sy)), self.radius)
        if "meteor" not in self.name:
            self.trail.append((sx, sy))
            if len(self.trail) > 200:
                self.trail.pop(0)
            if len(self.trail) > 2:
                pygame.draw.lines(screen, (100, 100, 100), False, self.trail, 1)

        if self.name == "Saturn":
            ring_color = (200, 200, 150)
            self.draw_ring(
                screen,
                sx,
                sy,
                int(self.radius + 4),
                int(self.radius * 2),
                ring_color,
            )

    def draw_ring(self, screen, x, y, inner_radius, outer_radius, color):
        for r in range(inner_radius, outer_radius):
            pygame.draw.circle(screen, color, (int(x), int(y)), r, 1)


# Buat Sun
sun = Body("Sun", 0, 0, mass_sun, YELLOW, 14)
bodies = [sun]

planet_color_index = 0
for i, (name, a, m, r) in enumerate(planet_data):
    angle = random.uniform(0, 2 * math.pi)
    x = math.cos(angle) * (a)
    y = math.sin(angle) * (a)

    if "Uranus" in name:
        tilt_angle = math.radians(15)
        ellipse_factor = 1.2
        x = math.cos(angle) * a
        y = math.sin(angle) * a * ellipse_factor

        x_rot = x * math.cos(tilt_angle) - y * math.sin(tilt_angle)
        y_rot = x * math.sin(tilt_angle) + y * math.cos(tilt_angle)
        x, y = x_rot, y_rot

    if "meteor" in name:
        color = (130, 130, 130)
    else:
        color = PLANET_COLORS[planet_color_index % len(PLANET_COLORS)]
        planet_color_index += 1
    b = Body(name, x, y, m, color, r)
    if "Uranus" in name:
        v = math.sqrt(G * sun.mass / a) * 0.95
    else:
        v = math.sqrt(G * sun.mass / a)
    b.vx = -v * math.sin(angle)
    b.vy = v * math.cos(angle)
    bodies.append(b)

earth = next(b for b in bodies if b.name == "Earth")

total_px = sum(b.vx * b.mass for b in bodies)
total_py = sum(b.vy * b.mass for b in bodies)
sun.vx = -total_px / sun.mass
sun.vy = -total_py / sun.mass

running = True
paused = False

while running:
    clock.tick(90)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                paused = not paused

    if not paused:
        for b in bodies:
            b.leapfrog_update(dt)

        for i, a in enumerate(bodies):
            for j, b in enumerate(bodies):
                if i == j:
                    continue
                a.apply_gravity(b)

        for b in bodies:
            b.finalize_velocity(dt)

    total_mass = sum(b.mass for b in bodies)
    bx = sum(b.x * b.mass for b in bodies) / total_mass
    by = sum(b.y * b.mass for b in bodies) / total_mass

    screen.fill(BLACK)
    for b in bodies:
        b.draw(screen, bx, by)

    pygame.display.flip()

pygame.quit()
