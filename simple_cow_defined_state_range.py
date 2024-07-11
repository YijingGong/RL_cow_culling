import numpy as np
from scipy.integrate import quad
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import pickle
import os

milk_price = 21.11 #milk price of $21.11 per cwt according to chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://www.ams.usda.gov/mnreports/dywweeklyreport.pdf
breed_cost_per_day = 4 # hard-coded according to chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://afs.ca.uky.edu/files/how_much_are_you_losing_from_extra_days_open.pdf, $3 to $5 per day, I chose $4 per day, a month would be 120
treatment_cost_per_day = 2 # hard-coded guess from https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10339984/#:~:text=The%20health%20treatment%20cost%20of,and%20usually%20increased%20with%20parity. 
recover_rate = 0.6 # after treatment, 60% can recover
slaughter_price =187 # according to chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://www.ams.usda.gov/mnreports/lsmdairycomp.pdf, $187 per cwt 
manuture_bw = 1500 #lbs, google holstein manure BW
replacement_cost = 2500 # hard-coded according to the figure on prelim proposal
woods_parameters = [[16.13, 23.61, 23.81], [0.235, 0.227, 0.244], [0.0019, 0.0032, 0.0036]] # [a], [b], and [c], each list have 3 values for 3 parity
death_rate = [0, 2.05, 2.66, 3.72, 4.38, 4.83, 5.78, 5.92, 6.40, 6.40, 6.40, 6.40, 6.40] #https://www.sciencedirect.com/science/article/pii/S0022030208710865#fig1 table 2
disease_risk = [0, 0.1, 0.12, 0.15, 0.15, 0.2, 0.2, 0.25, 0.25, 0.25, 0.3, 0.3, 0.35] # from health to sick per parity
preg_rate = {1: 0.4, 2: 0.4, 3: 0.3, 4: 0.3, 5: 0.25, 6: 0.25, 7: 0.2, 8: 0.2, 9: 0.15, 10: 0.15, 11: 0.1, 12: 0.1}
parity_range = range(13)
mim_range = range(21)
mip_range = range(10)
disease_range = range(2)

def possible_state(state):
    if not (state[0] in parity_range and state[1] in mim_range and state[2] in mip_range and state[3] in disease_range):
        return False
    if state[0] == 0: # only springer valid if parity == 0
        if state[1] != 0 or state[2] != 9 or state[3] != 0:
            return False
    else: #parity>=1
        if state[1] == 0 and state[2] == 0:
            return False
        if state[2] == 8 or state[2] == 9: # last two month, must be dry
            if state[1] != 0:
                return False
        else: # if not dry:
            if state[2] != 0: # preg
                if state[1] < state[2]+3: # not possible mim < mip+3 because start breeding during third month
                    return False
    return True

