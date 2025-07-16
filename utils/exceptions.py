class EmailConfigurationError(Exception):
    """Custom exception for missing email server configuration."""
    pass

class EmailSendingError(Exception):
    """Custom exception for failures during the email sending process."""
    pass