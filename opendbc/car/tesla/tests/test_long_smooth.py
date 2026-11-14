from opendbc.car.tesla.long_smooth import Ap1AccelSmoother


def test_rising_request_rate_limited():
  s = Ap1AccelSmoother()
  out = s.update(2.0, 10.0, True, dt=0.01)
  assert abs(out - 0.025) < 1e-9     # 2.5 m/s³ * 0.01 s


def test_braking_blends_to_eight():
  s = Ap1AccelSmoother()
  s.reset(0.0)
  out = s.update(-1.0, 10.0, True, dt=0.01)   # 2.0 m/s³
  assert abs(out - (-0.02)) < 1e-9
  s.reset(0.0)
  out = s.update(-1.5, 10.0, True, dt=0.01)   # 5.0 m/s³
  assert abs(out - (-0.05)) < 1e-9
  s.reset(0.0)
  out = s.update(-1.95, 10.0, True, dt=0.01)  # ~7.7 m/s³
  assert out < -0.07


def test_hard_braking_passes_through():
  s = Ap1AccelSmoother()
  s.reset(1.0)
  assert s.update(-2.0, 10.0, True, dt=0.01) == -2.0
  assert s.update(-3.0, 10.0, True, dt=0.01) == -3.0


def test_fcw_and_stopping_pass_through():
  s = Ap1AccelSmoother()
  s.reset(0.5)
  assert s.update(-0.8, 10.0, True, fcw=True, dt=0.01) == -0.8
  s.reset(0.5)
  assert s.update(-0.8, 10.0, True, stopping=True, dt=0.01) == -0.8


def test_low_speed_passes_through():
  s = Ap1AccelSmoother()
  s.reset(0.5)
  assert s.update(-1.0, 0.5, True, dt=0.01) == -1.0


def test_standstill_passes_through_below_one_mps():
  s = Ap1AccelSmoother()
  s.reset(-1.0)
  # BogPilot gates on AP1_SLEW_MIN_SPEED: at standstill the planner's
  # StopAccel is sent unchanged, not clamped by the smoother.
  assert s.update(-1.6, 0.0, True, standstill=True, dt=0.01) == -1.6


def test_standstill_floor_above_one_mps():
  s = Ap1AccelSmoother()
  s.reset(-1.0)
  # moving slowly but above the slew floor: hold at -1.0 instead of -1.6
  assert s.update(-1.6, 1.5, True, standstill=True, dt=0.01) == -1.0


def test_gas_pressed_neutral_and_inactive_reset():
  s = Ap1AccelSmoother()
  s.reset(1.0)
  assert s.update(1.5, 10.0, True, gas_pressed=True, dt=0.01) == 0.0
  assert s.last == 0.0
  assert s.update(0.4, 10.0, False, dt=0.01) == 0.4
  assert s.last == 0.4


def test_output_stays_between_last_and_target():
  s = Ap1AccelSmoother()
  for target in (1.5, -0.5, -1.2, 0.3):
    before = s.last
    out = s.update(target, 15.0, True, dt=0.01)
    lo, hi = min(before, target), max(before, target)
    assert lo - 1e-9 <= out <= hi + 1e-9
