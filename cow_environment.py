import numpy as np
from scipy.integrate import quad
import random
import utility
import animal_constants

# slaughter_price =1.49 # per kg, according to Manfei repro paper: https://www.sciencedirect.com/science/article/pii/S0022030223001145#bib66
# # avg of $260/cwt for dressed cow * 55% = $143/cwt = 3.15/kg
# manuture_bw = 740.1 #kg, according to Manfei repro paper
# replacement_cost = 2000 # hard-coded according to the figure on prelim proposal
# calf_price = 50 # hard-coded according to https://www.sciencedirect.com/science/article/pii/S2666910221001733

# milk_price = 21.11 #milk price of $21.11 per cwt according to chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://www.ams.usda.gov/mnreports/dywweeklyreport.pdf
# breed_cost_per_month = 11.2 # hard-coded https://www.sciencedirect.com/science/article/pii/S0022030223001145#bib20 : $120 for ED per year, 104 for TAI per year, avg to 11.2 per month

# treatment_cost_per_day = 1 # hard-coded guess from https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10339984/#:~:text=The%20health%20treatment%20cost%20of,and%20usually%20increased%20with%20parity. 
# recover_rate = 0.6 # after treatment, 60% can recover

# woods_parameters = [[15.72, 22.06, 21.92], [0.2433, 0.235, 0.2627], [0.002445, 0.003642, 0.004041]] # [a], [b], and [c], each list have 3 values for 3 parity, based on Manfei 2022 paper. Mean + parity adjustment
# death_rate = [0, 2.05, 2.66, 3.72, 4.38, 4.83, 5.78, 5.92, 6.40, 6.40, 6.40, 6.40, 6.40] #unit: %; https://www.sciencedirect.com/science/article/pii/S0022030208710865#fig1 table 2
# disease_risk = [0, 0.1, 0.12, 0.15, 0.15, 0.2, 0.2, 0.25, 0.25, 0.25, 0.3, 0.3, 0.35] # from health to sick per parity
# preg_rate = {1: 0.4, 2: 0.4, 3: 0.3, 4: 0.3, 5: 0.25, 6: 0.25, 7: 0.2, 8: 0.2, 9: 0.15, 10: 0.15, 11: 0.1, 12: 0.1}


