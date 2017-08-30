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

    MAIN_START_SEQ0,
    MAIN_DONE_SEQ0,

    # Wait for O1 to clear the ISS
    MAIN_EXIT_ISS_SAFETY_ZONE,

    MAIN_START_POWER_CHECK,
    MAIN_DONE_POWER_CHECK,

    MAIN_START_GLOBALSTAR_TRANSMIT,
    MAIN_DONE_GLOBALSTAR_TRANSMIT,

    MAIN_START_SEQ2,

    # ---- SEQ0
    # This is executed once, immediately upon satellite deployment.

    # Begun powering up PIM
    SEQ0_POWER_PAYLOAD,

    # Begun powering up cameras
    SEQ0_POWER_CAMERAS,

    # Recording images.
    SEQ0_RECORDING,

    # Error condition.  (WE SHOULD NEVER REACH THIS.)
    ERROR
    ) = range(13)


class Condition:
    """
    All predicates that define state transition conditions.
    """

    @staticmethod
    def always():
        return True

    @staticmethod
    def can_power_payload():
        return True

    @staticmethod
    def can_power_cameras():
        return True

    @staticmethod
    def out_of_iss_safety_zone():
        # Time > 1800s
        return Action.hw().time() > 1800

    @staticmethod
    def received_go_command():
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
    def nothing():
        None

    @staticmethod
    def do_power_payload():
        hw = Action.hw()
        hw.power_cpm(True)

    @staticmethod
    def do_power_cameras():
        hw = Action.hw()
        hw.power_cameras(True)

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
        ( State.INITIAL,                 State.MAIN_START_SEQ0,
              Condition.always,
              Action.nothing),

        ( State.MAIN_DONE_SEQ0,          State.MAIN_EXIT_ISS_SAFETY_ZONE,
              Condition.always,
              Action.nothing),

        ( State.MAIN_EXIT_ISS_SAFETY_ZONE, State.MAIN_START_POWER_CHECK,
              Condition.out_of_iss_safety_zone,
              Action.nothing),

        ( State.MAIN_DONE_POWER_CHECK,   State.MAIN_START_GLOBALSTAR_TRANSMIT,
              Condition.always,
              Action.nothing),

        ( State.MAIN_DONE_GLOBALSTAR_TRANSMIT, State.MAIN_START_SEQ2,
              Condition.received_go_command,
              Action.nothing),
        ( State.MAIN_DONE_GLOBALSTAR_TRANSMIT, State.MAIN_START_POWER_CHECK,
              Condition.always,
              Action.nothing),

        # -------------- SEQ0 ---------------------------------

        # !!!!!! TODO !!!!!!!!!!

        ( State.MAIN_START_SEQ0,      State.SEQ0_POWER_PAYLOAD,
              Condition.always,
              Action.nothing),

        ( State.SEQ0_POWER_PAYLOAD,      State.SEQ0_POWER_CAMERAS,
              Condition.can_power_cameras,
              Action.do_power_cameras),

        ( State.SEQ0_RECORDING,          State.MAIN_DONE_SEQ0,
              Condition.always,
              Action.nothing),


        # -------------- POWER_CHECK SEQ ---------------------

        # !!!!!! TODO !!!!!!!!!!
        ( State.MAIN_START_POWER_CHECK,  State.MAIN_DONE_POWER_CHECK,
              Condition.always,
              Action.nothing),


        # -------------- GLOBALSTAR_TRANSMIT SEQ ---------------------

        # !!!!!! TODO !!!!!!!!!!
        ( State.MAIN_START_GLOBALSTAR_TRANSMIT,  State.MAIN_DONE_GLOBALSTAR_TRANSMIT,
              Condition.always,
              Action.nothing),

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
        return current_state
