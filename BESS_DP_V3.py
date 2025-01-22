import numpy as np
# 新增限制条件
# Power(BESS) + Power(Devices) <= power_limit 禁止超额用电 3
# Power(BESS) + Power(Devices) >= 0 禁止逆流 4
# 名义充电效率：100% 名义放电效率：充电效率*放电效率
# 放电时等效收益 = 放电功率*效率*时间*电价 = 放电量*效率*电价 = 充电量*效率a*效率b*电价
# = （充电量*100%） * （电价*效率积）
# 需要满足：名义放电*放电功率 + 峰值负荷/时间 <= power_limit （通常容易满足）
# 充电时不影响，故等效为：放电量损失% = 放电收益损失%
# 该近似的精度误差 <= 0.0036 = 2 * 0.06 - (1 - 0.94^2)
# 限制条件需要的数据：一定误差范围的（负荷+光伏）预测数据，上误差和下误差区别考虑
# power_limit数据（可能和时段有关），光伏和负荷的分别边界范围（boundaries）
# DP 穷举所有的策略组合（path），剔除违规的策略点

# 初始化参数：时间节点，电池参数，效率（名义效率），soc步长
# 备忘录：shape = (t0, soc0, t1, soc1, 2)
# 使用iterative_dp, 填充起始时间t0, 结束时间t1, 起始soc的表
# 填充后可以随意获取memo[t0,t1,ini_index,fin_index,:]的数据
# 0 号位置对应最大收益， 1 号位置对应路径
def initialize_parameters(hours, power_limit, cap, max_char, max_dis, eff,soc_step):
    # Initialize default parameters for the algorithm and store them in a dictionary
    params = {
        'hours': hours,
        'power_lim': power_limit,
        'battery_capacity': cap,
        'max_char': max_char,
        'max_dis': max_dis,
        'efficiency': eff,
        'soc_step': soc_step     # 放电时，加入效率带来的损耗
    }

    # Set up price structure 
    prices = np.array([0.6 for hour in range(params['hours'] + 1)])
    for hour in range(params['hours'] + 1):
        real_hour = hour / 3     # 20 min interval
        if 18 < real_hour <= 20:
            prices[hour] = 1.473
        elif (8 < real_hour <= 11) or (17 < real_hour <= 18) or (20 < real_hour <= 22):
            prices[hour] = 1.228
        elif (11 < real_hour <= 17) or (22 < real_hour <= 24):
            prices[hour] = 0.734
        elif 0 <= real_hour <= 8:
            prices[hour] = 0.332
    params['prices'] = prices
    load_data = np.genfromtxt('loads_temp.csv', dtype=np.float16)
    # Keep only the first row of every second row
    back_loads = load_data[::2]
    loads = back_loads[::-1]
    # print(loads)
    # import loads from other files
    # uses data in 2024.12.22 
    params['loads'] = loads
    soc_actions = int((max_char - max_dis)/(3 * soc_step)) + 1   # 41
    params['actions'] = soc_actions
    return params

def initialize_memo(hours, max_soc, soc_step):
    # Initialize the memo array for DP.
    # 4D * 1D array with only one ini needed
    # estimated usage 126MB with float(32)
    # using float(16) is enough for precision
    soc_levels = int(max_soc/soc_step) + 1
    hour_levels = hours + 1
    shape = (hour_levels, hour_levels, soc_levels, soc_levels, 2)
    memo = np.full(shape, -float('inf'), dtype=np.float16)
    # initialized with all neg_inf
    return memo

