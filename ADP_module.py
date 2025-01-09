import numpy as np

def initialize_parameters():
    # Initialize default parameters for the algorithm and store them in a dictionary
    params = {
        'hours': 24,
        'battery_capacity': 200,
        'max_char': 100,
        'max_dis': -100,
        'efficiency': 0.95,
        'initial_soc': 40,
        'soc_step': 10,
        'base_price': 0.6
    }

    # Set up price structure 
    prices = np.array([params['base_price'] for hour in range(params['hours'] + 1)])
    for hour in range(params['hours'] + 1):
        if 18 < hour <= 20:
            prices[hour] = 1.473
        elif (8 < hour <= 11) or (17 < hour <= 18) or (20 < hour <= 22):
            prices[hour] = 1.228
        elif (11 < hour <= 17) or (22 < hour <= 24):
            prices[hour] = 0.734
        elif 0 <= hour <= 8:
            prices[hour] = 0.332

    params['prices'] = prices
    return params

def initialize_memo(hours, max_soc, soc_step):
    # Initialize the memo array for DP.
    soc_levels = int(max_soc/soc_step) + 1
    memo = np.full(((hours + 1) * soc_levels * 2,), float('inf'))  # Initialize with an impossible cost
    memo[1::2] = -10  # Set every second element to -10
    memo = memo.reshape((hours + 1, soc_levels, 2))
    return memo

def dp(time, soc, memo, params):
    battery_capacity = params['battery_capacity']
    efficiency = params['efficiency']
    prices = params['prices']
    soc_step = params['soc_step']
    hours = params['hours']
    max_char = params['max_char']
    max_dis = params['max_dis']
    initial_soc = params['initial_soc']
    if time < 0 or time > hours:
        return float('inf')
    if soc < 0 or soc > battery_capacity:
        return float('inf')
    if time == 0:
        if soc == initial_soc:
            memo[0][int(soc / soc_step)][0] = 0 # initial cost 0
            memo[0][int(soc / soc_step)][1] = -20 # unique num for memo[0]
            return 0
        else: 
            return float('inf')
    if memo[time, int(soc / soc_step), 1] != -10:
        return memo[time, int(soc / soc_step), 0]
    soc_actions = int((max_char - max_dis)/soc_step + 1)
    minimal_cost = float('inf')  # if this stays after checking all prevs, then point unreachable
    for i in range(soc_actions):
        cur_dis = max_dis + i * soc_step  # discharge action
        cost_change = 0
        prev_soc = soc - cur_dis
        if dp(time - 1, prev_soc, memo, params) == float('inf'):
            continue
        cost_change = cur_dis * prices[time]
        if cost_change < 0:
            cost_change *= efficiency
        else:
            cost_change /= efficiency
        cost_final = cost_change + dp(time - 1, prev_soc, memo, params)
        if cost_final < minimal_cost:
            minimal_cost = cost_final
            memo[time, int(soc / soc_step), 1] = prev_soc
        continue
    if minimal_cost == float('inf'):
        memo[time, int(soc / soc_step), 1] = -10
    memo[time, int(soc / soc_step), 0] = minimal_cost
    return memo[time, int(soc / soc_step), 0]

def trace_path(memo, initial_soc, soc_step, hours):
    path = []
    current_time = hours
    current_soc = initial_soc # initial soc = final soc, start tracing from final
    path.append(current_soc)
    while current_time > 0:
        current_soc = memo[current_time, int(current_soc / soc_step), 1]
        path.append(current_soc)
        current_time -= 1
    path.reverse()
    return path
