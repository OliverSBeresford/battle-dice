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
        # Gravity torque: only apply to x and z axes (tilt), not y (spin)
        torque_strength = 0.5
        def angle_to_nearest_90(angle):
            return min(abs((angle % 360) % 90), abs(90 - (angle % 90)))
        tx = angle_to_nearest_90(self.rotation_x)
        tz = angle_to_nearest_90(self.rotation_z)
        sign_x = -1 if (self.rotation_x % 180) > 90 else 1
        sign_z = -1 if (self.rotation_z % 180) > 90 else 1
        self.angular_velocity.x += sign_x * tx * torque_strength * time.dt
        self.angular_velocity.z += sign_z * tz * torque_strength * time.dt
        # Do not apply gravity torque to self.angular_velocity.y

        # Ground collision
        if self.y <= 0.25:
            self.y = 0.25

            # Only x and z axes need to be face-aligned for the die to be flat
            if self.velocity.length() < 0.5 and self.angular_velocity.length() < 20:
                for axis, av_axis in zip(['rotation_x', 'rotation_z'], ['x', 'z']):
                    angle = getattr(self, axis)
                    nearest = round(angle / 90) * 90
                    if abs((angle - nearest) % 360) < 10:
                        setattr(self, axis, nearest % 360)
                        setattr(self.angular_velocity, av_axis, 0)
                self.velocity = Vec3(0, 0, 0)
                # If both x and z angular velocities are now 0, mark as grounded (y can still spin)
                if abs(self.angular_velocity.x) < 1e-2 and abs(self.angular_velocity.z) < 1e-2:
                    self.angular_velocity.x = 0
                    self.angular_velocity.z = 0
                    self.angular_velocity.y *= 0.5  # Dampen y spin
                    self.grounded = True
            else:
                # Only dampen angular velocity for x and z axes that are close to face-aligned
                for axis, av_axis in zip(['rotation_x', 'rotation_z'], ['x', 'z']):
                    angle = getattr(self, axis)
                    nearest = round(angle / 90) * 90
                    if abs((angle - nearest) % 360) < 10:
                        # Flip direction of angular velocity for bounce
                        setattr(self.angular_velocity, av_axis, -getattr(self.angular_velocity, av_axis) * 0.5)
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