import types
from opendbc.car import Bus, structs
from opendbc.car.tesla.carstate import CarState
from opendbc.sunnypilot.car.tesla.carstate_ext import CarStateExt


class FakeParser:
  def __init__(self, vl):
    self.vl = vl


def _make_cs():
  CP = structs.CarParams.new_message()
  CP.carFingerprint = "TESLA_MODEL_S_HW1"
  CP_SP = types.SimpleNamespace(flags=0)
  return CarState(CP, CP_SP)


def test_hw1_reads_autopilot_status_speed_limit():
  cs = _make_cs()
  parsers = {
    Bus.party: FakeParser({"DI_state": {"DI_speedUnits": 0}}),      # 0 = MPH
    Bus.chassis: FakeParser({"DI_state": {"DI_speedUnits": 0}}),
    Bus.ap_party: FakeParser({"AutopilotStatus": {"DAS_fusedSpeedLimit": 15.0}}),
  }
  ret = types.SimpleNamespace()
  ret_sp = types.SimpleNamespace(speedLimit=0.0)
  CarStateExt.update(cs, ret, ret_sp, parsers)
  # 15 mph sign -> 6.7056 m/s
  assert abs(ret_sp.speedLimit - 15 * 0.44704) < 1e-4


def test_sna_limit_is_zero():
  cs = _make_cs()
  parsers = {
    Bus.party: FakeParser({"DI_state": {"DI_speedUnits": 0}}),
    Bus.chassis: FakeParser({"DI_state": {"DI_speedUnits": 0}}),
    Bus.ap_party: FakeParser({"AutopilotStatus": {"DAS_fusedSpeedLimit": 0.0}}),  # UNKNOWN_SNA
  }
  ret = types.SimpleNamespace()
  ret_sp = types.SimpleNamespace(speedLimit=0.0)
  CarStateExt.update(cs, ret, ret_sp, parsers)
  assert ret_sp.speedLimit == 0


def test_model3_das_status_still_works():
  CP = structs.CarParams.new_message()
  CP.carFingerprint = "TESLA_MODEL_3"
  cs = CarState(CP, types.SimpleNamespace(flags=0))
  parsers = {
    Bus.party: FakeParser({"DI_state": {"DI_speedUnits": 1}}),      # KPH
    Bus.ap_party: FakeParser({"DAS_status": {"DAS_fusedSpeedLimit": 50.0}}),
  }
  ret = types.SimpleNamespace()
  ret_sp = types.SimpleNamespace(speedLimit=0.0)
  CarStateExt.update(cs, ret, ret_sp, parsers)
  assert abs(ret_sp.speedLimit - 50 / 3.6) < 1e-4
