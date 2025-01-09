import numpy as np
from ADP_module import initialize_parameters, initialize_memo, dp, trace_path
from plotting import heatmap_plot, soc_plot

params = initialize_parameters()

# Initialize memoization table
memo = initialize_memo(params['hours'], params['battery_capacity'], params['soc_step'])

# Run dynamic programming to fill memo
# initial = final soc

print(dp(params['hours'], params['initial_soc'], memo, params))
# Trace the optimal path
path = trace_path(memo, params['initial_soc'], params['soc_step'], params['hours'])
print(path)
# Plot the heatmap of the cost
heatmap_plot(memo[:, :, 0])

# Plot the path on the heatmap
soc_plot(params['hours'], params['prices'], path)













