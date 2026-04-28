from iosacal import R
import numpy as np

r = R(1000, 36, 'AC-107')
cal = r.calibrate('intcal20')
print(np.array(cal)[:5])
