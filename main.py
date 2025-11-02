import pygame
import math
import random
import requests
from io import BytesIO
from PIL import Image

pygame.init()

# ======================= Setup =======================
WIDTH, HEIGHT = 960, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orbital Simulator (Images + Mouse Camera)")
clock = pygame.time.Clock()

G = 6.67430e-11
dt = 60 * 60 * 24  # 1 hari per frame

BLACK = (5, 5, 10)

# Planet data: nama, jarak (m), massa (kg), radius visual
planet_data = [
    ("Mercury", 5.79e10, 3.30e23, 6),
    ("Venus", 1.082e11, 4.87e24, 8),
    ("Earth", 1.496e11, 5.97e24, 10),
    ("Mars", 2.279e11, 6.42e23, 6),
    ("Jupiter", 7.785e11, 1.90e27, 20),
    ("Saturn", 1.433e12, 5.68e26, 16),
    ("Uranus", 2.872e12, 8.68e25, 14),
    ("Neptune", 4.495e12, 1.02e26, 12),
    ("Moon", 3.844e8, 7.35e22, 4),
]

# Image URLs
planet_urls = {
    "Sun": "https://www.freepnglogos.com/uploads/sun-png/sun-png-aecert-background-and-rationale-physics-36.png",  # perlu diubah ke direct image link
    "Mercury": "https://wallpapers.com/images/hd/planet-mercury-surface-texture-4b3e9dbrmxebdmzw.jpg",
    "Venus": "https://www.pngall.com/wp-content/uploads/11/Venus-PNG-Pic.png",
    "Earth": "https://pngimg.com/uploads/earth/earth_PNG21.png",
    "Mars": "https://pngimg.com/d/mars_planet_PNG28.png",
    "Jupiter": "https://pngimg.com/d/jupiter_PNG17.png",
    "Saturn": "https://www.pngall.com/wp-content/uploads/14/Saturn-PNG-File.png",
    "Uranus": "https://www.pngplay.com/wp-content/uploads/13/Uranus-Transparent-PNG.png",
    "Neptune": "https://www.pngall.com/wp-content/uploads/15/Neptune-PNG-Clipart.png",
    "Moon": "https://pngimg.com/uploads/moon/moon_PNG19.png",
}


# Load images via Pillow
planet_images = {}
for name, url in planet_urls.items():
    try:
        resp = requests.get(url)
        pil = Image.open(BytesIO(resp.content)).convert("RGBA")
        img = pygame.image.fromstring(pil.tobytes(), pil.size, pil.mode)
        planet_images[name] = img
    except Exception as e:
        print(f"Failed to load {name}: {e}")
# Meteor data
num_meteors = 110
meteor_data = []
for _ in range(num_meteors):
    dist = random.uniform(2.279e11, 3.5e11)
    angle = random.uniform(0, 2 * math.pi)
    mass = random.uniform(1e15, 5e15)
    radius = random.uniform(0.1, 0.3)
    meteor_data.append((f"meteor-{_}", dist, mass, radius, angle))


# ======================= Body Class =======================
class Body:
    def __init__(self, name, x, y, mass, radius):
        self.name = name
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.ax = 0
        self.ay = 0
        self.mass = mass
        self.radius = radius
        self.trail = []

    def apply_gravity(self, other, softening=1e9):
        dx = other.x - self.x
        dy = other.y - self.y
        r2 = dx * dx + dy * dy + softening
        r = math.sqrt(r2)
        f = G * self.mass * other.mass / r2
        self.ax += f * dx / r / self.mass
        self.ay += f * dy / r / self.mass

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

    def draw(self, screen, cam_x, cam_y, zoom, zoom_default):
        sx = WIDTH / 2 + (self.x - cam_x) * zoom
        sy = HEIGHT / 2 + (self.y - cam_y) * zoom

        # radius visual ikut zoom
        zoom_radius_factor = 50  # penyesuaian
        r_scaled = max(
            3, int(self.radius * (1 + (zoom - zoom_default) * zoom_radius_factor))
        )

        if self.name in planet_images:
            img = planet_images[self.name]
            img_scaled = pygame.transform.scale(img, (r_scaled * 2, r_scaled * 2))
            screen.blit(img_scaled, (sx - r_scaled, sy - r_scaled))
        else:
            pygame.draw.circle(screen, (200, 200, 200), (int(sx), int(sy)), r_scaled)

        if len(self.trail) > 1:
            pygame.draw.lines(screen, (100, 100, 100), False, self.trail[-100:], 1)
        if "meteor" not in self.name:
            self.trail.append((sx, sy))


# ======================= Create Bodies =======================
mass_sun = 1.989e30
sun = Body("Sun", 0, 0, mass_sun, 28)
bodies = [sun]

# Planets
for name, r, m, rad in planet_data:
    if name == "Moon":
        continue
    x = r
    y = 0
    b = Body(name, x, y, m, rad)
    v = math.sqrt(G * mass_sun / r)
    b.vx = 0
    b.vy = v
    bodies.append(b)

# Meteors
for name, r, m, rad, angle in meteor_data:
    x = r * math.cos(angle)
    y = r * math.sin(angle)
    b = Body(name, x, y, m, rad)
    v = math.sqrt(G * mass_sun / r)
    b.vx = -v * math.sin(angle)
    b.vy = v * math.cos(angle)
    bodies.append(b)

# Moon
earth = next(b for b in bodies if b.name == "Earth")
moon_distance = 3.844e8
moon_mass = 7.35e22
moon = Body("Moon", earth.x + moon_distance, earth.y, moon_mass, 4)
v_moon = math.sqrt(G * earth.mass / moon_distance)
moon.vx = earth.vx
moon.vy = earth.vy + v_moon
bodies.append(moon)

# Center of mass velocity
total_px = sum(b.vx * b.mass for b in bodies)
total_py = sum(b.vy * b.mass for b in bodies)
sun.vx = -total_px / sun.mass
sun.vy = -total_py / sun.mass

# ======================= Camera =======================
cam_x, cam_y = 0, 0
zoom_default = WIDTH / (2 * 4.6e12)
zoom = zoom_default  # zoom awal
dragging = False
last_mouse_pos = (0, 0)
paused = False

# ======================= Main Loop =======================
running = True
while running:
    clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                paused = not paused
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                dragging = True
                last_mouse_pos = e.pos
            elif e.button == 4:
                zoom *= 1.1
            elif e.button == 5:
                zoom /= 1.1
        elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == 1:
                dragging = False
        elif e.type == pygame.MOUSEMOTION:
            if dragging:
                mx, my = e.pos
                dx, dy = mx - last_mouse_pos[0], my - last_mouse_pos[1]
                cam_x -= dx / zoom
                cam_y -= dy / zoom
                last_mouse_pos = (mx, my)

    if not paused:
        for b in bodies:
            b.leapfrog_update(dt)
        for i, a in enumerate(bodies):
            for j, b2 in enumerate(bodies):
                if i != j:
                    a.apply_gravity(b2)
        for b in bodies:
            b.finalize_velocity(dt)

    # Default camera: center of mass
    total_mass = sum(b.mass for b in bodies)
    com_x = sum(b.x * b.mass for b in bodies) / total_mass
    com_y = sum(b.y * b.mass for b in bodies) / total_mass

    screen.fill(BLACK)
    for b in bodies:
        b.draw(
            screen,
            cam_x if dragging or cam_x != 0 else com_x,
            cam_y if dragging or cam_y != 0 else com_y,
            zoom,
            zoom_default,
        )
    pygame.display.flip()

pygame.quit()
