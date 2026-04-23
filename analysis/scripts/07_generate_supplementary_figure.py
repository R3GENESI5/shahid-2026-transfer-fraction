"""
Fig 3 for Paper E v2: Trajectory analysis with control test.
Panel (a): Poleward drift and OLR enhancement (Amazon parcels)
Panel (b): Amazon vs Atlantic control comparison
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

RESULTS = os.path.join(os.path.dirname(__file__), '..', 'results', 'trajectory_olr_all_runs.csv')
FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

df = pd.read_csv(RESULTS)
days = [0, 5, 10, 15, 20]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
fig.subplots_adjust(wspace=0.35)

# Panel (a): OLR enhancement over time, all 28 runs
mean_enh = [df[df['day'] == d]['enhancement'].mean() for d in days]
std_enh = [df[df['day'] == d]['enhancement'].std() for d in days]
mean_lat = [df[df['day'] == d]['mean_lat'].mean() for d in days]

ax1.errorbar(days, mean_enh, yerr=std_enh, fmt='o-', color='#2d6a4f', lw=2.5,
             markersize=10, capsize=6, capthick=2, label='OLR enhancement')
ax1.axhline(0, color='gray', lw=0.5)

# Add latitude as secondary info
for d, e, la in zip(days, mean_enh, mean_lat):
    if d > 0:
        ax1.annotate(f'{la:.0f}\u00b0', (d, e), fontsize=8, color='#666',
                     xytext=(0, -18), textcoords='offset points', ha='center')

ax1.set_xlabel('Days after release from Amazon TTL', fontsize=11)
ax1.set_ylabel('OLR at parcel locations minus\nAmazon source OLR (W m$^{-2}$)', fontsize=11)
ax1.set_title('(a) Relay pathway: parcels reach high-OLR\nsubtropical zones within 5 days',
              fontsize=11, fontweight='bold')
ax1.text(12, mean_enh[2] + std_enh[2] + 3, '28 runs, 7 years\nall seasons',
         fontsize=9, color='#666', ha='center')
ax1.set_ylim(-10, 75)

# Panel (b): Control comparison
# Amazon vs Atlantic at day 20 by month
control_data = {
    'month': ['Jan', 'Apr', 'Jul', 'Oct'],
    'amazon_olr': [273.3, 273.9, 265.2, 272.1],
    'atlantic_olr': [287.9, 256.4, 269.0, 267.9],
}

x = np.arange(4)
w = 0.35
bars1 = ax2.bar(x - w/2, control_data['amazon_olr'], w, color='#2d6a4f',
                label='Amazon parcels', alpha=0.8, edgecolor='black', lw=0.5)
bars2 = ax2.bar(x + w/2, control_data['atlantic_olr'], w, color='#219ebc',
                label='Atlantic parcels (control)', alpha=0.8, edgecolor='black', lw=0.5)

# Difference annotations
for i in range(4):
    diff = control_data['amazon_olr'][i] - control_data['atlantic_olr'][i]
    y_pos = max(control_data['amazon_olr'][i], control_data['atlantic_olr'][i]) + 2
    ax2.text(x[i], y_pos, f'{diff:+.1f}', ha='center', fontsize=9, fontweight='bold',
             color='#D62828' if abs(diff) > 10 else '#666')

ax2.set_xticks(x)
ax2.set_xticklabels(control_data['month'], fontsize=10)
ax2.set_ylabel('OLR at day 20 endpoints (W m$^{-2}$)', fontsize=11)
ax2.set_title('(b) Control test: Amazon vs Atlantic\nsource parcels reach similar OLR',
              fontsize=11, fontweight='bold')
ax2.legend(fontsize=9, loc='lower right')
ax2.set_ylim(240, 300)
ax2.text(1.5, 244, 'No consistent Amazon advantage;\nrelay is shared infrastructure',
         fontsize=9, color='#666', ha='center', style='italic')

plt.savefig(os.path.join(FIG_DIR, 'Fig3_trajectory_control.png'), dpi=200,
            bbox_inches='tight', facecolor='white')
plt.savefig(os.path.join(FIG_DIR, 'Fig3_trajectory_control.pdf'),
            bbox_inches='tight', facecolor='white')
print('Saved Fig3_trajectory_control')
