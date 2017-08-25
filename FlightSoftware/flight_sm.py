#!/usr/bin/env python2.7

"""
Flight state machine for BBB flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

from enum import Enum

class State(Enum):
    """
    Defines the flight software system states.
    """

    (
    # Startup state
    INITIAL,

    # Begun powering up PIM
    SEQ0_POWER_PAYLOAD,

    # Begun powering up cameras
    SEQ0_POWER_CAMERAS,

    # Recording images.
    SEQ0_RECORDING,

    # Have exited the ISS safety zone.
    EXIT_SAFETY_ZONE,

    # Error condition.  (WE SHOULD NEVER REACH THIS.)
    ERROR
    ) = range(6)


class Condition:
    """
    All predicates that define state transition conditions.
    """

    @staticmethod
    def can_power_payload():
        return True

    @staticmethod
    def can_power_cameras():
        return True

    @staticmethod
    def out_of_iss_safety_zone():
        # Time > 180s
        return True


class Action:
    """
    All actions associated with state transitions.
    """

    # There is a singleton instance of this class, set when it is constructed
    # during the initialization of the top-level software.
    # (And for testing purposes, a hardware mock instance can be injected.)
    HARDWARE = None

    @staticmethod
    def hw():
        """ Return the global singleton instance. """
        return Action.HARDWARE

    @staticmethod
    def do_power_payload():
        hw = Action.hw()
        hw.turn_on_cpm()

    @staticmethod
    def do_power_cameras():
        hw = Action.hw()
        hw.turn_on_cameras()

    @staticmethod
    def do_exit_iss_safety_zone():
        None # TODO


class Transitions:
    """
    State machine definition.
    """

    ALL = [
        #+----+--------------------------+---------------------
        # FROM STATE                     TO STATE
        #     TRANSITION CONDITION
        #     TRANSITION ACTION
        # +---+--------------------------+---------------------
        ( State.INITIAL,                 State.SEQ0_POWER_PAYLOAD,
              Condition.can_power_payload,
              Action.do_power_payload),

        ( State.SEQ0_POWER_PAYLOAD,      State.SEQ0_POWER_CAMERAS,
              Condition.can_power_cameras,
              Action.do_power_cameras),

        ( State.SEQ0_RECORDING,          State.EXIT_SAFETY_ZONE,
              Condition.out_of_iss_safety_zone,
              Action.do_exit_iss_safety_zone),
    ]

    @staticmethod
    def next(current_state):
        """
        Advance the state machine, if possible.

        We iterate through all transitions from the current state,
        in order, testing whether the transition condition is satisfied.
        If it is, the transition action is performed and the next state
        is returned.

        Otherwise, the current state is returned.
        """

        # Test all transitions in order.
        for (t_current, t_next, t_condition, t_action) in Transitions.ALL:
            if t_current == current_state and t_condition():
                t_action()
                return t_next
        # No transition is possible.  Remain in current state.
        t_next = t_current
