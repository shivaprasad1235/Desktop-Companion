class CollisionSolver:
    @staticmethod
    def check_boundaries(x: float, y: float, w: int, h: int, bounds: tuple) -> tuple:
        """
        Clamps the position to the bounds and flags which edges were hit.
        bounds format: (x_min, y_min, x_max, y_max)
        Returns: (clamped_x, clamped_y, hit_left, hit_right, hit_top, hit_bottom)
        """
        x_min, y_min, x_max, y_max = bounds
        
        # Subtract width/height to get right/bottom clamp targets
        max_x = x_max - w
        max_y = y_max - h
        
        hit_left = False
        hit_right = False
        hit_top = False
        hit_bottom = False
        
        clamped_x = x
        clamped_y = y
        
        if x <= x_min:
            clamped_x = x_min
            hit_left = True
        elif x >= max_x:
            clamped_x = max_x
            hit_right = True
            
        if y <= y_min:
            clamped_y = y_min
            hit_top = True
        elif y >= max_y:
            clamped_y = max_y
            hit_bottom = True
            
        return clamped_x, clamped_y, hit_left, hit_right, hit_top, hit_bottom

    @staticmethod
    def predict_collision(x: float, y: float, vx: float, vy: float, w: int, h: int, bounds: tuple, dt: float) -> dict:
        """
        Predicts if a collision will occur in the next dt seconds.
        Returns dictionary of booleans for predicted hits.
        """
        x_min, y_min, x_max, y_max = bounds
        next_x = x + vx * dt
        next_y = y + vy * dt
        
        max_x = x_max - w
        max_y = y_max - h
        
        return {
            "left": next_x < x_min,
            "right": next_x > max_x,
            "top": next_y < y_min,
            "bottom": next_y > max_y
        }
