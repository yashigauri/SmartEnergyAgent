
import random

temperature_options   = ["cold", "comfortable", "hot"]
time_options          = ["morning", "afternoon", "night"]
occupancy_options     = ["occupied", "empty"]
price_options         = ["cheap", "expensive"]


actions = [
    "AC_ON  | GEYSER_ON  | LIGHTS_ON",
    "AC_ON  | GEYSER_ON  | LIGHTS_OFF",
    "AC_ON  | GEYSER_OFF | LIGHTS_ON",
    "AC_ON  | GEYSER_OFF | LIGHTS_OFF",
    "AC_OFF | GEYSER_ON  | LIGHTS_ON",
    "AC_OFF | GEYSER_ON  | LIGHTS_OFF",
    "AC_OFF | GEYSER_OFF | LIGHTS_ON",
    "AC_OFF | GEYSER_OFF | LIGHTS_OFF",
]


def get_reward(state, action):

    reward = 0

    ac_on     = "AC_ON"     in action
    geyser_on = "GEYSER_ON" in action
    lights_on = "LIGHTS_ON" in action

    if not ac_on and not geyser_on and not lights_on:
        reward += 3

    if lights_on and state["occupancy"] == "occupied":
        reward += 1

    if state["electricity_price"] == "expensive":
        if ac_on or geyser_on:
            reward -= 3

    if ac_on and state["occupancy"] == "empty":
        reward -= 5

    if not ac_on and state["temperature"] == "hot" and state["occupancy"] == "occupied":
        reward -= 6

    return reward


print("=" * 55)
print("  Smart Home Environment — SUBGROUP 3F22")
print("=" * 55)

for step in range(1, 6):

    state = {
        "temperature"       : random.choice(temperature_options),
        "time_of_day"       : random.choice(time_options),
        "occupancy"         : random.choice(occupancy_options),
        "electricity_price" : random.choice(price_options)
    }

    action = random.choice(actions)

    reward = get_reward(state, action)

    print(f"\nStep {step}:")
    print(f"  Temperature : {state['temperature']}")
    print(f"  Time        : {state['time_of_day']}")
    print(f"  Occupancy   : {state['occupancy']}")
    print(f"  Elec. Price : {state['electricity_price']}")
    print(f"  Action      : {action}")
    print(f"  Reward      : {reward}")
    print("-" * 55)

print("\nSummary:")
print(f"  Total States  : {len(temperature_options) * len(time_options) * len(occupancy_options) * len(price_options)}")
print(f"  Total Actions : {len(actions)}")
print("\nEnvironment working correctly!")
print("Next step: Train Q-Learning agent over this environment.")