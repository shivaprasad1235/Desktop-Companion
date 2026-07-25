from physics.collisions import CollisionSolver

class PhysicsEngine:
    def __init__(self, x=100.0, y=100.0, w=64, h=64):
        self.x = float(x)
        self.y = float(y)
        self.w = w
        self.h = h
        
        # Velocity vectors
        self.vx = 0.0
        self.vy = 0.0
        
        # Physics parameters
        self.gravity = 980.0       # pixels/s^2
        self.friction = 0.88       # friction coefficient (applied per physics tick)
        self.bounce = 0.20         # bounce elasticity coefficient
        self.max_speed = 600.0     # speed limit in pixels/s
        
        # Toggleable gravity (False allows 2D flying/floating across screen)
        self.use_gravity = False
        self.is_on_ground = True
        self.is_falling = False

    def update(self, dt: float, bounds: tuple) -> dict:
        """
        Updates character position based on forces, gravity/friction, and bounds collisions.
        dt: time elapsed in seconds.
        bounds: (x_min, y_min, x_max, y_max)
        """
        # 1. Apply gravity or vertical friction
        if self.use_gravity:
            self.vy += self.gravity * dt
        else:
            # When gravity is off, apply vertical friction decay just like horizontal
            self.vy *= (self.friction ** (dt * 60.0))
            
        # 2. Limit velocities to max speed
        speed = (self.vx**2 + self.vy**2)**0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vx *= scale
            self.vy *= scale

        # 3. Apply friction/drag (gives smooth momentum decay)
        self.vx *= (self.friction ** (dt * 60.0))
        
        if self.use_gravity:
            # Air resistance
            self.vy *= (0.99 ** (dt * 60.0))
        else:
            # Floating friction decay
            self.vy *= (0.88 ** (dt * 60.0))

        # 4. Update positions
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 5. Handle collisions and clamp position
        new_x, new_y, hit_l, hit_r, hit_t, hit_b = CollisionSolver.check_boundaries(
            self.x, self.y, self.w, self.h, bounds
        )
        
        self.x = new_x
        self.y = new_y

        collisions = {
            "left": hit_l,
            "right": hit_r,
            "top": hit_t,
            "bottom": hit_b
        }

        # 6. Bounce or halt velocities on collision
        if hit_l or hit_r:
            self.vx = -self.vx * self.bounce
            if abs(self.vx) < 5.0:
                self.vx = 0.0
                
        if hit_t:
            if self.use_gravity:
                self.vy = -self.vy * self.bounce
                if abs(self.vy) < 5.0:
                    self.vy = 0.0
            else:
                self.vy = 0.0
                
        if hit_b:
            if self.use_gravity:
                self.vy = -self.vy * self.bounce
                if abs(self.vy) < 15.0:
                    self.vy = 0.0
                    self.is_on_ground = True
                    self.is_falling = False
                    self.use_gravity = False # disable gravity once landed
                else:
                    self.is_on_ground = False
                    self.is_falling = self.vy > 0
            else:
                self.vy = 0.0
                self.is_on_ground = True
                self.is_falling = False
        else:
            if self.use_gravity:
                self.is_on_ground = False
                self.is_falling = self.vy > 0
            else:
                # Without gravity, we can treat the floating state as ground-like for animation trigger purposes
                self.is_on_ground = True
                self.is_falling = False

        return collisions

    def apply_force(self, fx: float, fy: float):
        """Adds to velocity vector."""
        self.vx += fx
        self.vy += fy

    def accelerate_toward(self, target_vx: float, target_vy: float, rate: float, dt: float):
        """Smoothly accelerates horizontal/vertical speed toward target velocities using easing."""
        diff_x = target_vx - self.vx
        self.vx += diff_x * rate * (dt * 60.0)
        
        if not self.use_gravity:
            diff_y = target_vy - self.vy
            self.vy += diff_y * rate * (dt * 60.0)

    def jump(self, force: float):
        """Triggers a vertical jump with active gravity."""
        self.vy = -force
        self.use_gravity = True
        self.is_on_ground = False
        self.is_falling = False
        
    def reset(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.use_gravity = False
        self.is_on_ground = True
        self.is_falling = False
