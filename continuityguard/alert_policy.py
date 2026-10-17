"""Shared causal notification state for offline and live evaluation.

A persistent episode must be rechecked within the declared forecast horizon.
This prevents an old notification suppressing every later qualifying warning.
The same policy is applied to the static and learned detector comparisons.
"""
from collections import deque
from .simulation import SERVICES


class AlertTracker:
    def __init__(self, refresh_seconds=60):
        self.refresh_seconds=refresh_seconds
        self.windows={s:deque(maxlen=5) for s in SERVICES}
        self.latched={s:False for s in SERVICES}
        self.last={s:-float('inf') for s in SERVICES}

    def reset_service(self, service):
        self.windows[service].clear()
        self.latched[service]=False
        self.last[service]=-float('inf')

    def push(self, service, second, flag, ready=True, refresh_allowed=True):
        window=self.windows[service]
        window.append(bool(flag and ready))
        if not any(window):self.latched[service]=False
        age=second-self.last[service]
        if sum(window)>=3 and age>=30 and (not self.latched[service] or (age>=self.refresh_seconds and refresh_allowed)):
            self.last[service]=second
            self.latched[service]=True
            return True
        return False
