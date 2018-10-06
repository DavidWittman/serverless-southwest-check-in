class SouthwestAPIError(Exception):
    pass


class ReservationCancelledError(Exception):
    pass


class ReservationNotFoundError(Exception):
    pass


class NotLastCheckIn(Exception):
    """
    This exception is raised in the check_in handler when additional
    check-ins remain. It is used to form a ghetto loop as described above.
    TODO(dw): Finish this description
    """
    pass
