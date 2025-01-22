import numpy as np
import csv
import sys
from BESS_DP_V3 import initialize_parameters, initialize_memo
from BESS_DP_V3 import iterative_dp, trace_path, trace_profit, plot_heatmap, plot_power
import matplotlib.pyplot as plt
# choose max_soc = 600 for calculation 
# 600 = 40x3x5
# loads_temp now uses 2024.12.22 with 20 min interval
# power step length = 15
# SOC step length = 15/3 = 5   max_step = 200 in 20 minutes
params = initialize_parameters(72, 300, 600, 300, -300, 0.95, 5)
memo = initialize_memo(72, 600, 5)
iterative_dp(0, 0, 72, memo, params)
def memo_printer(t0, t1, soc0, soc1, soc_step):
    ini_index = int(soc0 / soc_step)
    fin_index = int(soc1 / soc_step)
    print(memo[t0, t1, ini_index, fin_index, 0],memo[t0, t1, ini_index, fin_index, 1])
    
memo_printer(0, 72, 0, 0, 5)
memo_printer(0, 72, 0, 60, 5)

plot_heatmap(memo, params, 0, 0, plt)

plot_power(memo, params, 0, 72, 0, 0, plt)


