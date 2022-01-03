class SouthwestAPIError(Exception):
    pass


class ReservationNotFoundError(SouthwestAPIError):
    pass


class TooManyRequestsError(SouthwestAPIError):
    "This error is thrown when the authentication headers aren't included or they have expired"
    pass
