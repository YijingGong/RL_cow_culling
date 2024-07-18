import pickle
import os
import time
import cow_environment

parity_range = range(13)
mim_range = range(21)
mip_range = range(10)
disease_range = range(2)

def peek_policy(filename):
    if os.path.exists(filename):
        print("loaded the q table")
        with open(filename, 'rb') as f:
            q_table, _, _ = pickle.load(f)
            # print("Q-table:", q_table)
            print("Q-table:")
            for state, actions in list(q_table.items()): #[:5]  # Print only the first 5 entries for brevity
                print(f"State: {state}")
                for action, value in actions.items():
                    print(f"  Action: {action}, Q-value: {value}")
        
def load_q_table(filename):
    if os.path.exists(filename):
        print("loaded the q table")
        with open(filename, 'rb') as f:
            return pickle.load(f)

def test_policy(policy_q_table, rep_num):
    max_steps = 60
    for i in range(rep_num):
        test_env = cow_environment.CowEnv(parity_range, mim_range, mip_range, disease_range) 
        total_reward = 0
        steps = 0

        while steps < max_steps:
            test_env.render()
            state = test_env.state
            action = max(policy_q_table[state], key=policy_q_table[state].get)
            print(action)
            next_state, reward = test_env.step(action)
            total_reward += reward
            test_env.state = next_state
            steps += 1
        print(f"Test rep: {i}, Total Reward in Test: {total_reward}")

# peek policy
peek_policy('q_table.pkl')

# q_table_filename = 'q_table.pkl'
# q_table, rewards_per_episode, epsilon = load_q_table(q_table_filename)
# print("q_table len:", len(q_table))
# print("rewards_per_episode len:", len(rewards_per_episode))
# print("epsilon len:", epsilon)

# test_start_time = time.time()
# test_policy(q_table, 10)
# test_end_time = time.time()
# print(f"Time taken for testing: {test_end_time - test_start_time} seconds")