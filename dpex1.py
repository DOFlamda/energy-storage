import numpy as np
import matplotlib.pyplot as plt
# Parameters loads not considered yet, load adds restrictions
hours = 24 # hour precision parallel to prices 
battery_capacity = 200  # kWh assume one Battery 
max_charge_power = 100  # actual power 107.5
max_discharge_power = 100
charge_efficiency = 0.95 # actual >94%
discharge_efficiency = 0.95
initial_soc = 40  # 20% SOC
soc_step = 10  # SOC granularity in kWh
# SOC 21 levels total (0, 10, ... 200)
# Electricity prices (peak/off-peak)
base_price = 0.6 #山东省一月电价，基础取平均包含补贴政策等，上下浮系数固定
prices = np.array([base_price for hour in range(hours + 1)])
for i in range(len(prices)):
    if i < 10:
        prices[i] *= 1
    elif i < 12:
        prices[i] *= 0.3
    elif i < 14:
        prices[i] *= 0.1
    elif i < 16:
        prices[i] *= 0.3
    elif i < 19:
        prices[i] *= 2
    elif i < 22:
        prices[i] *= 1.7
    else:
        prices[i] *= 1
# print(len(prices))
# Predicted load array (factory load prediction for each hour)
predicted_load = np.array([137, 240, 130, 178, 150, 137, 128, 84, 112, 35, 0, 0, 
                           0, 22, 0, 19, 99, 160, 72, 108, 129, 129, 120, 141])
# create memo for temp storage and path record
memo = np.full((25 * 21 * 2,), 500)  # Initialize all with impossible 500
memo[1::2] = -10  # Set every second element to -10

memo = memo.reshape((25, 21, 2))
# print(memo.shape)
# create dp function
# initialize time(0) and time(1), 40 = [4] SOC
memo[0][4][0] = 0 # initial cost is 0 yuan
memo[0][4][1] = initial_soc # this path is not used, actual previous day's time(23) soc
for i in range(21):
    max_dis = -100
    cur_dis = max_dis + i * soc_step # discharge action
    cost_change = 0
    after_soc = initial_soc + cur_dis
    if after_soc < 0 or after_soc > 200: # invalid soc
        continue
    after_index = int(after_soc/10)
    cost_change = prices[1] * cur_dis
    memo[1][after_index][0] = cost_change
    memo[1][after_index][1] = initial_soc # indicate path from time(0) 

# initial time(1) memo prepared, start dp
# dp(time, soc) returns a int indicating cost at given time and soc level
# returns 500 in default for non-existing values 
def dp(time, soc) -> int:
    if time < 0 or time > 24:
        return 500
    if soc < 0 or soc > battery_capacity:
        return 500
    if memo[int(time)][int(soc/10)][1] != -10:
        return memo[int(time)][int(soc/10)][0]
        # already exists in memo
    # find last actions
    minimal_cost = 500 # used for finding minimal cost, initial 500
    for i in range(21):
        max_dis = -100
        cur_dis = max_dis + i * soc_step # discharge action
        cost_change = 0
        prev_soc = soc - cur_dis
        if dp(time - 1, prev_soc) == 500: # imposible prev soc
            continue
        cost_change = cur_dis * prices[time]
        cost_final = cost_change + dp(time - 1, prev_soc)
        # previous minimal + cost change
        if cost_final < minimal_cost:
            minimal_cost = cost_final
            memo[int(time), int(soc/10), 1] = prev_soc
            # found new minimal, update path
        continue
    if minimal_cost == 500:
        memo[int(time), int(soc/10), 1] = -10
        # impossible state, ensure memo records as invalid
    memo[int(time), int(soc/10), 0] = minimal_cost
    # update checked result
    return memo[int(time), int(soc/10), 0]

print(dp(24, 40))
paths = []
paths.append(40)
current_time = 24
last_state = 40
while current_time > 0:
    last_state = memo[int(current_time)][int(last_state/10)][1] 
    paths.append(int(last_state))
    current_time -= 1
paths.reverse()
print(paths)

# Define x-axis (0 to 24 hours)
x = list(range(25))  # 25 points for 0 to 24
# Define y-axis (your list of integers)
y = paths
# Check if the length of x and y match
if len(x) != len(y):
    raise ValueError("x and y must have the same length")
# Create the plot
plt.figure(figsize=(10, 5))  # Set figure size
plt.plot(x, y, marker='o', linestyle='-', color='b', label='Data')  # Plot line with markers

# Add labels and title
plt.xlabel('Time')
plt.ylabel('SOC')
plt.title('Graph of SOC Over 24 Hours')

# Add grid and legend
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# Show the plot
plt.show()



