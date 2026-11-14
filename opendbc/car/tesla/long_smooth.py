"""AP1 longitudinal accel shaping (adapted from BogPilot `long_smooth.py`).

AP1's LongControl PID gains are zero, so the planner `aTarget` reaches the drive
inverter unfiltered. On recorded routes that produced one-frame braking steps of
up to -2.4 m/s² and brake/gas reversals around radar lead jumps. This module
slews the request sent in DAS_control 0x2b9:

- rising requests (more accel or a brake release): 2.5 m/s³
- braking onset: 2.0 m/s³ at 0, blending linearly to 8 m/s³ by -2.0 m/s²
- standstill hold floor: -1.0 m/s² (lets the DI latch less HOLD pressure)
- gas pressed: neutral frame (0), latch cleared
- pass-through on the same step: request <= -2.0, FCW, the stopping state,
  below 1 m/s, and while long control is not active

Not ported: the 0.2 s drive-release S-curve and the gas-handoff aEgo latch.
ACCEL_MIN/ACCEL_MAX, STOP_DISTANCE and the panda limits are untouched.
"""

AP1_DRIVE_JERK = 2.5       # m/s³, rising requests
AP1_BRAKE_ONSET_JERK = 2.0 # m/s³ at 0 m/s²
AP1_BRAKE_JERK_MAX = 8.0   # m/s³ by -2.0 m/s²
AP1_STANDSTILL_HOLD_ACCEL = -1.0
AP1_GAS_NEUTRAL = 0.0


class Ap1AccelSmoother:
  """One update per control step; dt is the control period in seconds."""

  def __init__(self):
    self.last = 0.0

  def reset(self, value: float = 0.0):
    self.last = value

  def update(self, target: float, v_ego: float, active: bool,
             fcw: bool = False, stopping: bool = False,
             standstill: bool = False, gas_pressed: bool = False,
             dt: float = 0.01) -> float:
    if not active:
      self.last = target
      return target

    if gas_pressed:
      self.last = AP1_GAS_NEUTRAL
      return AP1_GAS_NEUTRAL

    # Same-step pass-through cases. Below 1 m/s (standstill hold, launch,
    # creep) the request goes out unchanged, matching BogPilot's
    # AP1_SLEW_MIN_SPEED gate.
    if target <= -2.0 or fcw or stopping or v_ego < 1.0:
      self.last = target
      return target

    if standstill:
      target = max(target, AP1_STANDSTILL_HOLD_ACCEL)

    if target > self.last:
      rate = AP1_DRIVE_JERK
    elif target < 0.0:
      # Braking: 2.0 m/s³ at 0, ramping to 8 m/s³ at -2.0.
      blend = min(1.0, max(0.0, (-target - 1.0) / 1.0))
      rate = AP1_BRAKE_ONSET_JERK + (AP1_BRAKE_JERK_MAX - AP1_BRAKE_ONSET_JERK) * blend
    else:
      rate = AP1_BRAKE_ONSET_JERK

    step = rate * max(0.0, dt)
    if target > self.last:
      self.last = min(target, self.last + step)
    else:
      self.last = max(target, self.last - step)
    return self.last
