"""AP1 regen-sized comfort braking (adapted from BogPilot `regen_brake.py`).

On 2012-2016 Model S/X AP1 the brake pedal is friction-only; regen happens on
accelerator lift and tops out around 1-1.5 m/s² (about 1.0 m/s² at 30-35 mph).
Stock openpilot COMFORT_BRAKE is 2.5 m/s², so lead approaches start late and
need friction brakes.

The acados MPC model bakes COMFORT_BRAKE into its desired-distance cost, so we
do not regenerate the solver. Instead we shift the runtime `x_obstacle` by the
difference between the stock and the regen-sized desired distance:

  desired_dist(c) = v² / (2c) + t_follow·v + STOP_DISTANCE
  shift           = 0.5·v²·(1/c - 1/COMFORT_BRAKE)

Subtracting the shift from x_obstacle makes the cost identical to using the
smaller comfort brake. ACCEL_MIN, FCW/AEB, STOP_DISTANCE and the panda floor
are untouched, so hard braking still has full authority.
"""

STOCK_COMFORT_BRAKE = 2.5
AP1_REGEN_COMFORT_BRAKE = 1.0

HW1_CARS = ("TESLA_MODEL_S_HW1", "TESLA_MODEL_X_HW1")


def ap1_comfort_brake(fingerprint) -> float:
  """Comfort brake (m/s²) for the lead MPC cost; stock value for non-HW1."""
  if str(fingerprint) in HW1_CARS:
    return AP1_REGEN_COMFORT_BRAKE
  return STOCK_COMFORT_BRAKE


def obstacle_shift(v_ego: float, comfort_brake: float) -> float:
  """x_obstacle offset that emulates `comfort_brake` in the stock solver."""
  if comfort_brake <= 0.0 or comfort_brake >= STOCK_COMFORT_BRAKE:
    return 0.0
  return 0.5 * max(0.0, float(v_ego)) ** 2 * (1.0 / comfort_brake - 1.0 / STOCK_COMFORT_BRAKE)
