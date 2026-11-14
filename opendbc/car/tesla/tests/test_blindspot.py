from opendbc.car.tesla.blindspot import Ap1Blindspot, frames_from_vl_all, detected, BSM_HOLD_S


class FakeParser:
  def __init__(self, frames):
    # frames: list of {signal: value}
    self.vl_all = {"DAS_status": {}}
    for frame in frames:
      for name, value in frame.items():
        self.vl_all["DAS_status"].setdefault(name, []).append(value)


def test_detected_levels():
  assert detected(1) and detected(2)
  assert not detected(0) and not detected(3)
  assert not detected(None) and not detected("SNA")


def test_frames_from_vl_all():
  cp = FakeParser([{"DAS_blindSpotRearLeft": 1, "DAS_blindSpotRearRight": 0},
                   {"DAS_blindSpotRearLeft": 0, "DAS_blindSpotRearRight": 2}])
  frames = frames_from_vl_all(cp)
  assert len(frames) == 2
  assert frames[0]["DAS_blindSpotRearLeft"] == 1
  assert frames[1]["DAS_blindSpotRearRight"] == 2


def test_hold_latches_and_expires():
  bsm = Ap1Blindspot(hold_s=1.0)
  left, right = bsm.update([{"DAS_blindSpotRearLeft": 1, "DAS_blindSpotRearRight": 0}], 0.0)
  assert (left, right) == (True, False)

  # no new frame: still latched just under the hold window
  left, right = bsm.update([], 0.9)
  assert (left, right) == (True, False)

  # hold expires
  left, right = bsm.update([], 0.2)
  assert (left, right) == (False, False)


def test_run_of_frames_keeps_hold():
  bsm = Ap1Blindspot(hold_s=1.0)
  bsm.update([{"DAS_blindSpotRearRight": 2}], 0.0)
  bsm.update([{"DAS_blindSpotRearRight": 2}], 0.4)
  left, right = bsm.update([], 0.9)
  assert right is True
  left, right = bsm.update([], 0.2)
  assert right is False


def test_sna_does_not_set_flag():
  bsm = Ap1Blindspot()
  left, right = bsm.update([{"DAS_blindSpotRearLeft": 3, "DAS_blindSpotRearRight": 0}], 0.0)
  assert (left, right) == (False, False)
  assert BSM_HOLD_S == 1.0