class CowEnv:
    def __init__(self):
        # only consider parity, MIM, MIP, disease
        self.state = (0, 0, 9, 0)
        self.parameter_a = self.parameter_b = self.parameter_c = None
        self.actions = ['Keep', 'Cull']

    def reset(self):
        self.state = (random.choice(range(1, 13)), random.choice(mim_range), random.choice(mip_range), random.choice(disease_range)) 
        while possible_state(self.state) == False:
            self.state = (random.choice(range(1, 13)), random.choice(mim_range), random.choice(mip_range), random.choice(disease_range)) 
        return self.state

    def step(self, action):
        slaughter_income = 0
        replacement_cost = 0
        milk_income = 0
        calf_income = 0
        breed_cost = 0
        treatment_cost = 0
        parity, mim, mip, disease = self.state

        if action == 'Cull':
            slaughter_income = self.slaughter(parity, disease) 
            self.state = (0, 0, 9, 0) # replaced by a new springer
            reward = slaughter_income - replacement_cost
        
        else: 
            next_parity = parity # by default, parity does not change, unless mip == 9
            next_mim = 0
            next_mip = 0
            next_mip = 0
            next_disease = 0

            # death
            if self.death(parity, disease): # died
                slaughter_income = 0 # it's 0 because it is a died cow
                self.state = (0, 0, 9, 0) # replaced by a new springer
                reward = slaughter_income - replacement_cost
            else:
                # milking
                if mim != 0: 
                    dim = (mim-1)*30 + 1 
                    self.parameter_a, self.parameter_b, self.parameter_c = self.assign_woods_parameters(parity)
                    milk_production = self.calc_integral_wood_curve(dim, dim+30, self.parameter_a, self.parameter_b, self.parameter_c)
                    milk_income = milk_production*2.2/100 * milk_price
                    # print(parity, mim, milk_production_avg_day, milk_income)
                    next_mim = mim + 1

                # pregnancy status
                if mip == 7 or mip == 8: # dry
                    next_mim = 0
                if mip == 9: # calving
                    calf_income = 1000 # hard-coded according to personal guess
                    next_parity = parity+1
                    next_mim = 1
                    next_mip = 0
                elif mip == 0: # breeding
                    if mim>=3:
                        breed_cost = breed_cost_per_day * 30 
                        if self.breed(parity, disease) == True:
                            next_mip = 1
                        else: 
                            next_mip = 0
                else: # keep pregnancy
                    next_mip = mip + 1

                # Disease affect slauter income (in slaughter() function), milk income, breed success (in breed() function), and treatment_cost 
                if disease == 1: # when the cow is sick
                    milk_income *= 0.9
                    treatment_cost = treatment_cost_per_day * 30
                    if random.uniform(0, 1) < recover_rate:
                        next_disease = 0 # recovered from disease
                    else:
                        next_disease = 1 # remain sick
                else:
                    if random.uniform(0, 1) < disease_risk[parity]:
                        next_disease = 1 # become sick
                    else:
                        next_disease = 0 #remain healthy
                    

                self.state = (next_parity, next_mim, next_mip, next_disease)
                reward = milk_income + calf_income - breed_cost - treatment_cost

        # print(slaughter_income, replacement_cost, milk_income, calf_income, breed_cost)

        return self.state, reward
            

    def render(self):
        print(f"Current state: {self.state}")

    def assign_woods_parameters(self, parity):
        if parity <= 3:
            self.parameter_a = woods_parameters[0][parity-1]
            self.parameter_b = woods_parameters[1][parity-1]
            self.parameter_c = woods_parameters[2][parity-1]
        else: 
            self.parameter_a = woods_parameters[0][-1]
            self.parameter_b = woods_parameters[1][-1]
            self.parameter_c = woods_parameters[2][-1]
        return self.parameter_a, self.parameter_b, self.parameter_c
    
    def get_y_values_wood_curve(self, t, parameter_a, parameter_b, parameter_c):
        return parameter_a * np.power(t, parameter_b) * np.exp(-1 * parameter_c * t)

    def calc_integral_wood_curve(self, t1, t2, parameter_a, parameter_b, parameter_c):
        result, _ = quad(self.get_y_values_wood_curve, t1, t2, args=(parameter_a, parameter_b, parameter_c))
        return result
    
    def breed(self, parity, disease):
        random_num = random.uniform(0, 1)
        if disease == 0:
            return True if random_num < preg_rate[parity] else False
        else: # if sick, preg rate is 80% of normal rate
            return True if random_num < 0.8 * preg_rate[parity] else False 
    
    def slaughter(self, parity, disease): 
        if parity == 0 or 1:
            bw = 0.82 * manuture_bw
        elif parity == 2:
            bw = 0.92 * manuture_bw
        else:
            bw = manuture_bw
        return bw/100 * slaughter_price if disease == 0 else bw/100 * slaughter_price * 0.7 #hard-code: discounted to 70% for sick cows

    def death(self, parity, disease):
        random_num = random.uniform(0, 1)
        if disease == 0: #healthy
            if random_num < death_rate[parity]:
                return True
            else:
                return False
        else: #sick, twice of the normal dealth rate
            if random_num < 2*death_rate[parity]:
                return True
            else:
                return False

def q_learning(env, q_table, rewards_per_episode, num_episodes, max_steps, alpha=0.1, gamma=0.99, epsilon=1.0, epsilon_decay=0.999, min_epsilon=0.3):
    # rewards_per_episode = []  # To store the total rewards per episode
    
    for episode in range(num_episodes):
        state = env.reset()  # Start a new episode
        total_reward = 0
        steps = 0

        while steps < max_steps:
            if random.uniform(0, 1) < epsilon:
                action = random.choice(env.actions)  # Explore
            else:
                action = max(q_table[state], key=q_table[state].get)  # Exploit
                
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
                        if possible_state(state):
                            q_table[state] = {action: 0 for action in env.actions}
        return q_table, rewards_per_episode, epsilon


# Initialize the environment with individual features and train the agent
env = CowEnv()
# Load existing Q-table or create a new one
q_table_filename = 'q_table.pkl'
q_table, rewards_per_episode, epsilon = load_or_create_q_table(q_table_filename, env)
print("q_table:", len(q_table))
print("rewards_per_episode:", len(rewards_per_episode))
print(q_table, rewards_per_episode, epsilon)

q_table, rewards_per_episode, epsilon = q_learning(env, q_table = q_table,rewards_per_episode = rewards_per_episode, epsilon = epsilon, num_episodes=10000, max_steps = 60)  # Increase number of episodes for better learning

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
    plt.show()

plot_rewards(rewards_per_episode)

# # Test the learned policy
# state = env.reset()  # Start a new episode for testing
# total_reward = 0
# steps = 0
# max_steps = 60

# while steps < max_steps:
#     action = max(q_table[state], key=q_table[state].get)
#     next_state, reward = env.step(action)
#     total_reward += reward
#     state = next_state
#     env.render()
#     steps += 1

# print(f"Total Reward in Test: {total_reward}")
