from iosacal import R

r = R(1000, 36, 'AC-107')
cal = r.calibrate('intcal20')
print(type(cal.intervals[95]))
print(list(cal.intervals[95]))
