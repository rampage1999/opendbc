from opendbc.car.tesla.hso import (
  Ap1DriverYield, ap1_driver_input, ap1_lat_active, ap1_steering_pressed,
  AP1_RESUME_HOLD_S,
)


def test_thresholds():
  assert ap1_steering_pressed(2) and ap1_steering_pressed(3)
  assert not ap1_steering_pressed(1) and not ap1_steering_pressed(0)
  assert ap1_driver_input(1) and ap1_driver_input(3)
  assert not ap1_driver_input(0)
  assert ap1_lat_active(True, 0) and ap1_lat_active(True, 1)
  assert not ap1_lat_active(True, 2) and not ap1_lat_active(False, 0)


def test_pause_enters_and_resumes_after_hold():
  hso = Ap1DriverYield()
  assert hso.update(True, 0, 0.01) is False
  assert hso.update(True, 3, 0.01) is True
  assert hso.update(True, 1, 0.01) is True    # still held, count restarts
  assert hso.update(True, 0, 0.2) is True     # 0.2 s of quiet, not enough
  assert hso.update(True, 0, 0.05) is True
  assert hso.update(True, 0, 0.06) is False   # past 0.3 s, resumes
  assert hso.resumed is True


def test_level_one_restarts_quiet_window():
  hso = Ap1DriverYield()
  hso.update(True, 3, 0.01)
  hso.update(True, 0, 0.2)
  hso.update(True, 1, 0.01)   # driver touches again
  hso.update(True, 0, 0.2)
  assert hso.update(True, 0, 0.05) is True   # only 0.25 s since restart
  assert hso.update(True, 0, 0.06) is False


def test_disengage_clears_immediately():
  hso = Ap1DriverYield()
  hso.update(True, 3, 0.01)
  assert hso.update(False, 3, 0.01) is False
  assert hso.update(True, 0, 0.01) is False
  assert AP1_RESUME_HOLD_S == 0.3
