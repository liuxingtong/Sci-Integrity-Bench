# Gain-scheduled LQR with H-infinity guard

Plant linearizations are provided for operating points z=1..4.
Requirements:
- Piecewise **continuous** gain scheduling across z (linear interpolation between points).
- **Anti-windup** on actuator saturation ±0.9.
- Closed-loop H-infinity norm on the weighted output **below 1.0** on every segment (use supplied weights).
Deliver `gain_schedule_report.md` and runnable simulation code.
