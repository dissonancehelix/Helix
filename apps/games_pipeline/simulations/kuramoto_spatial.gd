## kuramoto_spatial.gd
## Helix — Spatial Kuramoto Oscillator Simulation
##
## Godot headless script. Run with:
##   godot --headless --script domains/games/godot_engine/simulations/kuramoto_spatial.gd
##   godot --headless --script ... -- profile=dissonance n_agents=64 n_steps=300
##
## Prints a single JSON object to stdout, then quits.
##
## Profile mapping (DISSONANCE):
##   Perceiving / delayed compression → high trust_window before locking
##   Low extraversion                 → small coupling_radius (neighbors only)
##   High internal variability        → omega_std (wide natural frequency spread)
##   Schizoid self-sufficiency        → self_weight (own phase weighted heavily)
##   High filtering / cynicism        → coherence_threshold (strict before trusting)
##   Trust builds slowly              → trust_build_rate is low
##   Betrayal sensitivity             → trust_decay_rate is high relative to build rate

extends SceneTree

# ---------------------------------------------------------------------------
# Parse CLI args  (key=value after "--")
# ---------------------------------------------------------------------------
func _parse_args() -> Dictionary:
	var args = {}
	var raw = OS.get_cmdline_user_args()
	for token in raw:
		var kv = token.split("=", true, 1)
		if kv.size() == 2:
			args[kv[0]] = kv[1]
	return args

# ---------------------------------------------------------------------------
# Profile definitions
# ---------------------------------------------------------------------------
func _profile(name: String) -> Dictionary:
	if name == "selective":
		return {
			"trust_window":          15,     # steps of coherence before trust increases
			"trust_build_rate":      0.06,   # per-step trust gain when coherent
			"trust_decay_rate":      0.15,   # per-step trust loss when incoherent
			"coupling_radius":       1,      # grid cells — immediate neighbors only
			"omega_std":             0.40,   # wide natural frequency spread
			"self_weight":           0.70,   # fraction of own phase retained
			"coherence_threshold":   0.08,   # |Δω| below this = coherent
			"coupling_K":            2.0,
		}
	else:  # baseline
		return {
			"trust_window":          1,
			"trust_build_rate":      1.0,    # instant full trust
			"trust_decay_rate":      0.0,
			"coupling_radius":       2,
			"omega_std":             0.20,
			"self_weight":           0.0,    # no self-weight — pure Kuramoto
			"coherence_threshold":   1.0,    # always coherent
			"coupling_K":            1.5,
		}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
func _init():
	var args   = _parse_args()
	var pname  = args.get("profile", "selective")
	var N      = int(args.get("n_agents", "64"))
	var STEPS  = int(args.get("n_steps",  "300"))
	var SEED   = int(args.get("seed",     "42"))
	var G      = int(sqrt(N))  # grid side length — N must be perfect square
	var p      = _profile(pname)
	var DT     = 0.05

	var rng = RandomNumberGenerator.new()
	rng.seed = SEED

	# --- Initialize agent state ---
	var phases  : PackedFloat64Array = []
	var omegas  : PackedFloat64Array = []
	# trust[i*N + j] = trust of agent i toward agent j
	var trust   : PackedFloat64Array = []

	phases.resize(N)
	omegas.resize(N)
	trust.resize(N * N)
	trust.fill(0.0)

	for i in range(N):
		phases[i] = rng.randf() * TAU
		omegas[i] = rng.randf_range(-p["omega_std"], p["omega_std"])

	# --- Simulate ---
	var steps_data = []
	var R_series : PackedFloat64Array = []

	for step in range(STEPS):
		var new_phases = phases.duplicate()

		for i in range(N):
			var ix = i % G
			var iy = i / G
			var influence = 0.0
			var r : int = p["coupling_radius"]

			for dxi in range(-r, r + 1):
				for dyi in range(-r, r + 1):
					if dxi == 0 and dyi == 0:
						continue
					var jx = ix + dxi
					var jy = iy + dyi
					if jx < 0 or jx >= G or jy < 0 or jy >= G:
						continue
					var j = jy * G + jx
					var t = trust[i * N + j]
					influence += t * sin(phases[j] - phases[i])

			var dphi = omegas[i] + (1.0 - p["self_weight"]) * p["coupling_K"] * influence
			new_phases[i] = phases[i] + dphi * DT

		# --- Update trust ---
		for i in range(N):
			var ix = i % G
			var iy = i / G
			var r : int = p["coupling_radius"]

			for dxi in range(-r, r + 1):
				for dyi in range(-r, r + 1):
					if dxi == 0 and dyi == 0:
						continue
					var jx = ix + dxi
					var jy = iy + dyi
					if jx < 0 or jx >= G or jy < 0 or jy >= G:
						continue
					var j = jy * G + jx
					var freq_diff = abs(omegas[j] - omegas[i])
					var t = trust[i * N + j]
					if freq_diff < p["coherence_threshold"]:
						trust[i * N + j] = minf(1.0, t + p["trust_build_rate"])
					else:
						trust[i * N + j] = maxf(0.0, t - p["trust_decay_rate"])

		phases = new_phases

		# --- Order parameter R (global synchrony) ---
		var cx = 0.0; var cy = 0.0
		for ph in phases:
			cx += cos(ph); cy += sin(ph)
		var R = sqrt(cx * cx + cy * cy) / N

		# --- Mean trust ---
		var total_trust = 0.0; var tc = 0
		for i in range(N):
			var ix = i % G; var iy = i / G
			var r : int = p["coupling_radius"]
			for dxi in range(-r, r + 1):
				for dyi in range(-r, r + 1):
					if dxi == 0 and dyi == 0: continue
					var jx = ix + dxi; var jy = iy + dyi
					if jx < 0 or jx >= G or jy < 0 or jy >= G: continue
					var j = jy * G + jx
					total_trust += trust[i * N + j]; tc += 1
		var mean_trust = total_trust / maxf(1, tc)

		R_series.append(R)
		steps_data.append({
			"step":               step,
			"order_parameter":    R,
			"mean_trust":         mean_trust,
			"possibility_breadth": 1.0 - R,
			"constraint_proxy":   mean_trust,
			"tension_proxy":      _tension(R_series),
		})

	# --- Detect locking event (first step R crosses 0.80) ---
	var lock_step = -1
	for i in range(R_series.size()):
		if R_series[i] >= 0.80:
			lock_step = i; break

	var result = {
		"experiment":   "kuramoto_spatial",
		"profile":      pname,
		"n_agents":     N,
		"n_steps":      STEPS,
		"seed":         SEED,
		"lock_step":    lock_step,
		"final_R":      R_series[-1] if R_series.size() > 0 else 0.0,
		"steps":        steps_data,
	}
	print(JSON.stringify(result))
	quit()

# Running tension = mean of last 10 R values subtracted from current R
func _tension(series: PackedFloat64Array) -> float:
	if series.size() < 2:
		return 0.0
	var window = mini(10, series.size())
	var recent_mean = 0.0
	for i in range(series.size() - window, series.size()):
		recent_mean += series[i]
	recent_mean /= window
	return absf(series[-1] - recent_mean)
