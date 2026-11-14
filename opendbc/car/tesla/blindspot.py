"""AP1 blind-spot flags from the stock Mobileye AutopilotStatus (0x399).

Adapted from BogPilot (github.com/BogPilot/openpilot, `selfdrive/car/tesla/blindspot.py`).

The stock DAS sends DAS_blindSpotRearLeft / DAS_blindSpotRearRight in 0x399.
Values (tesla_can.dbc): 0 NO_WARNING, 1 WARNING_LEVEL_1, 2 WARNING_LEVEL_2,
3 SNA. 1 and 2 count as a car in the blind spot. 0 and 3 do not set the flag.

0x399 arrives at roughly 2.4 Hz, so each side holds for BSM_HOLD_S after the
last frame that reported a warning. A single warning frame shows for
BSM_HOLD_S; a run of warning frames shows for the run plus BSM_HOLD_S.

Read-only: nothing here is sent to the car.
"""

BSM_HOLD_S = 1.0

BSM_LEFT = "DAS_blindSpotRearLeft"
BSM_RIGHT = "DAS_blindSpotRearRight"
BSM_DETECTED = (1, 2)  # WARNING_LEVEL_1, WARNING_LEVEL_2. 3 is SNA.


def detected(value) -> bool:
  try:
    return int(value) in BSM_DETECTED
  except (TypeError, ValueError):
    return False


def frames_from_vl_all(cp) -> list[dict]:
  """AP status frames received this step, oldest first, as {signal: value}.

  Legacy HW1/HW2 cars carry this in `AutopilotStatus` (0x399) on tesla_can;
  Model 3/Y carry it in `DAS_status` (0x3 9b) on tesla_model3_party.
  """
  name = "AutopilotStatus" if "AutopilotStatus" in cp.vl_all else "DAS_status"
  sigs = cp.vl_all.get(name, {})
  n = len(sigs.get(BSM_LEFT, []))
  out = []
  for i in range(n):
    frame = {}
    for name, values in sigs.items():
      if i < len(values):
        frame[name] = values[i]
    out.append(frame)
  return out


class Ap1Blindspot:
  """Per-side hold (latch-off delay) over the 0x399 blind-spot fields."""

  def __init__(self, hold_s: float = BSM_HOLD_S):
    self.hold_s = hold_s
    self.left_s = 0.0   # seconds of hold left
    self.right_s = 0.0

  @property
  def left(self) -> bool:
    return self.left_s > 0.0

  @property
  def right(self) -> bool:
    return self.right_s > 0.0

  def update(self, frames: list[dict], dt: float) -> tuple[bool, bool]:
    """Age the holds by dt, then apply this step's frames. Returns (left, right)."""
    self.left_s = max(0.0, self.left_s - dt)
    self.right_s = max(0.0, self.right_s - dt)
    for frame in frames:
      if detected(frame.get(BSM_LEFT)):
        self.left_s = self.hold_s
      if detected(frame.get(BSM_RIGHT)):
        self.right_s = self.hold_s
    return self.left, self.right
