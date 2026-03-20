import numpy as np

class OscillatorSystem:
    """
    Base class for individual and coupled oscillators.
    """
    def __init__(self, n_oscillators: int = 1, natural_freqs: np.ndarray = None):
        self.n = n_oscillators
        if natural_freqs is not None:
            self.omega = natural_freqs
        else:
            self.omega = np.random.uniform(0.5, 1.5, self.n)
        
        # Initial phases
        self.theta = np.random.uniform(0, 2 * np.pi, self.n)
        self.history = []

    def simulate(self, dt: float, steps: int):
        """
        Simple Euler integration for independent oscillators (no coupling).
        """
        self.history = []
        for _ in range(steps):
            self.theta = (self.theta + self.omega * dt) % (2 * np.pi)
            self.history.append(self.theta.copy())
        return np.array(self.history)

    def get_phases(self):
        return self.theta

    def get_history(self):
        return np.array(self.history)
