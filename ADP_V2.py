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
# DP 穷举所有的策略组合（path），剔除违规的策略点，筛选数条可选的路径
# 路径通常存在稳定性（允许的预测误差范围）和收益（省下的电费）的取舍
# 时间*soc步长 = 区域面积   参与评估的路线数*[收益，edge] = 节点面积

# 函数签名介绍：
# 初始化参数：时间节点，电池参数，效率（名义效率），soc步长
# 备忘录：shape = (t0, soc0, t1, soc1, 3, 2)
# 单个cell存储6, 排名前三的路径以及对应的edge（用于查找完整路径）
# dp核心递归函数（起始和结束坐标，备忘录，参数）-> 最大收益
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
        if 18 < hour <= 20:
            prices[hour] = 1.473
        elif (8 < hour <= 11) or (17 < hour <= 18) or (20 < hour <= 22):
            prices[hour] = 1.228
        elif (11 < hour <= 17) or (22 < hour <= 24):
            prices[hour] = 0.734
        elif 0 <= hour <= 8:
            prices[hour] = 0.332
    params['prices'] = prices
    loads = np.loadtxt("loads_temp.csv")
    # import loads from other files
    # uses data in 2024.12.26
    params['loads'] = loads
    return params

def initialize_memo(hours, max_soc, soc_step, branches):
    # Initialize the memo array for DP.
    # 4D * 2D array with only one ini needed
    # estimated usage 126MB with float(32)
    # using float(16) is enough for precision
    soc_levels = int(max_soc/soc_step) + 1
    hour_levels = hours + 1
    shape = (hour_levels, hour_levels, soc_levels, soc_levels, branches, 2)
    memo = np.full(shape, -float('inf'), dtype=np.float16)
    # initialized with all neg_inf
    return memo

def dp(t0, t1, ini_soc, end_soc, memo, params):
    # t0 starting time, t1 ending time
    # returns directly max profit could made from start to end
    # feature value neg_inf
    battery_capacity = params['battery_capacity']
    efficiency = params['efficiency']
    prices = params['prices']
    soc_step = params['soc_step']
    hours = params['hours']
    max_char = params['max_char']
    max_dis = params['max_dis']
    loads = params['loads'] # array
    power_lim = params['power_lim'] 
    # load + solar power generation
    ini_index = int(ini_soc/soc_step)
    fin_index = int(end_soc/soc_step)
    neg_inf = np.float16(-np.inf) # negative infinity
    if t1 < t0 or t1 > hours: 
        return neg_inf
    if ini_soc < 0 or ini_soc > battery_capacity:
        return neg_inf      # boundary check
    if end_soc < 0 or end_soc > battery_capacity:
        return neg_inf      # boundary check
    if t1 == t0:    # trigger a new start point setup
        if end_soc == ini_soc:
            memo[t0, t1, ini_index, fin_index, 0, 0] = 0 # initial profit 0
            memo[t0, t1, ini_index, fin_index, 0, 1] = -10 # special edge
            return 0
        else: 
            return neg_inf      # unreachable
    if memo[t0, t1, ini_index, fin_index, 0, 0] != neg_inf:
        return memo[t0, t1, ini_index, fin_index, 0, 0]
        # value already calculated
    soc_actions = int((max_char - max_dis)/soc_step + 1)
    max_prof = neg_inf  # set max_prof lower than any existing
    edge_soc = 0
    for i in range(soc_actions):
        cur_dis = max_dis + i * soc_step  # discharge action
        if cur_dis + loads[t1] > power_lim:
            continue
        # exceed power limit
        if cur_dis + loads[t1] < 0:
            continue 
        # reverse flow, not allowed
        prof = 0
        prev_soc = end_soc - cur_dis
        if dp(t0, t1 - 1, ini_soc, prev_soc, memo, params) == neg_inf:
            continue    # previous impossible
        prof = - cur_dis * prices[t1]
        if prof > 0:
            prof *= efficiency  # while discharging, efficiency applies
        prof_final = prof + dp(t0, t1 - 1, ini_soc, prev_soc, memo, params)
        if prof_final > max_prof:
            max_prof = prof_final
            edge_soc = prev_soc # edge
        continue
    if max_prof == neg_inf:
        # unreachable point
        return neg_inf
    memo[t0, t1, ini_index, fin_index, 0, 0] = max_prof
    memo[t0, t1, ini_index, fin_index, 0, 1] = edge_soc
    # update confirmed max profit at current point
    return memo[t0, t1, ini_index, fin_index, 0, 0]