class CowEnv:
    def __init__(self, parity_range, mim_range, mip_range, disease_range):
        # only consider parity, MIM, MIP, disease
        self.state = (0, 0, 9, 0)
        self.parameter_a = self.parameter_b = self.parameter_c = None
        self.actions = ['Keep', 'Cull']
        self.parity_range = parity_range
        self.mim_range = mim_range
        self.mip_range = mip_range
        self.disease_range = disease_range

    def reset(self):
        self.state = (random.choice(self.parity_range), random.choice(self.mim_range), random.choice(self.mip_range), random.choice(self.disease_range)) 
        while utility.possible_state(self.state, self.parity_range, self.mim_range, self.mip_range, self.disease_range) == False:
            self.state = (random.choice(self.parity_range), random.choice(self.mim_range), random.choice(self.mip_range), random.choice(self.disease_range)) 
        return self.state

    def step(self, action):
        slaughter_income = 0
        calf_income = 0
        milk_income = 0
        breed_cost = 0
        treatment_cost = 0
        parity, mim, mip, disease = self.state

        if action == 'Cull':
            slaughter_income = self.slaughter(parity, disease) 
            self.state = (0, 0, 9, 0) # replaced by a new springer
            reward = slaughter_income - animal_constants.REPLACEMENT_COST 
            # print(">cull", parity, mim, mip, disease)
            # print(slaughter_income, replacement_cost)
        
        else: 
            next_parity = parity # by default, parity does not change, unless mip == 9
            next_mim = 0
            next_mip = 0
            next_mip = 0
            next_disease = 0

            # death
            if self.death(parity, disease): # died
                # print(">keep died")
                slaughter_income = 0 # it's 0 because it is a died cow
                self.state = (0, 0, 9, 0) # replaced by a new springer
                reward = slaughter_income - animal_constants.REPLACEMENT_COST 
                # print("slaughter_income:", slaughter_income, "replacement_cost", replacement_cost)
            else:
                # milking
                if mim != 0: 
                    dim = (mim-1)*30 + 1 
                    self.parameter_a, self.parameter_b, self.parameter_c = self.assign_woods_parameters(parity)
                    milk_production = self.calc_integral_wood_curve(dim, dim+30, self.parameter_a, self.parameter_b, self.parameter_c)
                    milk_income = milk_production*2.2/100 * animal_constants.MILK_PRICE  
                    next_mim = mim + 1

                # pregnancy status
                if mip == 7 or mip == 8: # dry
                    next_mim = 0
                if mip == 9: # calving
                    calf_income = animal_constants.CALF_PRICE
                    next_parity = parity+1
                    next_mim = 1
                    next_mip = 0
                elif mip == 0: # breeding
                    if mim>=3:
                        breed_cost = animal_constants.BREED_COST_PER_MONTH  
                        if self.breed(parity, mim, disease) == True:
                            next_mip = 1
                        else: 
                            next_mip = 0
                else: # keep pregnancy
                    next_mip = mip + 1

                # Disease affect slauter income (in slaughter() function), milk income, breed success (in breed() function), and treatment_cost 
                if disease == 1: # when the cow is sick
                    milk_income *= 0.9
                    treatment_cost = animal_constants.TREATMENT_COST_PER_MONTH
                    if random.uniform(0, 1) < animal_constants.RECOVER_RATE:
                        next_disease = 0 # recovered from disease
                    else:
                        next_disease = 1 # remain sick
                else:
                    if random.uniform(0, 1) < animal_constants.DISEASE_RISK[parity]:
                        next_disease = 1 # become sick
                    else:
                        next_disease = 0 #remain healthy

                self.state = (next_parity, next_mim, next_mip, next_disease)
                reward = milk_income + calf_income - breed_cost - treatment_cost
                # print(">keep not died")
                # print("milk income:", milk_income, "calf_income:", calf_income, "breed_cost", breed_cost, "treatment_cost",treatment_cost)
        # print("one reward:", reward)

        # print(slaughter_income, replacement_cost, milk_income, calf_income, breed_cost)

        return self.state, reward
            

    def render(self):
        print(f"Current state: {self.state}")

    def assign_woods_parameters(self, parity):
        if parity <= 3:
            self.parameter_a = animal_constants.WOODS_PARAMETERS[0][parity-1]
            self.parameter_b = animal_constants.WOODS_PARAMETERS[1][parity-1]
            self.parameter_c = animal_constants.WOODS_PARAMETERS[2][parity-1]
        else: 
            self.parameter_a = animal_constants.WOODS_PARAMETERS[0][-1]
            self.parameter_b = animal_constants.WOODS_PARAMETERS[1][-1]
            self.parameter_c = animal_constants.WOODS_PARAMETERS[2][-1]
        return self.parameter_a, self.parameter_b, self.parameter_c
    
    def get_y_values_wood_curve(self, t, parameter_a, parameter_b, parameter_c):
        return parameter_a * np.power(t, parameter_b) * np.exp(-1 * parameter_c * t)

    def calc_integral_wood_curve(self, t1, t2, parameter_a, parameter_b, parameter_c):
        result, _ = quad(self.get_y_values_wood_curve, t1, t2, args=(parameter_a, parameter_b, parameter_c))
        return result
    
    def breed(self, parity, mim, disease):
        random_num = random.uniform(0, 1)
        health_success_rate = max(0, animal_constants.PREG_RATE[parity] - (mim-3)*0.025)
        sick_success_rate = health_success_rate*0.8 # hard-code, if sick, preg rate is 80% of normal rate
        if disease == 0:
            return True if random_num < health_success_rate else False
        else: 
            return True if random_num < sick_success_rate else False 
    
    def slaughter(self, parity, disease): 
        if parity == 0 or parity == 1:
            bw = 0.82 * animal_constants.MANUTURE_BODY_WEIGHT
        elif parity == 2:
            bw = 0.92 * animal_constants.MANUTURE_BODY_WEIGHT
        else:
            bw = animal_constants.MANUTURE_BODY_WEIGHT
        return bw * animal_constants.SLAUGHTER_PRICE if disease == 0 else bw * animal_constants.SLAUGHTER_PRICE * 0.7 #hard-code: discounted to 70% for sick cows

    def death(self, parity, disease):
        random_num = random.uniform(0, 1)
        if disease == 0: #healthy
            if random_num < animal_constants.DEATH_RATE[parity]/100:
                return True
            else:
                return False
        else: 
            if random_num < animal_constants.SICK_DEATH_RATE_MULTIPLIER*animal_constants.DEATH_RATE[parity]/100:
                return True
            else:
                return False
