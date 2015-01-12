class NotAuthenticatedError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class RequestError(Exception):
    pass


class ResponseError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass