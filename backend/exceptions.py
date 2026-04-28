

# exceptions.py — Custom exception hierarchy for the backend
#
# We define our own exceptions so the API layer can catch them and return
# the correct HTTP status codes:
#   BackendError      → 500 Internal Server Error
#   ValidationError   → 400 Bad Request
#   RecordNotFoundError → 404 Not Found



# Base exception for all backend errors.
# Any unexpected failure in the service layer raises this.
class BackendError(Exception):
    
    def __init__(self, message: str = "An unexpected backend error occurred"):
        self.message = message
        super().__init__(self.message)


# Raised when the incoming sensor payload fails validation checks.
# e.g. missing sensor_id, non-numeric values, empty metrics dict.
class ValidationError(BackendError):
   

    def __init__(self, message: str = "Payload validation failed"):
        super().__init__(message)


# Raised when a data_id lookup returns no record from the database.
# The API translates this into an HTTP 404 response.
class RecordNotFoundError(BackendError):
   

    def __init__(self, data_id: str):
        self.data_id = data_id
        super().__init__(f"Record not found: {data_id}")

