class HTTPieArgumentError(Exception):
    """Raised by argument processing logic to signal a user-facing error.
    Caught by HTTPieArgumentParser and converted to a proper error() call.
    """
    pass 