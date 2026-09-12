import numpy as np
import matplotlib.pyplot as plt

# x range
x = np.linspace(0, 1, 500)



# function
def compute_y(k1, k2):
    c = 5 * (k1 ** k2)
    return (-c + (5 + c)/(1 + (x/k1)**k2)) * 100

# --------------------------------
# choose parameter sets
# --------------------------------
# 0.7 <= k2 <= 0.9
# 0.3 <= k1 <= 0.9
params = [
    (0.8, 0.8),
    (0.8, 1.0),
    (1.0, 1.0),
]

# --------------------------------
# plot
# --------------------------------
fig, ax = plt.subplots()

for k1, k2 in params:
    y = compute_y(k1, k2)
    ax.plot(x, y, label=f"k1={k1}, k2={k2}")

# grid every 1/12 on x-axis
xticks = np.arange(0, 1 + 1/12, 1/12)
ax.set_xticks(xticks)
ax.grid(axis="x", linestyle="--", alpha=0.6)

ax.set_xlabel("x")
ax.set_ylabel("f(x)")
ax.set_title("Effect of k1 and k2")
ax.legend()

plt.show()