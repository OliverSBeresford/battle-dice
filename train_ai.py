import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque, namedtuple

# --- Environment & Game Logic ---

class BattleDiceEnv:
    def __init__(self, dice_types, target, max_rerolls_first=3, max_rerolls_second=2):
        self.dice_types = dice_types
        self.target = target
        self.max_rerolls_first = max_rerolls_first
        self.max_rerolls_second = max_rerolls_second
        self.reset()

    def reset(self):
        # Start new round, initial rolls for both players
        self.round = 1
        self.player_order = ["agent", "heuristic"]
        self.scores = {"agent": 0, "heuristic": 0}
        self.rerolls_left = {self.player_order[0]: self.max_rerolls_first,
                             self.player_order[1]: self.max_rerolls_second}
        self.current_player = self.player_order[0]
        self.rolls = {
            "agent": [self.roll_die(d) for d in self.dice_types],
            "heuristic": [self.roll_die(d) for d in self.dice_types]
        }
        self.done = False
        self.turn_done = False
        self.reroll_count = 0
        self.state = self._get_state()
        self.phase = "agent_turn"  # or "heuristic_turn", "round_over"
        return self.state

    def roll_die(self, sides):
        return random.randint(1, sides)

    def _get_state(self):
        # State: current rolls (3 dice), rerolls left, dice types, target
        # Normalize rolls and dice types by max dice side for stable input
        max_side = max(self.dice_types)
        # We'll encode state as numpy float array of shape (12,)
        # [rolls..., rerolls_left, dice_types..., target_norm]
        rolls_norm = [r / max_side for r in self.rolls[self.current_player]]
        rerolls_norm = [self.rerolls_left[self.current_player] / self.max_rerolls_first]
        dice_norm = [d / max_side for d in self.dice_types]
        target_norm = [self.target / (max_side * len(self.dice_types))]
        state = np.array(rolls_norm + rerolls_norm + dice_norm + target_norm, dtype=np.float32)
        return state

    def step(self, action):
        """
        action: int 0,1,2 for reroll that die, or 3 for pass (no reroll)
        Returns: next_state, reward, done, info
        """

        if self.done:
            raise Exception("Episode is done. Call reset().")

        if action == 3:  # pass, end turn
            self.turn_done = True
        else:
            # reroll chosen die if rerolls left
            if self.rerolls_left[self.current_player] > 0:
                old_val = self.rolls[self.current_player][action]
                self.rolls[self.current_player][action] = self.roll_die(self.dice_types[action])
                self.rerolls_left[self.current_player] -= 1
            else:
                # no rerolls left, ignore reroll attempt
                self.turn_done = True

        # Update state
        self.state = self._get_state()

        if self.turn_done:
            if self.phase == "agent_turn":
                self.phase = "heuristic_turn"
                self.current_player = "heuristic"
                self.turn_done = False
                self.state = self._get_state()
                # Heuristic plays immediately:
                self._heuristic_play()
                self.phase = "round_over"
                # Calculate reward for agent
                reward, done = self._calculate_reward()
                self.done = done
                return self.state, reward, self.done, {}

            elif self.phase == "heuristic_turn":
                # Round ends after heuristic turn
                self.phase = "round_over"
                reward, done = self._calculate_reward()
                self.done = done
                return self.state, reward, self.done, {}

        # If turn not done, reward=0, done=False
        return self.state, 0.0, False, {}

    def _heuristic_play(self):
        # Heuristic rerolls intelligently with max rerolls_second
        rerolls_left = self.max_rerolls_second
        rolls = self.rolls["heuristic"]

        # Simple heuristic: reroll highest die if sum too high, or lowest die if sum too low
        for _ in range(rerolls_left):
            current_sum = sum(rolls)
            if current_sum > self.target:
                # reroll highest die to try to reduce sum
                idx = rolls.index(max(rolls))
                rolls[idx] = self.roll_die(self.dice_types[idx])
            elif current_sum < self.target - 4:
                # reroll lowest die to try to increase sum
                idx = rolls.index(min(rolls))
                rolls[idx] = self.roll_die(self.dice_types[idx])
            else:
                break

        self.rolls["heuristic"] = rolls

    def _calculate_reward(self):
        # Reward from agent's perspective at end of round
        agent_sum = sum(self.rolls["agent"])
        heuristic_sum = sum(self.rolls["heuristic"])

        def score(s):
            return s if s <= self.target else -1

        s_agent = score(agent_sum)
        s_heuristic = score(heuristic_sum)

        if s_agent > s_heuristic:
            reward = 2
            done = True
        elif s_agent < s_heuristic:
            reward = -1  # penalty for losing
            done = True
        else:
            reward = 1  # draw
            done = True
        return reward, done


