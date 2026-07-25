import random
import math
from engine.event_bus import event_bus

# Node Return Statuses
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
RUNNING = "RUNNING"

class Node:
    def run(self, context) -> str:
        raise NotImplementedError

class Selector(Node):
    def __init__(self, children):
        self.children = children

    def run(self, context) -> str:
        for child in self.children:
            status = child.run(context)
            if status != FAILURE:
                return status
        return FAILURE

class Sequence(Node):
    def __init__(self, children):
        self.children = children

    def run(self, context) -> str:
        for child in self.children:
            status = child.run(context)
            if status != SUCCESS:
                return status
        return SUCCESS

# Condition Nodes
class CheckDragged(Node):
    def run(self, context) -> str:
        if context.get("is_dragged", False):
            return SUCCESS
        return FAILURE

class CheckSystemIdle(Node):
    def run(self, context) -> str:
        if context.get("system_idle_time", 0.0) > 40.0:
            return SUCCESS
        return FAILURE

class CheckMouseNear(Node):
    def run(self, context) -> str:
        if context.get("global_ctrl_held", False):
            return FAILURE

        mx, my = context["mouse_pos"]
        bx = context["buddy_pos"][0] + context["buddy_width"] / 2
        by = context["buddy_pos"][1] + context["buddy_height"] / 2
        
        dist = math.hypot(mx - bx, my - by)
        fear_dist = context["personality"].cursor_fear_dist
        
        mvx, mvy = context.get("mouse_vel", (0.0, 0.0))
        m_speed = math.hypot(mvx, mvy)
        
        if m_speed > 100.0:
            dx = bx - mx
            dy = by - my
            d_len = math.hypot(dx, dy)
            if d_len > 0:
                dx /= d_len
                dy /= d_len
                dot = (mvx * dx + mvy * dy)
                if dot > 80.0:
                    fear_dist += min(80.0, dot * 0.1)

        if dist < fear_dist:
            context["mood"].trigger_fear(0.02)
            return SUCCESS
        return FAILURE

# Action Nodes
class DraggedAction(Node):
    def run(self, context) -> str:
        context["animation"] = "caught"
        context["target_vx"] = 0.0
        context["target_vy"] = 0.0
        
        if random.random() < 0.02 and not context.get("speech_active", False):
            context["speech"] = "😫 You got me!"
            context["play_sound"] = "caught"
        return SUCCESS

class CtrlCaptureAction(Node):
    def run(self, context) -> str:
        ctrl_held = context.get("global_ctrl_held", False)
        dt = context["dt"]
        
        cooldown = context.get("drop_cooldown", 0.0)
        if cooldown > 0.0:
            cooldown -= dt
            context["drop_cooldown"] = cooldown
            context["target_vx"] = 0.0
            context["target_vy"] = 0.0
            context["animation"] = "surprised"
            return SUCCESS
            
        is_captured = context.get("is_captured", False)
        
        if ctrl_held:
            mx, my = context["mouse_pos"]
            bx, by = context["buddy_pos"]
            char_size = context["buddy_width"]
            
            bcx = bx + char_size / 2
            bcy = by + char_size / 2
            dist = math.hypot(mx - bcx, my - bcy)
            
            if is_captured:
                context["force_position"] = (mx - char_size / 2, my - char_size / 2)
                context["target_vx"] = 0.0
                context["target_vy"] = 0.0
                context["animation"] = "caught"
                return SUCCESS
            else:
                if dist < char_size * 0.75:
                    context["is_captured"] = True
                    context["play_sound"] = "caught"
                    if not context.get("speech_active", False):
                        caught_msgs = [
                            "Okay, you got me!",
                            "Hey! 😆",
                            "Fine... you win.",
                            "Don't drop me!",
                            "Where are we going?",
                            "Easy there!",
                            "You caught me!"
                        ]
                        context["speech"] = random.choice(caught_msgs)
                    context["force_position"] = (mx - char_size / 2, my - char_size / 2)
                    context["target_vx"] = 0.0
                    context["target_vy"] = 0.0
                    context["animation"] = "caught"
                else:
                    context["target_vx"] = 0.0
                    context["target_vy"] = 0.0
                    context["animation"] = "surprised"
                return SUCCESS
        else:
            if is_captured:
                bx, by = context["buddy_pos"]
                char_size = context["buddy_width"]
                context["is_captured"] = False
                context["drop_cooldown"] = 0.8
                context["target_vx"] = 0.0
                context["target_vy"] = 0.0
                context["animation"] = "surprised"
                context["play_sound"] = "boing"
                
                # Spawn landing impact dust particles
                event_bus.publish("spawn_particles", "dust", bx + char_size / 2, by + char_size, 8)
                
                if not context.get("speech_active", False):
                    release_msgs = [
                        "Freedom! 😄",
                        "See you!",
                        "Bye!",
                        "Catch me again!",
                        "Off I go!",
                        "Zoom!"
                    ]
                    context["speech"] = random.choice(release_msgs)
                return SUCCESS
                
        return FAILURE

