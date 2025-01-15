import numpy as np
import csv
import sys
from ADP_V2 import initialize_parameters, initialize_memo, dp
import matplotlib.pyplot as plt

params = initialize_parameters(24, 300, 600, 300, -300, 0.95, 20)
memo = initialize_memo(24, 600, 20, 3)
print(params['loads'])
print(dp(0,24,160,160,memo, params))
print(dp(0,12,160,160,memo, params))
print(dp(12,24,160,160,memo, params))
print(dp(3,4,40,80,memo, params))

rows, cols = 31, 25
prof_array = np.zeros((rows, cols))  # Initialize with zeros
for i in range(rows):
    for j in range(cols):
        prof_array[i, j] = dp(0, j, 160, i*20, memo, params)  # data filling
       
# Step 4: Display the array as a heatmap
plt.figure(figsize=(12, 6))
plt.imshow(prof_array, cmap='viridis', origin='lower', aspect='auto')
plt.colorbar(label='Value')  # Add a colorbar
plt.title('Max final profit gainable ending at (time, soc)')
plt.ylabel('initial soc, start = 160')
plt.xlabel('initial time, start = 0')
#plt.savefig("24_40_heatmap.jpg", dpi=300)
plt.show()





