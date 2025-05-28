import random
import json
import torch  # Add this import for AI
from ai_player import BattleDiceAIPlayer  # Add this import for AI

# Dice collection definitions
COLLECTIONS = {
    "A": {"dice": [4, 8, 12], "target": 14},
    "B": {"dice": [6, 10, 20], "target": 21}
}

def roll_die(sides):
    return random.randint(1, sides)

def roll_dice(dice):
    return [roll_die(d) for d in dice]

def get_sum(rolls):
    return sum(rolls)

def reroll_choice_manual(player_name, rolls, dice_types, rerolls_left):
    log = []
    while rerolls_left > 0:
        dice_str = ', '.join([f'd{dice_types[i]}: {rolls[i]}' for i in range(len(rolls))])
        print(f"\n{player_name}, current rolls: {dice_str}, sum = {get_sum(rolls)}")
        print(f"You have {rerolls_left} rerolls left.")
        reroll_input = input("Enter index of die to reroll (0-2), or 'n' to stop: ").strip()
        if reroll_input.lower() == 'n':
            break
        if reroll_input not in ['0', '1', '2']:
            print("Invalid input. Try again.")
            continue

        index = int(reroll_input)
        old_val = rolls[index]
        new_val = roll_die(dice_types[index])
        rolls[index] = new_val
        rerolls_left -= 1

        log.append({
            "reroll_index": index,
            "old_val": old_val,
            "new_val": new_val,
            "current_sum": get_sum(rolls),
            "rerolls_left": rerolls_left
        })
    return rolls, rerolls_left, log

def play_turn_manual(player_name, dice_types, rerolls):
    initial_rolls = roll_dice(dice_types)
    log = [{
        "roll": initial_rolls[:],
        "dice": dice_types,
        "sum": get_sum(initial_rolls),
        "rerolls_left": rerolls
    }]

    rerolled, remaining_rerolls, reroll_log = reroll_choice_manual(
        player_name, initial_rolls, dice_types, rerolls
    )

    for step in reroll_log:
        log.append({
            "roll": rerolled[:],
            "dice": dice_types,
            "sum": get_sum(rerolled),
            "rerolls_left": step["rerolls_left"],
            "reroll_info": {
                "index": step["reroll_index"],
                "old": step["old_val"],
                "new": step["new_val"]
            }
        })
    return rerolled, get_sum(rerolled), log

def determine_round_winner(sum_p1, sum_p2, target):
    score1 = sum_p1 if sum_p1 <= target else -1
    score2 = sum_p2 if sum_p2 <= target else -1
    if score1 > score2:
        return 1, 2, 0
    elif score2 > score1:
        return 2, 0, 2
    else:
        return 0, 1, 1

def choose_collection():
    while True:
        print("Choose dice collection:")
        print("A: d4, d8, d12 — aim ≤ 14")
        print("B: d6, d10, d20 — aim ≤ 21")
        choice = input("Enter A or B: ").strip().upper()
        if choice in COLLECTIONS:
            return COLLECTIONS[choice], choice
        print("Invalid choice. Try again.")

def print_rolls_with_types(rolls, dice_types):
    roll_str = ', '.join([f'd{dice_types[i]}: {rolls[i]}' for i in range(len(rolls))])
    print(f"Rolls: {roll_str}")

