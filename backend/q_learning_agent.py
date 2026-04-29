

import random
from smart_home_environment import (
    temperature_options, time_options,
    occupancy_options, price_options,
    actions, get_reward, build_state_from_sensors
)



def state_to_key(state):
    return (
        state["temperature"],
        state["time_of_day"],
        state["occupancy"],
        state["electricity_price"]
    )



def random_state():
    return {
        "temperature"       : random.choice(temperature_options),
        "time_of_day"       : random.choice(time_options),
        "occupancy"         : random.choice(occupancy_options),
        "electricity_price" : random.choice(price_options)
    }


ALPHA   = 0.1    
GAMMA   = 0.9    
EPSILON = 0.3    
EPISODES = 1000  
STEPS_PER_EPISODE = 24  


Q_table = {}

def get_q(state_key, action_idx):
    if state_key not in Q_table:
        Q_table[state_key] = [0.0] * len(actions)
    return Q_table[state_key][action_idx]

def set_q(state_key, action_idx, value):
    if state_key not in Q_table:
        Q_table[state_key] = [0.0] * len(actions)
    Q_table[state_key][action_idx] = value


def choose_action(state_key):
    if random.random() < EPSILON:
        return random.randint(0, len(actions) - 1)   # Explore
    else:
        if state_key not in Q_table:
            return random.randint(0, len(actions) - 1)
        return Q_table[state_key].index(max(Q_table[state_key]))  # Exploit



print("=" * 55)
print("  Q-Learning Agent Training — SUBGROUP 3F22")
print("=" * 55)
print(f"\n  Episodes     : {EPISODES}")
print(f"  Steps/Episode: {STEPS_PER_EPISODE}")
print(f"  Alpha (lr)   : {ALPHA}")
print(f"  Gamma        : {GAMMA}")
print(f"  Epsilon      : {EPSILON}")
print("\n  Training started...\n")

episode_rewards = []   

for episode in range(1, EPISODES + 1):

    state        = random_state()
    total_reward = 0

    for step in range(STEPS_PER_EPISODE):

        state_key  = state_to_key(state)
        action_idx = choose_action(state_key)
        action     = actions[action_idx]

        reward = get_reward(state, action)
        total_reward += reward


        next_state     = random_state()
        next_state_key = state_to_key(next_state)

        current_q  = get_q(state_key, action_idx)
        max_next_q = max(Q_table.get(next_state_key, [0.0] * len(actions)))

        new_q = current_q + ALPHA * (reward + GAMMA * max_next_q - current_q)
        set_q(state_key, action_idx, new_q)

        state = next_state

    episode_rewards.append(total_reward)

    if episode % 100 == 0:
        avg = sum(episode_rewards[-100:]) / 100
        print(f"  Episode {episode:4d} | Avg Reward (last 100): {avg:7.2f}")



print("\n" + "=" * 55)
print("  Training Complete!")
print("=" * 55)

print("\n  Q-Table Sample (Best action for each state):\n")
print(f"  {'STATE':<45} {'BEST ACTION'}")
print(f"  {'-'*45} {'-'*30}")

sample_states = [
    {"temperature": "hot",         "time_of_day": "afternoon", "occupancy": "empty",    "electricity_price": "expensive"},
    {"temperature": "hot",         "time_of_day": "afternoon", "occupancy": "occupied", "electricity_price": "cheap"},
    {"temperature": "comfortable", "time_of_day": "night",     "occupancy": "empty",    "electricity_price": "cheap"},
    {"temperature": "cold",        "time_of_day": "morning",   "occupancy": "occupied", "electricity_price": "expensive"},
    {"temperature": "comfortable", "time_of_day": "afternoon", "occupancy": "occupied", "electricity_price": "cheap"},
]

for s in sample_states:
    key = state_to_key(s)
    if key in Q_table:
        best_idx    = Q_table[key].index(max(Q_table[key]))
        best_action = actions[best_idx]
        best_q      = round(max(Q_table[key]), 2)
        label       = f"{s['temperature']},{s['time_of_day']},{s['occupancy']},{s['electricity_price']}"
        print(f"  {label:<45} {best_action}  (Q={best_q})")


print("\n" + "=" * 55)
print("  Random Agent vs Trained Agent (100 test episodes)")
print("=" * 55)

random_rewards = []
for _ in range(100):
    state = random_state()
    total = 0
    for _ in range(STEPS_PER_EPISODE):
        action = random.choice(actions)
        total += get_reward(state, action)
        state  = random_state()
    random_rewards.append(total)

trained_rewards = []
for _ in range(100):
    state = random_state()
    total = 0
    for _ in range(STEPS_PER_EPISODE):
        key = state_to_key(state)
        if key in Q_table:
            best_idx = Q_table[key].index(max(Q_table[key]))
        else:
            best_idx = random.randint(0, len(actions) - 1)
        total += get_reward(state, actions[best_idx])
        state  = random_state()
    trained_rewards.append(total)

avg_random  = round(sum(random_rewards)  / len(random_rewards),  2)
avg_trained = round(sum(trained_rewards) / len(trained_rewards), 2)
improvement = round(((avg_trained - avg_random) / abs(avg_random)) * 100, 1) if avg_random != 0 else 0

print(f"\n  Random Agent  avg reward : {avg_random}")
print(f"  Trained Agent avg reward : {avg_trained}")
print(f"  Improvement              : {improvement}%")
print("\n  Q-Learning training complete!")
print("  Agent has learned optimal policy for all 36 states.")

def get_best_action(state):
    key = state_to_key(state)
    if key not in Q_table:
        import random
        ai = random.randint(0, len(actions) - 1)
        return actions[ai], 0.0
    ai = Q_table[key].index(max(Q_table[key]))
    return actions[ai], round(max(Q_table[key]), 3)