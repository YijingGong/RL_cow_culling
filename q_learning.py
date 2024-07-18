import numpy as np
import random
import matplotlib.pyplot as plt
import pickle
import os
import time
import utility
import cow_environment

parity_range = range(13)
mim_range = range(21)
mip_range = range(10)
disease_range = range(2)

def q_learning(env, q_table, rewards_per_episode, num_episodes, max_steps, alpha=0.1, gamma=0.99, epsilon=1.0, epsilon_decay=0.999, min_epsilon=0.3):
    for episode in range(num_episodes):
        state = env.reset()  # Start a new episode
        total_reward = 0
        steps = 0

        while steps < max_steps:
            if random.uniform(0, 1) < epsilon:
                action = random.choice(env.actions)  # Explore
                # print("current state", state, 'Explore', action)
            else:
                action = max(q_table[state], key=q_table[state].get)  # Exploit
                # print("current state", state, 'Exploit', action)
                
            next_state, reward = env.step(action)
            total_reward += reward

            if not (next_state[0] in parity_range and next_state[1] in mim_range and next_state[2] in mip_range):
                break

            best_next_action = max(q_table[next_state], key=q_table[next_state].get)
            td_target = reward + gamma * q_table[next_state][best_next_action]
            td_error = td_target - q_table[state][action]
            # print("best_next_action:", best_next_action, "td_target:", td_target, "td_error:", td_error)
            q_table[state][action] += alpha * td_error

            state = next_state
            steps += 1

        epsilon = max(min_epsilon, epsilon * epsilon_decay)
        rewards_per_episode.append(total_reward)
        print(f"Episode {episode + 1}/{num_episodes}, Total Reward: {total_reward}")

    return q_table, rewards_per_episode, epsilon

def save_q_table(q_table, rewards_per_episode, epsilon, filename):
    with open(filename, 'wb') as f:
        pickle.dump((q_table, rewards_per_episode, epsilon), f)

def load_or_create_q_table(filename, env):
    if os.path.exists(filename):
        print("loaded the q table")
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        print("created a new q table")
        q_table = {}
        rewards_per_episode = []
        epsilon = 1
        for parity in parity_range:
            for mim in mim_range:
                for mip in mip_range:
                    for disease in disease_range:
                        state = (parity, mim, mip, disease)
                        if utility.possible_state(state, parity_range, mim_range, mip_range, disease_range):
                            q_table[state] = {action: 0 for action in env.actions}
        return q_table, rewards_per_episode, epsilon


# Initialize the environment with individual features and train the agent
env = cow_environment.CowEnv(parity_range, mim_range, mip_range, disease_range)
# Load existing Q-table or create a new one
q_table_filename = 'q_table.pkl'
q_table, rewards_per_episode, epsilon = load_or_create_q_table(q_table_filename, env)
# print("q_table:", len(q_table))
# print("rewards_per_episode:", len(rewards_per_episode))
# print(q_table, rewards_per_episode, epsilon)

start_time = time.time()
q_table, rewards_per_episode, epsilon = q_learning(env, q_table = q_table,rewards_per_episode = rewards_per_episode, epsilon = epsilon, num_episodes=1000000, max_steps = 60)  # Increase number of episodes for better learning
end_time = time.time()

# Save the learned Q-table
save_q_table(q_table, rewards_per_episode, epsilon, q_table_filename)


# Print the learned Q-table
print("Learned Q-table:")
for state, actions in q_table.items():
    print(f"State: {state}")
    for action, value in actions.items():
        print(f"  Action: {action}, Q-value: {value}")
# print(q_table)
print(len(q_table))

def plot_rewards(rewards, window=100):
    moving_avg = np.convolve(rewards, np.ones(window)/window, mode='valid')
    plt.figure(figsize=(10, 5))
    plt.plot(rewards, label='Total Reward per Episode')
    plt.plot(moving_avg, label=f'Moving Average (window={window})')
    plt.xlabel('Episode')
    plt.ylabel('Total Reward')
    plt.title('Total Reward per Episode and Moving Average')
    plt.legend()
    # plt.show()
    plt.savefig('figure.png')
    plt.close()

plot_rewards(rewards_per_episode)
print(f"Time taken for training: {end_time - start_time} seconds")