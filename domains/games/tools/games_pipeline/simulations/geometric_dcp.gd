## geometric_dcp.gd
## Helix — Geometric DCP Simulation
##
## Godot headless script. Run with:
##   godot --headless --script domains/games/godot_engine/simulations/geometric_dcp.gd
##   godot --headless --script ... -- profile=dissonance grid_size=32 n_steps=200
##
## Simulates an agent navigating a 2D grid whose navigable area geometrically
## narrows over time. Uses flood-fill to compute possibility_breadth at each step.
##
## The agent follows the Dissonance cognitive loop:
##   EXPAND  → explore the full navigable space, count reachable cells
##   PRUNE   → detect and mark dead-end paths (cells that no longer connect to goal)
##   COMMIT  → when breadth falls below commit_threshold, navigate directly to goal
##   RESET   → log result, prepare for next run
##
## Profile mapping (DISSONANCE):
##   High openness / Perceiving   → explore_bias: stays in EXPAND phase longer
##   Delayed compression          → commit_threshold: only commits when very few options remain
##   Backtrack on contradiction   → when path is blocked, re-enters EXPAND not COMMIT
##   Bimodal conscientiousness    → effort spikes in EXPAND and COMMIT, slow in PRUNE

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
			"explore_bias":        0.80,   # probability of random move in EXPAND phase
			"commit_threshold":    0.15,   # breadth must fall below this to enter COMMIT
			"prune_patience":      3,      # steps in PRUNE before returning to EXPAND
			"backtrack_on_block":  true,   # if path blocked, re-enter EXPAND
			"wall_advance_rate":   0.015,  # grid fraction walls advance per step
		}
	else:  # baseline
		return {
			"explore_bias":        0.30,
			"commit_threshold":    0.35,   # commits early
			"prune_patience":      1,
			"backtrack_on_block":  false,
			"wall_advance_rate":   0.015,
		}

# States
const EXPAND = 0
const PRUNE  = 1
const COMMIT = 2
const DONE   = 3

func _init():
	var args  = _parse_args()
	var pname = args.get("profile", "selective")
	var G     = int(args.get("grid_size", "32"))
	var STEPS = int(args.get("n_steps",   "200"))
	var SEED  = int(args.get("seed",      "42"))
	var p     = _profile(pname)
	var rng   = RandomNumberGenerator.new()
	rng.seed  = SEED

	# Grid: 0 = open, 1 = wall
	# Start = top-left, Goal = bottom-right
	var grid = PackedInt32Array()
	grid.resize(G * G)
	grid.fill(0)

	var start_pos = Vector2i(1, 1)
	var goal_pos  = Vector2i(G - 2, G - 2)

	# Walls advance inward from all sides
	var wall_margin = 0  # grows each step
	var agent_pos   = start_pos
	var agent_state = EXPAND
	var prune_count = 0

	var steps_data = []

	for step in range(STEPS):
		# --- Advance walls ---
		var new_margin = int(step * p["wall_advance_rate"])
		if new_margin != wall_margin:
			wall_margin = new_margin
			# Fill border cells
			for x in range(G):
				for y in range(G):
					var is_border = (x < wall_margin or x >= G - wall_margin
						or y < wall_margin or y >= G - wall_margin)
					if is_border and not (Vector2i(x, y) == start_pos or Vector2i(x, y) == goal_pos):
						grid[y * G + x] = 1

		# Clamp agent if walls caught it
		if grid[agent_pos.y * G + agent_pos.x] == 1:
			agent_pos = _find_open_near(grid, agent_pos, G)

		# --- Compute possibility_breadth via flood fill ---
		var reachable = _flood_fill(grid, agent_pos, G)
		var total_open = 0
		for v in grid:
			if v == 0:
				total_open += 1
		var breadth = float(reachable) / float(maxi(1, (G - 2) * (G - 2)))

		# --- Constraint and tension ---
		var constraint = 1.0 - breadth

		# --- State machine ---
		var moved = false
		match agent_state:
			EXPAND:
				if breadth < p["commit_threshold"]:
					agent_state = COMMIT
				elif rng.randf() < p["explore_bias"]:
					# Random walk within reachable area
					var moved_to = _random_step(grid, agent_pos, G, rng)
					if moved_to != agent_pos:
						agent_pos = moved_to
						moved = true
					else:
						agent_state = PRUNE
						prune_count = 0
				else:
					agent_state = PRUNE
					prune_count = 0

			PRUNE:
				prune_count += 1
				if prune_count >= p["prune_patience"]:
					agent_state = EXPAND

			COMMIT:
				# Move toward goal using simple gradient (BFS would be better but GDScript limitation)
				var step_toward = _step_toward(grid, agent_pos, goal_pos, G, rng)
				if step_toward == agent_pos and p["backtrack_on_block"]:
					agent_state = EXPAND
				else:
					agent_pos = step_toward
					moved = true
					if agent_pos == goal_pos:
						agent_state = DONE

			DONE:
				pass

		# --- Collapse detection ---
		var collapse_flag  = (breadth < p["commit_threshold"] and agent_state == COMMIT)
		var goal_reached   = (agent_pos == goal_pos)

		steps_data.append({
			"step":               step,
			"possibility_breadth": snappedf(breadth, 0.001),
			"constraint_proxy":   snappedf(constraint, 0.001),
			"tension_proxy":      snappedf(constraint * float(step) / float(STEPS), 0.001),
			"agent_state":        ["EXPAND","PRUNE","COMMIT","DONE"][agent_state],
			"wall_margin":        wall_margin,
			"reachable_cells":    reachable,
			"collapse_flag":      collapse_flag,
			"goal_reached":       goal_reached,
		})

		if agent_state == DONE:
			break

	var collapse_step = -1
	for i in range(steps_data.size()):
		if steps_data[i]["collapse_flag"]:
			collapse_step = i; break

	print(JSON.stringify({
		"experiment":    "geometric_dcp",
		"profile":       pname,
		"grid_size":     G,
		"n_steps":       STEPS,
		"seed":          SEED,
		"collapse_step": collapse_step,
		"goal_reached":  steps_data[-1]["goal_reached"] if steps_data.size() > 0 else false,
		"final_breadth": steps_data[-1]["possibility_breadth"] if steps_data.size() > 0 else 0.0,
		"steps":         steps_data,
	}))
	quit()