# --- Neural Network for DQN ---

class DQN(nn.Module):
    def __init__(self, input_dim=8, output_dim=4):
        super(DQN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )

    def forward(self, x):
        return self.net(x)


# --- Replay Buffer ---

Transition = namedtuple('Transition', ('state', 'action', 'reward', 'next_state', 'done'))

class ReplayBuffer:
    def __init__(self, capacity=10000):
        self.memory = deque(maxlen=capacity)

    def push(self, *args):
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        batch = random.sample(self.memory, batch_size)
        return Transition(*zip(*batch))

    def __len__(self):
        return len(self.memory)


# --- Training Loop ---

def train_dqn(env, num_episodes=10000, batch_size=64, gamma=0.99, lr=1e-3,
              epsilon_start=1.0, epsilon_end=0.1, epsilon_decay=5000, target_update=100):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    policy_net = DQN().to(device)
    target_net = DQN().to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=lr)
    memory = ReplayBuffer()

    steps_done = 0

    def select_action(state, epsilon):
        nonlocal steps_done
        sample = random.random()
        steps_done += 1
        if sample > epsilon:
            with torch.no_grad():
                state_t = torch.tensor(state, dtype=torch.float32).to(device)
                q_values = policy_net(state_t)
                return q_values.argmax().item()
        else:
            return random.randrange(4)

    epsilon = epsilon_start

    for episode in range(num_episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            action = select_action(state, epsilon)
            next_state, reward, done, _ = env.step(action)
            memory.push(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

            if len(memory) >= batch_size:
                transitions = memory.sample(batch_size)
                batch = Transition(*transitions)

                non_final_mask = torch.tensor(
                    tuple(map(lambda d: not d, batch.done)),
                    device=device, dtype=torch.bool
                )
                non_final_next_states = torch.stack(
                    [torch.tensor(s, dtype=torch.float32).to(device) for s, d in zip(batch.next_state, batch.done) if not d]
                ) if any(non_final_mask) else torch.empty((0, 12), device=device)

                state_batch = torch.stack([torch.tensor(s, dtype=torch.float32).to(device) for s in batch.state])
                action_batch = torch.tensor(batch.action, device=device).unsqueeze(1)
                reward_batch = torch.tensor(batch.reward, device=device, dtype=torch.float32)

                # Compute Q(s_t, a)
                state_action_values = policy_net(state_batch).gather(1, action_batch)

                # Compute V(s_{t+1}) for all next states.
                next_state_values = torch.zeros(batch_size, device=device)
                if non_final_next_states.size(0) > 0:
                    next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0].detach()

                # Compute expected Q values
                expected_state_action_values = (next_state_values * gamma) + reward_batch

                # Compute loss
                loss = nn.MSELoss()(state_action_values.squeeze(), expected_state_action_values)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # Decay epsilon
            epsilon = epsilon_end + (epsilon_start - epsilon_end) * np.exp(-1. * steps_done / epsilon_decay)

        if episode % 500 == 0:
            print(f"Episode {episode} total reward: {total_reward:.2f} epsilon: {epsilon:.2f}")
            # Update target network
            target_net.load_state_dict(policy_net.state_dict())

    # Save trained model
    torch.save(policy_net.state_dict(), "battle_dice_dqn.pth")
    print("Training complete, model saved as battle_dice_dqn.pth")

if __name__ == "__main__":
    # Train and save a DQN for each collection (A and B)
    collections = {
        "A": {"dice": [4, 8, 12], "target": 14},
        "B": {"dice": [6, 10, 20], "target": 21}
    }
    for key, collection in collections.items():
        print(f"\n=== Training DQN for Collection {key} ===")
        env = BattleDiceEnv(collection["dice"], collection["target"])
        train_dqn(env)
        # Rename the saved model to include the collection key
        import os
        os.rename("battle_dice_dqn.pth", f"battle_dice_dqn_{key}.pth")
        print(f"Model for Collection {key} saved as battle_dice_dqn_{key}.pth")