def play_game():
    print("=== BATTLE DICE PvP ===")
    collection, coll_key = choose_collection()
    dice_types = collection["dice"]
    target = collection["target"]

    # Ask user for game mode
    mode = input("Play vs (1) Human or (2) AI? Enter 1 or 2: ").strip()
    use_ai = (mode == '2')
    if use_ai:
        ai_model_path = f"battle_dice_dqn_{coll_key}.pth"
        ai_player = BattleDiceAIPlayer(dice_types, target, ai_model_path, max_rerolls=3)

    print(f"\nBoth players will use Collection {coll_key} — Target: {target}")

    game_log = {
        "collection": coll_key,
        "rounds": [],
        "final_score": {"Player 1": 0, "Player 2": 0}
    }

    # Alternating player order
    player_order = ["Player 1", "Player 2"]

    for round_num in range(1, 8):
        print(f"\n--- Round {round_num} ---")
        p1, p2 = player_order

        # Assign reroll limits: first gets 3, second gets 2
        rerolls = {p1: 3, p2: 2}

        # Play turns
        if use_ai:
            # Determine which player is AI for this round
            if p1 == "Player 1":
                rolls_1, sum_1, log_1 = play_turn_manual(p1, dice_types, rerolls[p1])
                print_rolls_with_types(rolls_1, dice_types)
                rolls_2, sum_2, log_2 = ai_player.play_turn(p2, dice_types, rerolls[p2])
                print(f"{p2} (AI) turn:")
                for step in log_2:
                    if 'reroll_info' in step:
                        idx = step['reroll_info']['index']
                        old = step['reroll_info']['old']
                        new = step['reroll_info']['new']
                        print(f"AI rerolled die {idx} (d{dice_types[idx]}) from {old} to {new} (sum={step['sum']}, rerolls left={step['rerolls_left']})")
                print_rolls_with_types(rolls_2, dice_types)
            else:
                rolls_1, sum_1, log_1 = ai_player.play_turn(p1, dice_types, rerolls[p1])
                print(f"{p1} (AI) turn:")
                for step in log_1:
                    if 'reroll_info' in step:
                        idx = step['reroll_info']['index']
                        old = step['reroll_info']['old']
                        new = step['reroll_info']['new']
                        print(f"AI rerolled die {idx} (d{dice_types[idx]}) from {old} to {new} (sum={step['sum']}, rerolls left={step['rerolls_left']-1})")
                print_rolls_with_types(rolls_1, dice_types)
                rolls_2, sum_2, log_2 = play_turn_manual(p2, dice_types, rerolls[p2])
                print_rolls_with_types(rolls_2, dice_types)
        else:
            rolls_1, sum_1, log_1 = play_turn_manual(p1, dice_types, rerolls[p1])
            print_rolls_with_types(rolls_1, dice_types)
            rolls_2, sum_2, log_2 = play_turn_manual(p2, dice_types, rerolls[p2])
            print_rolls_with_types(rolls_2, dice_types)

        winner, p1_pts, p2_pts = determine_round_winner(
            sum_1 if p1 == "Player 1" else sum_2,
            sum_2 if p2 == "Player 2" else sum_1,
            target
        )

        game_log["final_score"]["Player 1"] += p1_pts
        game_log["final_score"]["Player 2"] += p2_pts

        round_data = {
            "round": round_num,
            p1: {"log": log_1, "final_sum": sum_1 if p1 == "Player 1" else sum_2},
            p2: {"log": log_2, "final_sum": sum_2 if p2 == "Player 2" else sum_1},
            "winner": f"Player {winner}" if winner else "Draw"
        }

        print(f"\n=> {p1} final sum: {round_data[p1]['final_sum']}")
        print(f"=> {p2} final sum: {round_data[p2]['final_sum']}")
        print(f"=> Round Winner: {'Draw' if winner == 0 else f'Player {winner}'}")

        game_log["rounds"].append(round_data)

        # Alternate order
        player_order.reverse()

    # Final results
    print("\n=== FINAL SCORES ===")
    p1_score = game_log["final_score"]["Player 1"]
    p2_score = game_log["final_score"]["Player 2"]
    print(f"Player 1: {p1_score} points")
    print(f"Player 2: {p2_score} points")
    if p1_score > p2_score:
        print("🏆 Player 1 wins the game!")
    elif p2_score > p1_score:
        print("🏆 Player 2 wins the game!")
    else:
        print("🤝 The game is a draw!")

    # Save log
    with open("battle_dice_pvp_log.json", "w") as f:
        json.dump(game_log, f, indent=2)
    print("Game log saved to 'battle_dice_pvp_log.json'.")

if __name__ == "__main__":
    play_game()
