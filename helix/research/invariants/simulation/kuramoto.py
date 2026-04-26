import numpy as np
from .oscillator import OscillatorSystem

class KuramotoSystem(OscillatorSystem):
    """
    Kuramoto model of coupled oscillators.
    d_theta_i / dt = omega_i + (K/N) * sum_j(sin(theta_j - theta_i))
    """
    def __init__(self, n_oscillators: int, K: float = 1.0, natural_freqs: np.ndarray = None, adjacency: np.ndarray = None):
        super().__init__(n_oscillators, natural_freqs)
        self.K = K
        # If adjacency is None, assume all-to-all coupling
        if adjacency is not None:
            self.adj = adjacency
        else:
            self.adj = np.ones((n_oscillators, n_oscillators)) - np.eye(n_oscillators)

    def compute_derivatives(self, theta):
        # theta is (N,)
        # theta_j - theta_i
        phase_diffs = theta[None, :] - theta[:, None]
        coupling = (self.K / self.n) * np.sum(self.adj * np.sin(phase_diffs), axis=1)
        return self.omega + coupling

    def simulate(self, dt: float, steps: int):
        self.history = []
        for _ in range(steps):
            # 4th order Runge-Kutta
            k1 = self.compute_derivatives(self.theta)
            k2 = self.compute_derivatives(self.theta + 0.5 * dt * k1)
            k3 = self.compute_derivatives(self.theta + 0.5 * dt * k2)
            k4 = self.compute_derivatives(self.theta + dt * k3)
            
            self.theta = (self.theta + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)) % (2 * np.pi)
            self.history.append(self.theta.copy())
            
        return np.array(self.history)

    def order_parameter(self, theta=None):
        """
        Calculates the complex order parameter R * exp(i * psi).
        R is the sync index (0 to 1).
        """
        if theta is None:
            theta = self.theta
        z = np.mean(np.exp(1j * theta))
        return np.abs(z), np.angle(z)

    def get_results_summary(self):
        r, _ = self.order_parameter()
        return {
            "n_oscillators": self.n,
            "K": self.K,
            "sync_index": float(r),
            "final_phases": self.theta.tolist()
        }
