import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates

# Define the timeline and temperature
times = [
    '14:00', # Initialized
    '14:08', # Added reagents
    '14:20', # Start ramp
    '14:40', # Reach 120 C (assuming 20 C start, 5 C/min)
    '15:25', # End 45 min hold
    '16:00', # Cooling down (estimated)
    '16:55'  # Decanted
]

temps = [
    20, # Assumed room temp
    20,
    20,
    120,
    120,
    20,
    20
]

# Convert strings to datetime objects
base_date = datetime.date(2024, 3, 12)
datetimes = [datetime.datetime.combine(base_date, datetime.datetime.strptime(t, '%H:%M').time()) for t in times]

plt.figure(figsize=(10, 6))
plt.plot(datetimes, temps, marker='o', linestyle='-', color='b', linewidth=2)

# Formatting the x-axis
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 15, 30, 45]))
plt.gcf().autofmt_xdate()

# Annotations
plt.annotate('Initialization', xy=(datetimes[0], temps[0]), xytext=(0, 15), textcoords='offset points', ha='center')
plt.annotate('Add Reagents', xy=(datetimes[1], temps[1]), xytext=(0, -20), textcoords='offset points', ha='center')
plt.annotate('Start Ramp\n(5 °C/min)', xy=(datetimes[2], temps[2]), xytext=(10, -30), textcoords='offset points', ha='center')
plt.annotate('Reach 120 °C', xy=(datetimes[3], temps[3]), xytext=(-20, 15), textcoords='offset points', ha='center')
plt.annotate('End 45 min Hold', xy=(datetimes[4], temps[4]), xytext=(20, 15), textcoords='offset points', ha='center')
plt.annotate('Centrifuge & Decant', xy=(datetimes[6], temps[6]), xytext=(0, 15), textcoords='offset points', ha='center')

plt.title('Theoretical Temperature Profile for Catalyst-X9 Synthesis')
plt.xlabel('Time (HH:MM)')
plt.ylabel('Temperature (°C)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('report/images/temperature_profile.png', dpi=300)
print('Saved temperature_profile.png')
