## consensus_network.gd
## Helix — Selective Consensus Network Simulation
##
## Godot headless script. Run with:
##   godot --headless --script domains/games/godot_engine/simulations/consensus_network.gd
##   godot --headless --script ... -- profile=dissonance n_agents=50 n_steps=200
##
## N agents each hold a belief b_i ∈ [0,1] about a hidden truth T.
## Agents share beliefs with neighbors each step, but only update based on
## neighbors whose trust exceeds a threshold.
##
## Profile mapping (DISSONANCE):
##   High trust threshold / delayed bonding  → trust_threshold: must exceed 0.60 to influence
##   Trust builds slowly                      → trust_build_rate: low per step
##   Betrayal sensitivity                     → trust_decay_rate: high when inconsistency detected
##   Schizoid self-sufficiency                → self_weight: own belief weighted 0.85
##   Cynicism as constraint detection         → cynicism_threshold: sudden belief shifts trigger decay
##   Selective attachment once formed         → max_trust amplifies trusted neighbors significantly
##   Low affective contagion                  → update_rate: even trusted neighbors move belief slowly

extends SceneTree

func _parse_args() -> Dictionary:
	var args = {}
	for token in OS.get_cmdline_user_args():
		var kv = token.split("=", true, 1)
		if kv.size() == 2:
			args[kv[0]] = kv[1]
	return args

func _profile(name: String) -> Dictionary:
	if name == "selective":
		return {
			"trust_threshold":     0.60,   # minimum trust to accept influence
			"trust_build_rate":    0.04,   # per-step trust gain when consistent
			"trust_decay_rate":    0.18,   # per-step trust loss on inconsistency
			"self_weight":         0.85,   # fraction of own belief retained
			"update_rate":         0.12,   # how much a trusted neighbor moves belief
			"cynicism_threshold":  0.20,   # belief delta that triggers cynicism decay
			"noise_std":           0.02,   # small belief noise per step (internal variability)
			"connection_prob":     0.20,   # sparse connections (low extraversion)
		}
	else:  # baseline
		return {
			"trust_threshold":     0.0,    # trust everyone immediately
			"trust_build_rate":    1.0,
			"trust_decay_rate":    0.0,
			"self_weight":         0.0,    # standard averaging
			"update_rate":         0.50,
			"cynicism_threshold":  1.0,    # never cynical
			"noise_std":           0.0,
			"connection_prob":     0.40,
		}

func _init():
	var args  = _parse_args()
	var pname = args.get("profile", "selective")
	var N     = int(args.get("n_agents", "50"))
	var STEPS = int(args.get("n_steps",  "200"))
	var SEED  = int(args.get("seed",     "42"))
	var TRUTH = float(args.get("truth",  "0.75"))
	var p     = _profile(pname)
	var rng   = RandomNumberGenerator.new()
	rng.seed  = SEED

	# --- Initialize beliefs (uniform random in [0,1]) ---
	var beliefs     : PackedFloat64Array = []
	var prev_beliefs: PackedFloat64Array = []
	# trust[i*N + j] = trust of i toward j
	var trust       : PackedFloat64Array = []
	# edges[i] = list of neighbor indices
	var edges = []

	beliefs.resize(N)
	prev_beliefs.resize(N)
	trust.resize(N * N)
	trust.fill(0.0)

	for i in range(N):
		beliefs[i]      = rng.randf()
		prev_beliefs[i] = beliefs[i]
		edges.append([])

	# --- Erdős–Rényi random graph ---
	for i in range(N):
		for j in range(i + 1, N):
			if rng.randf() < p["connection_prob"]:
				edges[i].append(j)
				edges[j].append(i)

	var steps_data = []
	var mean_error_series : PackedFloat64Array = []

	for step in range(STEPS):
		prev_beliefs = beliefs.duplicate()

		var new_beliefs = beliefs.duplicate()

		for i in range(N):
			var trusted_influence = 0.0
			var trusted_weight    = 0.0

			for j in edges[i]:
				var t = trust[i * N + j]
				if t >= p["trust_threshold"]:
					trusted_influence += t * beliefs[j]
					trusted_weight    += t

			if trusted_weight > 0.0:
				var external = trusted_influence / trusted_weight
				new_beliefs[i] = (p["self_weight"] * beliefs[i]
					+ (1.0 - p["self_weight"]) * p["update_rate"] * external
					+ (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i])
			# else: belief unchanged (no trusted neighbors updated this step)

			# Internal noise (Perceiving / internal variability)
			if p["noise_std"] > 0.0:
				new_beliefs[i] += rng.randf_range(-p["noise_std"], p["noise_std"])
			new_beliefs[i] = clampf(new_beliefs[i], 0.0, 1.0)

		# --- Update trust ---
		for i in range(N):
			for j in edges[i]:
				var belief_delta = absf(beliefs[j] - prev_beliefs[j])
				var t = trust[i * N + j]
				if belief_delta < p["cynicism_threshold"]:
					# Neighbor is being consistent
					trust[i * N + j] = minf(1.0, t + p["trust_build_rate"])
				else:
					# Sudden shift — cynicism fires
					trust[i * N + j] = maxf(0.0, t - p["trust_decay_rate"])

		beliefs = new_beliefs

		# --- Metrics ---
		var mean_belief = 0.0
		var mean_error  = 0.0
		var n_trusted   = 0

		for i in range(N):
			mean_belief += beliefs[i]
			mean_error  += absf(beliefs[i] - TRUTH)

		mean_belief /= N
		mean_error  /= N

		for i in range(N):
			for j in edges[i]:
				if trust[i * N + j] >= p["trust_threshold"]:
					n_trusted += 1
		n_trusted /= 2  # undirected

		var consensus_gap = 0.0
		for i in range(N):
			consensus_gap += absf(beliefs[i] - mean_belief)
		consensus_gap /= N

		mean_error_series.append(mean_error)

		steps_data.append({
			"step":               step,
			"mean_belief":        snappedf(mean_belief, 0.001),
			"mean_error":         snappedf(mean_error, 0.001),
			"consensus_gap":      snappedf(consensus_gap, 0.001),
			"n_trusted_edges":    n_trusted,
			"possibility_breadth": snappedf(consensus_gap, 0.001),  # divergence = open space
			"constraint_proxy":   snappedf(1.0 - consensus_gap, 0.001),
			"tension_proxy":      snappedf(_running_mean_error(mean_error_series), 0.001),
		})

	# --- Final accuracy ---
	var final_error = mean_error_series[-1] if mean_error_series.size() > 0 else 1.0
	var converged   = final_error < 0.05

	# --- Collapse step = first time consensus_gap < 0.10 ---
	var collapse_step = -1
	for i in range(steps_data.size()):
		if steps_data[i]["consensus_gap"] < 0.10:
			collapse_step = i; break

	print(JSON.stringify({
		"experiment":    "consensus_network",
		"profile":       pname,
		"n_agents":      N,
		"n_steps":       STEPS,
		"seed":          SEED,
		"truth":         TRUTH,
		"converged":     converged,
		"collapse_step": collapse_step,
		"final_error":   snappedf(final_error, 0.0001),
		"steps":         steps_data,
	}))
	quit()

func _running_mean_error(series: PackedFloat64Array) -> float:
	if series.size() == 0:
		return 0.0
	var window = mini(20, series.size())
	var s = 0.0
	for i in range(series.size() - window, series.size()):
		s += series[i]
	return s / window
