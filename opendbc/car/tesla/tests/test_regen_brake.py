from opendbc.car.tesla.regen_brake import (
  ap1_comfort_brake, obstacle_shift, AP1_REGEN_COMFORT_BRAKE, STOCK_COMFORT_BRAKE,
)


def test_comfort_brake_selection():
  assert ap1_comfort_brake("TESLA_MODEL_S_HW1") == AP1_REGEN_COMFORT_BRAKE
  assert ap1_comfort_brake("TESLA_MODEL_X_HW1") == AP1_REGEN_COMFORT_BRAKE
  assert ap1_comfort_brake("TESLA_MODEL_S_HW3") == STOCK_COMFORT_BRAKE
  assert ap1_comfort_brake("TOYOTA_COROLLA_TSS2") == STOCK_COMFORT_BRAKE


def test_obstacle_shift_matches_desired_distance_delta():
  v = 15.0  # ~33 mph
  shift = obstacle_shift(v, AP1_REGEN_COMFORT_BRAKE)
  expected = v**2 / (2 * AP1_REGEN_COMFORT_BRAKE) - v**2 / (2 * STOCK_COMFORT_BRAKE)
  assert abs(shift - expected) < 1e-9
  # 33 mph: regen-sized distance is ~67 m longer than the stock 2.5 m/s² one
  assert 60 < shift < 70


def test_obstacle_shift_is_noop_for_stock_or_faster():
  assert obstacle_shift(20.0, STOCK_COMFORT_BRAKE) == 0.0
  assert obstacle_shift(20.0, 3.0) == 0.0
  assert obstacle_shift(-5.0, AP1_REGEN_COMFORT_BRAKE) == 0.0
