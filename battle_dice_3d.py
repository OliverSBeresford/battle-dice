import os
os.environ["PANDA3D_DISABLE_SHADERS"] = "1"
from ursina import *
import random

# Dice sides map
DICE_SIDES = {
    'd4': 4,
    'd6': 6,
    'd8': 8,
    'd10': 10,
    'd12': 12,
    'd20': 20,
}

# Parse input like: "d6 2 d20 1"
def parse_input(input_str):
    tokens = input_str.lower().split()
    result = []
    for i in range(0, len(tokens), 2):
        die_type = tokens[i]
        count = int(tokens[i+1])
        if die_type not in DICE_SIDES:
            raise ValueError(f"Unsupported die type: {die_type}")
        result.extend([die_type] * count)
    return result

class Die(Entity):
    def __init__(self, die_type='d6', **kwargs):
        super().__init__(
            model='cube',
            collider='box',
            texture='white_cube',
            scale=0.5,
            color=color.random_color(),
            **kwargs
        )
        self.die_type = die_type
        self.sides = DICE_SIDES[die_type]
        self.velocity = Vec3(0, 0, 0)
        self.angular_velocity = Vec3(0, 0, 0)
        self.grounded = False

    def roll(self):
        self.velocity = Vec3(
            random.uniform(-3, 3),
            random.uniform(5, 10),
            random.uniform(-3, 3)
        )
        self.angular_velocity = Vec3(
            random.uniform(-180, 180),
            random.uniform(-180, 180),
            random.uniform(-180, 180)
        )
        self.grounded = False

    def update(self):
        if self.grounded:
            return

        # Apply motion
        self.position += self.velocity * time.dt
        self.rotation_x += self.angular_velocity.x * time.dt
        self.rotation_y += self.angular_velocity.y * time.dt
        self.rotation_z += self.angular_velocity.z * time.dt

        # Gravity
        self.velocity.y -= 9.8 * time.dt

        # Ground collision
        if self.y <= 0.25:
            self.y = 0.25

            # Check if close to a face-aligned orientation (within 10 degrees of 0, 90, 180, 270, 360)
            def is_face_aligned(angle):
                return any(abs((angle % 90) - x) < 10 or abs((angle % 90) - x + 90) < 10 for x in [0, 90])

            if self.velocity.length() < 0.5 and self.angular_velocity.length() < 20:
                # Snap and zero only axes that are close to face-aligned
                for axis, av_axis in zip(['rotation_x', 'rotation_y', 'rotation_z'], ['x', 'y', 'z']):
                    angle = getattr(self, axis)
                    nearest = round(angle / 90) * 90
                    if abs((angle - nearest) % 360) < 10:
                        setattr(self, axis, nearest % 360)
                        setattr(self.angular_velocity, av_axis, 0)
                self.velocity = Vec3(0, 0, 0)
                # If all angular velocities are now 0, mark as grounded
                if self.angular_velocity.length() < 1e-2:
                    self.angular_velocity = Vec3(0, 0, 0)
                    self.grounded = True
            else:
                # Only dampen angular velocity for axes that are close to face-aligned
                for axis, av_axis in zip(['rotation_x', 'rotation_y', 'rotation_z'], ['x', 'y', 'z']):
                    angle = getattr(self, axis)
                    nearest = round(angle / 90) * 90
                    if abs((angle - nearest) % 360) < 10:
                        setattr(self.angular_velocity, av_axis, getattr(self.angular_velocity, av_axis) * 0.5)
                self.velocity.y *= -0.2
                self.velocity.x *= 0.8
                self.velocity.z *= 0.8

    def get_result(self):
        return random.randint(1, self.sides)  # Placeholder

class DiceRoller:
    def __init__(self, dice_list):
        self.dice = []
        self.dice_list = dice_list
        self.result_shown = False
        self.texts = []

        # Ground plane
        self.ground = Entity(model='plane', collider='box', scale=20, texture='white_cube', texture_scale=(10, 10))
        DirectionalLight(y=2, z=3, shadows=True)
        Sky()

        # Camera: isometric angle
        camera.position = (0, 6, -6)
        camera.look_at(Vec3(0, 0, 0))
        camera.fov = 90

        # Spawn dice
        for i, die_type in enumerate(self.dice_list):
            die = Die(die_type=die_type, position=(i * 0.7 - len(self.dice_list) * 0.35, 3, 0))
            die.roll()
            self.dice.append(die)

    def update(self):
        for die in self.dice:
            die.update()

        if not self.result_shown and all(die.grounded for die in self.dice):
            self.result_shown = True
            total = 0
            for die in self.dice:
                value = die.get_result()
                total += value
                t = Text(
                    text=f'{die.die_type.upper()}: {value}',
                    position=Vec3(*die.position) + Vec3(0, 1, 0),
                    scale=1.5,
                    origin=(0, 0),
                    color=color.black
                )
                self.texts.append(t)
            print(f"Total: {total}")

# === Main ===
if __name__ == '__main__':
    input_str = input("Enter dice to roll (e.g., 'd6 2 d20 1'): ")
    dice_to_roll = parse_input(input_str)
    app = Ursina()
    roller = DiceRoller(dice_to_roll)
    app.update = roller.update
    app.run()