class Personality:
    def __init__(self, name: str, fear_dist: int, speed: float, wander: float, idle_ch: float, jump_ch: float, run_ch: float, greet_ch: float, approach_ch: float):
        self.name = name
        self.cursor_fear_dist = fear_dist
        self.speed_multiplier = speed
        self.wander_frequency = wander  # seconds between wander decisions
        self.idle_chance = idle_ch
        self.jump_chance = jump_ch
        
        # Probabilities when cursor approaches
        self.run_chance = run_ch
        self.greet_chance = greet_ch
        self.approach_chance = approach_ch

PERSONALITIES = {
    "Friendly": Personality(
        name="Friendly",
        fear_dist=130,
        speed=1.0,
        wander=4.0,
        idle_ch=0.20,
        jump_ch=0.10,
        run_ch=0.50,
        greet_ch=0.40,
        approach_ch=0.10
    ),
    "Shy": Personality(
        name="Shy",
        fear_dist=220,
        speed=1.3,
        wander=5.0,
        idle_ch=0.10,
        jump_ch=0.05,
        run_ch=0.90,
        greet_ch=0.10,
        approach_ch=0.00
    ),
    "Playful": Personality(
        name="Playful",
        fear_dist=170,
        speed=1.1,
        wander=3.0,
        idle_ch=0.15,
        jump_ch=0.25,
        run_ch=0.60,
        greet_ch=0.20,
        approach_ch=0.20
    ),
    "Lazy": Personality(
        name="Lazy",
        fear_dist=80,
        speed=0.6,
        wander=8.0,
        idle_ch=0.40,
        jump_ch=0.02,
        run_ch=0.70,
        greet_ch=0.20,
        approach_ch=0.10
    ),
    "Hyper": Personality(
        name="Hyper",
        fear_dist=180,
        speed=1.5,
        wander=2.0,
        idle_ch=0.05,
        jump_ch=0.40,
        run_ch=0.80,
        greet_ch=0.10,
        approach_ch=0.10
    )
}

def get_personality(name: str) -> Personality:
    return PERSONALITIES.get(name, PERSONALITIES["Friendly"])