func _flood_fill(grid: PackedInt32Array, start: Vector2i, G: int) -> int:
	var visited = {}
	var queue   = [start]
	var count   = 0
	while queue.size() > 0:
		var cur = queue.pop_front()
		var key = cur.x * 1000 + cur.y
		if visited.has(key):
			continue
		if cur.x < 0 or cur.x >= G or cur.y < 0 or cur.y >= G:
			continue
		if grid[cur.y * G + cur.x] == 1:
			continue
		visited[key] = true
		count += 1
		queue.append(Vector2i(cur.x + 1, cur.y))
		queue.append(Vector2i(cur.x - 1, cur.y))
		queue.append(Vector2i(cur.x, cur.y + 1))
		queue.append(Vector2i(cur.x, cur.y - 1))
	return count

func _random_step(grid: PackedInt32Array, pos: Vector2i, G: int, rng: RandomNumberGenerator) -> Vector2i:
	var dirs = [Vector2i(1,0), Vector2i(-1,0), Vector2i(0,1), Vector2i(0,-1)]
	dirs.shuffle()
	for d in dirs:
		var np = pos + d
		if np.x >= 0 and np.x < G and np.y >= 0 and np.y < G and grid[np.y * G + np.x] == 0:
			return np
	return pos

func _step_toward(grid: PackedInt32Array, pos: Vector2i, goal: Vector2i, G: int, rng: RandomNumberGenerator) -> Vector2i:
	# Greedy gradient toward goal, prefer open cells
	var best = pos
	var best_dist = pos.distance_to(goal)
	var dirs = [Vector2i(1,0), Vector2i(-1,0), Vector2i(0,1), Vector2i(0,-1)]
	for d in dirs:
		var np = pos + d
		if np.x >= 0 and np.x < G and np.y >= 0 and np.y < G and grid[np.y * G + np.x] == 0:
			var dist = np.distance_to(goal)
			if dist < best_dist:
				best_dist = dist
				best = np
	return best

func _find_open_near(grid: PackedInt32Array, pos: Vector2i, G: int) -> Vector2i:
	for r in range(1, G):
		for dx in range(-r, r + 1):
			for dy in range(-r, r + 1):
				var np = pos + Vector2i(dx, dy)
				if np.x >= 0 and np.x < G and np.y >= 0 and np.y < G and grid[np.y * G + np.x] == 0:
					return np
	return Vector2i(1, 1)
