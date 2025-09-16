import time
from enum import Enum

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, max_failures: int = 3, reset_timeout: int = 60):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = State.CLOSED
        self.opened_at = None

    def record_success(self):
        self.failures = 0
        self.state = State.CLOSED
        self.opened_at = None

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.max_failures:
            self.state = State.OPEN
            self.opened_at = time.time()

    def allow_request(self) -> bool:
        # If closed -> allow
        if self.state == State.CLOSED:
            return True
        # If open -> check timeout -> move to HALF_OPEN
        if self.state == State.OPEN:
            if (time.time() - (self.opened_at or 0)) >= self.reset_timeout:
                self.state = State.HALF_OPEN
                return True
            return False
        # HALF_OPEN -> allow a trial request
        if self.state == State.HALF_OPEN:
            return True
        return False
