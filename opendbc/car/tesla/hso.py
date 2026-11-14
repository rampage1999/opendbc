"""AP1 hands-on pause (HSO), adapted from BogPilot (`selfdrive/car/tesla/hso.py`).

Tinkla's original behaviour: when the driver takes the wheel firmly the EPAS
reports `EPAS_handsOnLevel >= 2`. openpilot then withholds the lateral command
(type NONE) without dropping cruise, so the driver can steer around something
and openpilot resumes afterwards.

AP1 EPAS logs levels 0, 1 and 3 in practice (never 2): level 1 is light torque
and stays a normal `steeringPressed` override, level 3 is the firm override that
pauses lateral. The pause therefore latches on >= 2 and only releases after the
driver has been back at level 0 for AP1_RESUME_HOLD_S, so the handoff does not
chatter when the wheel is released and re-gripped.

This module is pure logic; CarController owns the CAN side.
"""

AP1_HANDS_ON_LEVEL = 2      # lateral pause threshold
AP1_DRIVER_INPUT_LEVEL = 1  # carState.steeringPressed threshold (display/override)
AP1_RESUME_HOLD_S = 0.3     # level-0 quiet time before lateral resumes


def ap1_steering_pressed(hands_on_level: int) -> bool:
  """True at the HSO threshold (lateral pause). Level 1 does not pause."""
  return hands_on_level >= AP1_HANDS_ON_LEVEL


def ap1_driver_input(hands_on_level: int) -> bool:
  """carState.steeringPressed on AP1: any driver torque EPAS reports."""
  return hands_on_level >= AP1_DRIVER_INPUT_LEVEL


class Ap1DriverYield:
  """Engaged-only hands pause with a resume hold. One update per control step.

  Enters at hands_on_level >= AP1_HANDS_ON_LEVEL while enabled. Stays active
  until hands_on_level has been 0 for AP1_RESUME_HOLD_S in a row; any level
  >= 1 restarts the count. Not enabled clears it at once, so disengage and
  re-engage are not delayed. `resumed` is true only on the step the hold ends.
  """

  def __init__(self, resume_hold_s: float = AP1_RESUME_HOLD_S):
    self.resume_hold_s = resume_hold_s
    self.active = False
    self.quiet_s = 0.0
    self.resumed = False

  def update(self, enabled: bool, hands_on_level: int, dt: float) -> bool:
    self.resumed = False
    if not enabled:
      self.active = False
      self.quiet_s = 0.0
      return False

    if ap1_steering_pressed(hands_on_level):
      self.active = True
      self.quiet_s = 0.0
    elif self.active:
      if ap1_driver_input(hands_on_level):
        self.quiet_s = 0.0
      else:
        self.quiet_s += max(0.0, dt)
        if self.quiet_s >= self.resume_hold_s:
          self.active = False
          self.quiet_s = 0.0
          self.resumed = True

    return self.active


def ap1_lat_active(lat_active: bool, hands_on_level: int) -> bool:
  """Path lateral is off while hands are at or above the HSO threshold."""
  if ap1_steering_pressed(hands_on_level):
    return False
  return bool(lat_active)
