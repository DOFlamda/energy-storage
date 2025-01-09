import matplotlib.pyplot as plt
import numpy as np

def heatmap_plot(cost_data):
    # Plot the heatmap for cost over time and SOC
    plt.figure(figsize=(10, 6))
    plt.imshow(cost_data, aspect='auto', cmap='viridis', origin='lower', interpolation='nearest')
    plt.colorbar(label="Cost (Yuan)")
    plt.xlabel('SOC levels (10 kWh)')
    plt.ylabel('Time (Hours)')
    plt.title('Cost Over Time and SOC Levels')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

def soc_plot(hours, prices, path):
    # Define x-axis (0 to hours)
    x = list(range(hours + 1))  
    # Define y-axis
    y_soc = path
    y_prices = prices * 100
    if len(x) != len(y_soc) or len(x) != len(y_prices):
        raise ValueError("x and y arrays must have the same length")

    plt.figure(figsize=(10, 5))  # Set figure size

    plt.plot(x, y_soc, marker='o', linestyle='-', color='b', label='SOC (kWh)')

    plt.plot(x, y_prices, marker='x', linestyle='--', color='r', label='100x Electricity Price (¥/kWh)')

    plt.xlabel('Time (Hours)')
    plt.ylabel('SOC and Prices')
    plt.title('SOC and Electricity Prices Over Hours')

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.show()