class MoveModeAction(Node):
    def run(self, context) -> str:
        target = context.get("move_target")
        if target is None:
            return FAILURE
            
        # Check if collided with walls while moving in Move Mode
        if context.get("collided_left") or context.get("collided_right") or context.get("collided_top") or context.get("collided_bottom"):
            context["target_vx"] = 0.0
            context["target_vy"] = 0.0
            context["animation"] = "happy"
            context["play_sound"] = "greet"
            if not context.get("speech_active", False):
                context["speech"] = "Arrived! 😄"
            event_bus.publish("move_target_reached")
            return SUCCESS
            
        bx, by = context["buddy_pos"]
        tx, ty = target
        
        dx = tx - bx
        dy = ty - by
        dist = math.hypot(dx, dy)
        
        if dist > 15:
            speed = 220.0 if dist > 200 else 100.0
            context["animation"] = "run" if dist > 200 else "walk"
            context["target_vx"] = (dx / dist) * speed
            context["target_vy"] = (dy / dist) * speed
            context["disable_gravity"] = True
        else:
            context["target_vx"] = 0.0
            context["target_vy"] = 0.0
            context["animation"] = "happy"
            context["play_sound"] = "greet"
            if not context.get("speech_active", False):
                context["speech"] = "Arrived! 😄"
            event_bus.publish("move_target_reached")
            
        return SUCCESS

class SleepAction(Node):
    def run(self, context) -> str:
        context["animation"] = "sleep"
        context["target_vx"] = 0.0
        context["target_vy"] = 0.0
        
        if context.get("prev_animation") != "sleep":
            context["play_sound"] = "yawn"
        return SUCCESS

class EscapeAction(Node):
    def run(self, context) -> str:
        reaction = context.get("escaped_reaction")
        dt = context["dt"]
        
        if reaction is None:
            p = context["personality"]
            r = random.random()
            if r < p.greet_chance:
                reaction = "greet"
            elif r < (p.greet_chance + p.approach_chance):
                reaction = "approach"
            else:
                reaction = "run"
            context["escaped_reaction"] = reaction
            context["reaction_timer"] = 3.0
            
        timer = context.get("reaction_timer", 0.0) - dt
        context["reaction_timer"] = timer
        if timer <= 0:
            context["escaped_reaction"] = None
            
        mx, my = context["mouse_pos"]
        bx = context["buddy_pos"][0] + context["buddy_width"] / 2
        by = context["buddy_pos"][1] + context["buddy_height"] / 2
        
        dx = bx - mx
        dy = by - my
        dist = math.hypot(dx, dy)
        
        if reaction == "run":
            context["animation"] = "run"
            run_speed = 350.0 * context["personality"].speed_multiplier
            mvx, mvy = context.get("mouse_vel", (0.0, 0.0))
            m_speed = math.hypot(mvx, mvy)
            if dist < 100:
                run_speed *= 1.4
            if m_speed > 300:
                run_speed *= 1.3
                
            if dist > 0:
                dir_x = dx / dist
                dir_y = dy / dist
            else:
                dir_x = random.choice([-1.0, 1.0])
                dir_y = random.choice([-1.0, 1.0])
                
            # Wall-sliding redirects to prevent getting pinned against screen edges
            if context.get("collided_left") and dir_x < 0:
                dir_x = 0.0
                dir_y = 1.0 if dy >= 0 else -1.0
            elif context.get("collided_right") and dir_x > 0:
                dir_x = 0.0
                dir_y = 1.0 if dy >= 0 else -1.0
                
            if context.get("collided_top") and dir_y < 0:
                dir_y = 0.0
                dir_x = 1.0 if dx >= 0 else -1.0
            elif context.get("collided_bottom") and dir_y > 0:
                dir_y = 0.0
                dir_x = 1.0 if dx >= 0 else -1.0
                
            context["target_vx"] = dir_x * run_speed
            context["target_vy"] = dir_y * run_speed
            context["disable_gravity"] = True
            
            if context.get("prev_animation") != "run":
                context["play_sound"] = "whoosh"
                
                playful_timer = context.get("playful_speech_timer", 0.0)
                if playful_timer <= 0.0 and not context.get("speech_active", False):
                    escape_msgs = [
                        "Catch me if you can! 😜",
                        "Too slow!",
                        "You almost got me!",
                        "Nope! 😂",
                        "Nice try!",
                        "Hehe!",
                        "You can't catch me!",
                        "I'm over here!",
                        "Faster! 😆",
                        "Missed me!",
                        "Wheee!",
                        "Not today!",
                        "Keep trying!",
                        "You'll need faster reflexes!",
                        "So close!"
                    ]
                    context["speech"] = random.choice(escape_msgs)
                    context["playful_speech_timer"] = random.uniform(2.0, 3.0)
                    
        elif reaction == "greet":
            context["animation"] = "wave"
            context["target_vx"] = 0.0
            context["target_vy"] = 0.0
            if context.get("prev_animation") != "wave":
                context["play_sound"] = "greet"
                
                playful_timer = context.get("playful_speech_timer", 0.0)
                if playful_timer <= 0.0 and not context.get("speech_active", False):
                    context["speech"] = random.choice(["Hi Shiva 👋", "Hello!", "Hi 👋"])
                    context["playful_speech_timer"] = random.uniform(2.0, 3.0)
                    context["mood"].trigger_joy(0.15)
                    
        elif reaction == "approach":
            context["animation"] = "walk"
            walk_speed = 100.0 * context["personality"].speed_multiplier
            if dist > 0:
                dir_x = -dx / dist
                dir_y = -dy / dist
            else:
                dir_x, dir_y = 0, 0
            context["target_vx"] = dir_x * walk_speed
            context["target_vy"] = dir_y * walk_speed
            context["disable_gravity"] = True
            
            if dist < 50:
                context["escaped_reaction"] = "run"
                context["reaction_timer"] = 2.0
                
            if context.get("prev_animation") != "walk" and not context.get("speech_active", False):
                playful_timer = context.get("playful_speech_timer", 0.0)
                if playful_timer <= 0.0:
                    context["speech"] = "Hi 👋"
                    context["playful_speech_timer"] = random.uniform(2.0, 3.0)
                
        return SUCCESS