# iterative memo writer. Writes layer of memo with fixed t0 and ini_soc
def iterative_dp(t0, ini_soc, t1, memo, params):
    battery_capacity = params['battery_capacity']
    efficiency = params['efficiency']
    prices = params['prices']
    soc_step = params['soc_step']
    hours = params['hours']
    max_char = params['max_char']
    max_dis = params['max_dis']
    loads = params['loads']  # array
    power_lim = params['power_lim']
    actions = params['actions']
    neg_inf = np.float16(-np.inf)  # negative infinity
    ini_index = int(ini_soc / soc_step)
    memo[t0, t0, ini_index, ini_index, 0] = 0  # Initial profit 0
    memo[t0, t0, ini_index, ini_index, 1] = -10  # Special edge value
    # Iterate over the time range (t1) and final SOC (fin_soc)
    for t in range(t0, t1 + 1):  # Iterate over final time t1
        if t == t0:
            continue    # first row already filled
        for fin_soc in range(0, battery_capacity + 1, soc_step):  # Iterate over final SOC  
            max_prof = neg_inf
            edge_soc = 0
            for i in range(actions):
                cur_dis = int(max_dis / 3) + i * soc_step
                if (3 * cur_dis) + loads[t] > power_lim or (3 * cur_dis) + loads[t] < 0:
                    continue
                prev_soc = fin_soc - cur_dis
                if prev_soc < 0 or prev_soc > battery_capacity:
                    continue
                prev_prof = memo[t0, t - 1, ini_index, int(prev_soc / soc_step), 0]
                if prev_prof == neg_inf:
                    continue        # check previous point
                prof = -cur_dis * prices[t]
                if prof > 0:
                    prof *= efficiency
                # Compare with the previous profit and update
                prof_final = prof + prev_prof
                if prof_final > max_prof:
                    max_prof = prof_final
                    edge_soc = prev_soc
            if max_prof != neg_inf:
                memo[t0, t, ini_index, int(fin_soc / soc_step), 0] = max_prof
                memo[t0, t, ini_index, int(fin_soc / soc_step), 1] = edge_soc

def trace_path(memo, t0, t1, s0, s1, step):
    path = []
    while t1 > t0:
        path.append(s1)
        prev_soc = memo[t0, t1, int(s0/step), int(s1/step), 1]  # Retrieve previous SOC
        t1 -= 1  # Move to the previous time step
        s1 = prev_soc  # Update SOC to the previous SOC
    path.append(s0)  # Append the starting SOC
    path.reverse()  # Reverse 
    return path

def trace_profit(memo, t0, t1, s0, s1, step):
    profits = []
    while t1 > t0:
        profits.append(memo[t0, t1, int(s0/step), int(s1/step), 0])
        prev_soc = memo[t0, t1, int(s0/step), int(s1/step), 1]  # Retrieve previous SOC
        t1 -= 1  # Move to the previous time step
        s1 = prev_soc  # Update SOC to the previous SOC
    profits.append(0)  # Append the starting profit
    profits.reverse()  # Reverse 
    return profits

def plot_power(memo, params, t0, t1, s0, s1, plt_obj):
    step = params['soc_step']
    prices_print = params['prices']
    loads_print = params['loads']
    times_print = np.arange(t1 - t0 + 1)  
    path_print = trace_path(memo,t0,t1,s0,s1,step)
    charge_print = np.diff(path_print, prepend=path_print[0]) * 3
    plt_obj.plot(times_print, prices_print * 100, label='Prices', color='blue', linestyle='-', marker='o')
    plt_obj.plot(times_print, loads_print, label='Loads', color='green', linestyle='--', marker='s')
    plt_obj.plot(times_print, charge_print, label='Charging', color='red', linestyle='-.', marker='d')
    plt_obj.xlabel('Time (20 mins)')
    plt_obj.ylabel('Values')
    plt_obj.title('100x Prices, Loads, and Charging power Over Time')
    plt_obj.legend()
    plt_obj.grid(True)
    plt_obj.show()

def plot_heatmap(memo, params, t0, s0, plt_obj):
    layer = memo[t0, :, s0, :, 0]
    max_time = params['hours']
    max_cap = params['battery_capacity']
    plt_obj.figure(figsize=(10, 8))
    heatmap = plt_obj.imshow(
        layer.T, 
        aspect="auto", 
        cmap="coolwarm", 
        origin="lower", 
        extent=[0, max_time, 0, max_cap]  # Set axis range
    )
    cbar = plt_obj.colorbar(heatmap)
    cbar.set_label("Profit/Cost Saving", fontsize=12)
    plt_obj.title("Heatmap of Memo Layer (t0=0, ini_soc=0)", fontsize=14)
    plt_obj.xlabel("Ending Time (hours)", fontsize=12)
    plt_obj.ylabel("Ending SOC", fontsize=12)
    plt_obj.xticks(ticks=np.arange(0, max_time + 1, 6))  # Every 6
    plt_obj.yticks(ticks=np.arange(0, max_cap + 1, 60))  # Every 60 SOC
    plt_obj.tight_layout()
    plt_obj.show()


