# Eco
SLAUGHTER_PRICE =1.49 # per kg, according to Manfei repro paper: https://www.sciencedirect.com/science/article/pii/S0022030223001145#bib66
# avg of $260/cwt for dressed cow * 55% = $143/cwt = 3.15/kg
MANUTURE_BODY_WEIGHT = 740.1 #kg, according to Manfei repro paper
REPLACEMENT_COST = 2000 # hard-coded according to the figure on prelim proposal
CALF_PRICE = 50 # hard-coded according to https://www.sciencedirect.com/science/article/pii/S2666910221001733

# milking
WOODS_PARAMETERS = [[15.72, 22.06, 21.92], [0.2433, 0.235, 0.2627], [0.002445, 0.003642, 0.004041]] # [a], [b], and [c], each list have 3 values for 3 parity, based on Manfei 2022 paper. Mean + parity adjustment
MILK_PRICE = 21.11 #milk price of $21.11 per cwt according to chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://www.ams.usda.gov/mnreports/dywweeklyreport.pdf

#breeding
BREED_COST_PER_MONTH = 11.2 # hard-coded https://www.sciencedirect.com/science/article/pii/S0022030223001145#bib20 : $120 for ED per year, 104 for TAI per year, avg to 11.2 per month
PREG_RATE = {1: 0.4, 2: 0.4, 3: 0.3, 4: 0.3, 5: 0.25, 6: 0.25, 7: 0.2, 8: 0.2, 9: 0.15, 10: 0.15, 11: 0.1, 12: 0.1}
PREG_RATE_DROP = 0.025
SICK_PREG_RATE_MULTIPLIER = 0.8

# dealth
DEATH_RATE = [0, 2.05, 2.66, 3.72, 4.38, 4.83, 5.78, 5.92, 6.40, 6.40, 6.40, 6.40, 6.40] #unit: %; https://www.sciencedirect.com/science/article/pii/S0022030208710865#fig1 table 2

#disease
DISEASE_RISK = [0, 0.15, 0.18, 0.2, 0.2, 0.23, 0.25, 0.28, 0.3, 0.3, 0.32, 0.35, 0.35] # from health to sick per parity
TREATMENT_COST_PER_MONTH = 100 # hard-coded guess from https://www.sciencedirect.com/science/article/pii/S0022030216308992#tbl8
RECOVER_RATE = 0.6 # after treatment, 60% can recover
SICK_DEATH_RATE_MULTIPLIER = 2 #sick, twice of the normal dealth rate
SICK_MILK_PRODUCTION_MULTIPLIER = 0.7 #sick, 0% of the normal dealth rate
SICK_SLAUGHTER_PRICE_MULTIPLIER = 0.9 # 90% of healthy cow