class WanderAction(Node):
    def run(self, context) -> str:
        # Clear escape reaction variables since the mouse is no longer near
        context["escaped_reaction"] = None
        context["reaction_timer"] = 0.0
        
        timer = context.get("wander_timer", 0.0) - context["dt"]
        context["wander_timer"] = timer
        
        current_state = context.get("wander_state", "idle")
        target_pos = context.get("wander_target_pos")
        char_size = context["buddy_width"]
        
        bounds = context.get("bounds", (0, 0, 1920, 1080))
        x_min, y_min, x_max, y_max = bounds
        
        if timer <= 0 or (current_state == "walk" and target_pos is None):
            p = context["personality"]
            r = random.random()
            
            if r < p.idle_chance:
                current_state = "idle"
                context["wander_timer"] = random.uniform(2.0, 5.0)
                context["wander_target_pos"] = None
            elif r < p.idle_chance + p.jump_chance:
                current_state = "jump"
                context["wander_timer"] = random.uniform(1.0, 2.5)
                context["wander_target_pos"] = None
                if context["buddy_on_ground"]:
                    context["jump_force"] = context["jump_height"] * 1.8
                    context["play_sound"] = "boing"
            else:
                current_state = "walk"
                tx = random.randint(x_min + 30, x_max - 30 - char_size)
                ty = random.randint(y_min + 30, y_max - 30 - char_size)
                target_pos = (tx, ty)
                context["wander_target_pos"] = target_pos
                context["wander_timer"] = random.uniform(4.0, 8.0)
                
            context["wander_state"] = current_state
            
        if current_state == "idle":
            context["animation"] = "idle"
            if random.random() < 0.005 and not context.get("speech_active", False):
                context["animation"] = "thinking"
                context["speech"] = random.choice(["Coding again? 😄", "Need coffee? ☕", "Working?"])
            context["target_vx"] = 0.0
            context["target_vy"] = 0.0
            
        elif current_state == "walk":
            context["animation"] = "walk"
            if target_pos:
                # Cancel target walk if hit any screen wall to prevent stuck states
                if context.get("collided_left") or context.get("collided_right") or context.get("collided_top") or context.get("collided_bottom"):
                    context["wander_target_pos"] = None
                    context["wander_state"] = "idle"
                    context["wander_timer"] = random.uniform(1.0, 3.0)
                    context["target_vx"] = 0.0
                    context["target_vy"] = 0.0
                    return SUCCESS
                    
                bx, by = context["buddy_pos"]
                tx, ty = target_pos
                dx = tx - bx
                dy = ty - by
                dist = math.hypot(dx, dy)
                
                if dist > 15:
                    walk_speed = 75.0 * context["personality"].speed_multiplier
                    if context["mood"].get_current_mood_state() == "sleepy":
                        walk_speed *= 0.7
                    context["target_vx"] = (dx / dist) * walk_speed
                    context["target_vy"] = (dy / dist) * walk_speed
                    context["disable_gravity"] = True
                else:
                    context["wander_target_pos"] = None
                    context["wander_state"] = "idle"
                    context["wander_timer"] = random.uniform(1.5, 3.5)
            else:
                context["target_vx"] = 0.0
                context["target_vy"] = 0.0
                
        elif current_state == "jump":
            if context["buddy_on_ground"]:
                context["animation"] = "idle"
                context["target_vx"] = 0.0
                context["target_vy"] = 0.0
            else:
                context["animation"] = "jump"
                walk_speed = 60.0 * context["personality"].speed_multiplier
                drift_dx = context.setdefault("wander_dx", random.choice([-1.0, 1.0]))
                context["target_vx"] = drift_dx * walk_speed

        return SUCCESS

class BuildBehaviourTree:
    @staticmethod
    def build() -> Node:
        return Selector([
            Sequence([
                CheckDragged(),
                DraggedAction()
            ]),
            CtrlCaptureAction(),
            MoveModeAction(),
            Sequence([
                CheckSystemIdle(),
                SleepAction()
            ]),
            Sequence([
                CheckMouseNear(),
                EscapeAction()
            ]),
            WanderAction()
        ])
