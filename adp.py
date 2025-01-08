import numpy as np

# 输入数据
T = 0.5  # 每个时间段的时长 (小时)
N = 96   # 时间间隔数量
load = np.array([6052.011,5904.847,5961.48,6052.028,6039.6,6023.882,6029.166,6096.898,6046.529,6128.213,5969.273,5762.747,5752.847,
5731.001,5613.234,5668.132,5623.084,5673.527,5776.209,5846.07,5784.962,5668.072,5726.106,5656.742,5711.072,5759.507,5768.952,5778.518,5843.385,5995.026,
6918.215,7265.336,7730.157,8408.099,8934.832,9428.197,9507.78,9779.303,9945.062,10007.561,10174.346,10503.369,10252.344,9957.939,9986.736,9703.984,
8860.837,8215.661,7815.897,7918.039,7909.448,8058.994,9459.872,10081.622,10286.709,10421.373,10355.028,10361.288,10603.32,10687.265,10888.695,10978.302,
10320.828,10591.377,10806.111,10988.393,11001.739,10972.78,11021.914,10155.77,9149.136,8773.158,8537.823,9258.466,9778.863,10136.97,10247.452,10233.059,
10420.701,10362.492,10267.398,10314.392,10480.834,10479.643,10118.317,9590.018,9338.194,9083.917,8773.589,8622.803,8595.28,8580.469,8391.465,8258.741,
7882.619,6633.753])

def electricity_price(hour):
    if 18 <= hour < 20:
        return 1.473
    elif (8 <= hour < 11) or (17 <= hour < 18) or (20 <= hour < 22):
        return 1.228
    elif (11 <= hour < 17) or (22 <= hour < 24):
        return 0.734
    elif 0 <= hour < 8:
        return 0.332
    else:
        raise ValueError("Invalid hour!")
# 参数
SOC = 0.0           # 初始 SOC
SOC_min, SOC_max = 0, 1
P_min, P_max = -200, 200  # 功率范围 (kW)
eta_c, eta_d = 0.9, 0.9  # 充放电效率
P_fixed = 0.3  # 固定功率

# 初始化
SOCs = [SOC]
costs = []
P_values = []

# 贪心策略
for t in range(N):
    hour = (t * T) % 24  # 当前小时
    p_t = electricity_price(hour)  # 当前时段电价
    load_t = load[t]

    # 决策：根据电价确定充电或放电
    if p_t < 0.5:  # 谷价，充电
        P = min(P_max, (SOC_max - SOC) / T, P_fixed)  # 限制充电功率
    elif p_t > 1.0:  # 峰价，放电
        P = max(P_min, (SOC_min - SOC) / T, -P_fixed)  # 限制放电功率
    else:  # 平价
        P = 0

    # 计算 E(t)
    if P > 0:  # 充电
        E_t = P * T * eta_c
        load_t += P  # 增加负载
    elif P < 0:  # 放电
        E_t = P * T / eta_d
    else:
        E_t = 0

    # 计算成本
    cost_t = (load_t - E_t) * p_t
    costs.append(cost_t)

    # 更新 SOC
    SOC += P * T
    SOC = np.clip(SOC, SOC_min, SOC_max)
    SOCs.append(SOC)
    P_values.append(P)

# 总成本
total_cost = sum(costs)


import matplotlib.pyplot as plt

# 可视化 SOC 和功率
plt.figure(figsize=(12, 6))

# SOC
plt.subplot(2, 1, 1)
plt.plot(range(N + 1), SOCs, label="SOC")
plt.xlabel("Time Interval")
plt.ylabel("SOC")
plt.title("State of Charge Over Time")
plt.grid(True)
plt.legend()

# 功率
plt.subplot(2, 1, 2)
plt.step(range(N), P_values, label="Power (kW)", where="mid")
plt.xlabel("Time Interval")
plt.ylabel("Power (kW)")
plt.title("Charging/Discharging Power")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# 输出结果
print(f"总成本: {total_cost:.2f} 元")
print(f"策略功率 (kW): {P_values}")
print(f"SOC 状态: {SOCs}")