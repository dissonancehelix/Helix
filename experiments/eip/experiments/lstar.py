import numpy as np

def verify_lstar_tightness():
    print("--- L* TIGHTNESS VERIFICATION (QUADRATIC BOWL) ---")
    
    # Parameters
    eta = 1.0     # Safety margin
    g_norm = 2.0  # Local gradient norm ||g||
    c_max = 5.0   # Curvature bound
    
    # Calculate L* using the theorem formula
    l_star = (-g_norm + np.sqrt(g_norm**2 + 2 * c_max * eta)) / c_max
    
    # Construct the worst-case quadratic bowl along the gradient direction x
    # q(x) = eta - g_norm * x - 0.5 * c_max * x^2  (x is distance along -g)
    def q(x):
        return eta - g_norm * x - 0.5 * c_max * x**2
    
    # At x = L_star, q(x) should be exactly 0
    margin_at_lstar = q(l_star)
    
    print(f"Parameters: eta={eta}, ||g||={g_norm}, Cmax={c_max}")
    print(f"Calculated L*: {l_star:.5f}")
    print(f"Safety Margin at L*: {margin_at_lstar:.5e}")
    
    is_tight = np.isclose(margin_at_lstar, 0.0, atol=1e-12)
    print(f"Tightness Confirmed (q(L*) == 0): {is_tight}")

if __name__ == "__main__":
    verify_lstar_tightness()
