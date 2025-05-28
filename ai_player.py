import random
import torch
import numpy as np
from train_ai import DQN

def roll_die(sides):
    return random.randint(1, sides)

def roll_dice(dice):
    return [roll_die(d) for d in dice]

class BattleDiceAIPlayer:
    def __init__(self, dice_types, target, model_path, max_rerolls=3):
        self.dice_types = dice_types
        self.target = target
        self.max_rerolls = max_rerolls
        self.model = DQN(input_dim=8, output_dim=4)
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        self.model.eval()
        self.max_side = max(dice_types)

    def get_state(self, rolls, rerolls_left):
        rolls_norm = [r / self.max_side for r in rolls]
        rerolls_norm = [rerolls_left / self.max_rerolls]
        dice_norm = [d / self.max_side for d in self.dice_types]
        target_norm = [self.target / (self.max_side * len(self.dice_types))]
        state = np.array(rolls_norm + rerolls_norm + dice_norm + target_norm, dtype=np.float32)
        return state

    def play_turn(self, player_name, dice_types, rerolls):
        rolls = roll_dice(dice_types)
        log = [{
            "roll": rolls[:],
            "dice": dice_types,
            "sum": sum(rolls),
            "rerolls_left": rerolls
        }]
        rerolls_left = rerolls
        while rerolls_left > 0:
            state = self.get_state(rolls, rerolls_left)
            state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                q_values = self.model(state_t)
                action = q_values.argmax().item()
            if action == 3:
                break
            old_val = rolls[action]
            rolls[action] = roll_die(dice_types[action])
            rerolls_left -= 1
            log.append({
                "roll": rolls[:],
                "dice": dice_types,
                "sum": sum(rolls),
                "rerolls_left": rerolls_left,
                "reroll_info": {
                    "index": action,
                    "old": old_val,
                    "new": rolls[action]
                }
            })
        return rolls, sum(rolls), log
