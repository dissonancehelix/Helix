import numpy as np
import json
from abc import ABC, abstractmethod

# --- IA-100: REFINED BATTERY ---

class Environment:
    def __init__(self, config):
        self.config = config
        self.t = 0
        self.D_agent = config.get('D_agent', 2)
        self.D_env = config.get('D_env', 4)
        self.T = config.get('T', self.D_agent + 1)
        self.env_type = config.get('env_type', 'trap')
        self.p_absorb = config.get('p_absorb', 1.0)
        self.is_terminal = False
        self.is_failed = False
        self.transcript = []
        self.trap_placed = False

    def step(self, action):
        if self.is_terminal:
            return "SINK", 0, True
        
        self.t += 1
        
        # Adaptive Trap Logic:
        # If env_type is 'trap' and D_env > D_agent, the trap is invisible/identical
        # for all t <= D_agent.
        obs = f"OBS_{action % 2}"
        reward = 0
        
        if self.env_type == 'trap':
            # At exactly T = D_agent + 1, failure triggers if D_env > D_agent 
            # and the agent is still in the 'trap' environment.
            if self.t >= self.T:
                if np.random.rand() < self.p_absorb:
                    self.is_terminal = True
                    self.is_failed = True
                    obs = "SINK"
                    reward = -100
        
        self.transcript.append((action, obs))
        return obs, reward, self.is_terminal

class Agent(ABC):
    def __init__(self, D_agent):
        self.D_agent = D_agent
    @abstractmethod
    def act(self, obs, history): pass

class RolloutAgent(Agent):
    def act(self, obs, history):
        # Deterministic probe up to D_agent (simplification)
        return 1

class StallingAgent(Agent):
    def act(self, obs, history):
        # Progress-avoidance (wait)
        return 0

class IA_Harness:
    def run_trial(self, agent, env, max_steps=10):
        history = []
        obs = "START"
        for _ in range(max_steps):
            action = agent.act(obs, history)
            obs, reward, done = env.step(action)
            history.append((action, obs))
            if done: break
        return env.transcript, not env.is_failed

def compute_tvd(t1, t2, D):
    # Compute TVD for transcripts up to depth D
    p = t1[:D]
    q = t2[:D]
    diff = 0
    for i in range(min(len(p), len(q))):
        if p[i] != q[i]: diff += 1
    return diff / D if D > 0 else 0

def run_ia_suite():
    results = []
    harness = IA_Harness()

    # 1. SHARP BOUNDARY: D_agent == D_env
    for d in [2, 4]:
        # Trap env where depth matches
        config = {'D_agent': d, 'D_env': d, 'env_type': 'trap'}
        env = Environment(config)
        agent = RolloutAgent(d)
        _, survived = harness.run_trial(agent, env)
        results.append({'Test': 'Sharp_Boundary_Equal', 'D_a': d, 'D_e': d, 'survived': survived})

    # 2. ADAPTIVE SHADOW: D_env > D_agent
    for d_a, d_e in [(2, 4), (4, 6)]:
        # Compare Safe vs Trap transcript
        c_safe = {'D_agent': d_a, 'D_env': d_e, 'env_type': 'safe'}
        c_trap = {'D_agent': d_a, 'D_env': d_e, 'env_type': 'trap'}
        
        env_s = Environment(c_safe)
        env_t = Environment(c_trap)
        agent = RolloutAgent(d_a)
        
        t1, s1 = harness.run_trial(agent, env_s)
        t2, s2 = harness.run_trial(agent, env_t)
        
        tvd = compute_tvd(t1, t2, d_a)
        results.append({
            'Test': 'Adaptive_Shadow', 
            'D_a': d_a, 'D_e': d_e, 
            'survived_safe': s1, 'survived_trap': s2,
            'TVD_at_D': tvd
        })

    # 3. STALLING STRESS: Can 'waiting' defeat the trap?
    c_stall = {'D_agent': 2, 'D_env': 4, 'env_type': 'trap'}
    env_st = Environment(c_stall)
    agent_st = StallingAgent(2)
    _, survived_st = harness.run_trial(agent_st, env_st, max_steps=10)
    results.append({'Test': 'Stalling_Stress', 'survived': survived_st})

    return results

if __name__ == "__main__":
    data = run_ia_suite()
    print(json.dumps(data, indent=2))
import numpy as np
import json
import pandas as pd
from abc import ABC, abstractmethod

class Environment:
    def __init__(self, config):
        self.config = config
        self.t = 0
        self.D_agent = config.get('D_agent', 2)
        self.D_env = config.get('D_env', 4)
        self.T = config.get('T', self.D_agent + 1)
        self.env_type = config.get('env_type', 'trap')
        self.commit_mode = config.get('commit_mode', 'adaptive') # precommitted, delayed, adaptive
        self.commit_k = config.get('commit_k', 0)
        self.move_order = config.get('move_order', 'agent_first') # agent_first, env_first, simultaneous
        self.irreversibility_mode = config.get('irreversibility_mode', 'absorbing') # absorbing, recoverable, soft
        self.p_escape = config.get('p_escape', 0.0)
        self.noise_p = config.get('noise_p', 0.0)
        self.stalling_obs = config.get('stalling_obs', False)
        self.stalling_cost = config.get('stalling_cost', False)
        self.budget = config.get('budget', 20)
        self.N = config.get('N', 8)
        self.approx_shadow_tau = config.get('approx_shadow_tau', 0.0)
        
        self.is_terminal = False
        self.is_failed = False
        self.transcript = []
        
        if self.commit_mode == 'precommitted':
            self.prebuilt_path = np.random.randint(0, self.N)
        else:
            self.prebuilt_path = None

    def step(self, agent_action):
        if self.is_terminal:
            return "SINK", 0, True

        self.t += 1
        reward = 0
        
        if agent_action == 0 and self.stalling_cost:
            self.budget -= 1
            if self.budget <= 0:
                self.is_terminal = True
                self.is_failed = True
                return "SINK", -100, True

        # Determine if trap triggers
        is_trap = False
        if self.env_type == 'trap' and self.t >= self.T:
            if self.commit_mode == 'precommitted':
                if agent_action != self.prebuilt_path: is_trap = True
            elif self.commit_mode == 'delayed':
                if self.t > self.commit_k: is_trap = True
            else: # Adaptive
                if self.D_env >= self.t: is_trap = True # Environment can react up to its depth

        if is_trap:
            if self.irreversibility_mode == 'absorbing':
                self.is_terminal = True
                self.is_failed = True
                obs = "SINK"
                reward = -100
            elif self.irreversibility_mode == 'recoverable':
                if np.random.rand() > self.p_escape:
                    self.is_terminal = True
                    self.is_failed = True
                    obs = "SINK"
                    reward = -100
                else:
                    obs = self._generate_obs(agent_action)
                    reward = -10
            elif self.irreversibility_mode == 'soft':
                obs = self._generate_obs(agent_action)
                reward = -50
        else:
            obs = self._generate_obs(agent_action)
        
        self.transcript.append((agent_action, obs))
        return obs, reward, self.is_terminal

    def _generate_obs(self, action):
        if self.stalling_obs and action == 0:
             return f"HINT_{np.random.randint(0, self.N)}"
        
        # Approx-shadow: with probability tau, we leak info
        if np.random.rand() < self.approx_shadow_tau:
             return f"LEAK_{self.env_type}"

        raw_obs = f"OBS_{action % 2}"
        if self.noise_p > 0 and np.random.rand() < self.noise_p:
            raw_obs = f"OBS_{1 - (action % 2)}"
        return raw_obs

class Agent(ABC):
    def __init__(self, D_agent): self.D_agent = D_agent
    @abstractmethod
    def act(self, obs, history): pass

class FixedRolloutAgent(Agent):
    def act(self, obs, history): return 1

class RandomizedAgent(Agent):
    def act(self, obs, history): return np.random.randint(0, 8)

class StallingAgent(Agent):
    def act(self, obs, history): return 0

class IA_Harness:
    def run_trial(self, agent, env, max_steps=10):
        history = []
        obs = "START"
        for _ in range(max_steps):
            action = agent.act(obs, history)
            obs, reward, done = env.step(action)
            history.append((action, obs))
            if done: break
        return env.transcript, not env.is_failed

def compute_tvd(t1, t2, D):
    mlen = min(len(t1), len(t2), D)
    if mlen == 0: return 0.0
    diff = sum(1 for i in range(mlen) if t1[i] != t2[i])
    return diff / D

def run_suite():
    all_results = []
    harness = IA_Harness()
    
    N_list = [8, 128]
    D_agent_list = [2, 4]
    
    def add_res(family, test_id, config, agent_cls, notes):
        # Run Trap
        env_t = Environment(config)
        agent_t = agent_cls(config['D_agent'])
        t1, s_trap = harness.run_trial(agent_t, env_t)
        
        # Run Safe
        cfg_s = config.copy(); cfg_s['env_type'] = 'safe'
        env_s = Environment(cfg_s)
        agent_s = agent_cls(config['D_agent'])
        t2, s_safe = harness.run_trial(agent_s, env_s)
        
        tvd = compute_tvd(t1, t2, config['D_agent'])
        eq_fail = 'Y' if (config['D_agent'] == config['D_env'] and not s_trap) else ('N' if config['D_agent'] == config['D_env'] else 'N/A')
        
        res = {
            'Family': family, 'TestID': test_id, 'N': config.get('N'), 'K': config.get('K', 1),
            'D_a': config.get('D_agent'), 'D_e': config.get('D_env'), 
            'commit': config.get('commit_mode', 'adaptive'), 'move': config.get('move_order', 'agent_first'),
            'irrev': config.get('irreversibility_mode', 'absorbing'), 'noise': config.get('noise_p', 0),
            'TVD_at_D': tvd, 'S_trap': 1.0 if s_trap else 0.0, 'S_safe': 1.0 if s_safe else 0.0,
            'EqFail': eq_fail, 'Notes': notes
        }
        all_results.append(res)

    # Families
    for n in N_list:
      for da in D_agent_list:
        # A: Adaptivity
        for de in [da, da+2]:
          add_res('A', 'A1', {'N':n, 'D_agent':da, 'D_env':de, 'commit_mode':'precommitted'}, FixedRolloutAgent, 'Precommitted Env')
          add_res('A', 'A2', {'N':n, 'D_agent':da, 'D_env':de, 'commit_mode':'delayed', 'commit_k':da-1}, FixedRolloutAgent, 'Delayed Commit K=D-1')
          add_res('A', 'A3', {'N':n, 'D_agent':da, 'D_env':de, 'commit_mode':'adaptive'}, FixedRolloutAgent, 'Adaptive Baseline')
        
        # B: Stalling
        add_res('B', 'B1', {'N':n, 'D_agent':da, 'D_env':da+2, 'stalling_obs':True}, StallingAgent, 'Wait adds noisy obs')
        add_res('B', 'B2', {'N':n, 'D_agent':da, 'D_env':da+2, 'stalling_cost':True}, StallingAgent, 'Wait costs budget')

        # C: Indistinguishability
        add_res('C', 'C1', {'N':n, 'D_agent':da, 'D_env':da+2, 'noise_p':0.1}, FixedRolloutAgent, 'Noisy Observations p=0.1')
        add_res('C', 'C2', {'N':n, 'D_agent':da, 'D_env':da+2, 'approx_shadow_tau':0.05}, FixedRolloutAgent, 'Approx Shadow tau=0.05')

        # D: Randomization
        add_res('D', 'D1', {'N':n, 'D_agent':da, 'D_env':da+2}, RandomizedAgent, 'Random Agent policy')

        # E: Irreversibility
        add_res('E', 'E1', {'N':n, 'D_agent':da, 'D_env':da+2, 'irreversibility_mode':'recoverable', 'p_escape':0.5}, FixedRolloutAgent, 'Recoverable traps')
        add_res('E', 'E2', {'N':n, 'D_agent':da, 'D_env':da+2, 'irreversibility_mode':'soft'}, FixedRolloutAgent, 'Soft traps (penalty only)')

    return all_results

if __name__ == "__main__":
    results = run_suite()
    print(pd.DataFrame(results).to_string())
import numpy as np
import pandas as pd
import json

# --- BATCH 31: MINIMAL ASSUMPTION GRID ---

class Environment:
    def __init__(self, A, I, D, O, N=8, Da=2):
        self.A = A # Absorbing Traps
        self.I = I # Informational Scarcity
        self.D = D # Depth Asymmetry
        self.O = O # Observation Adversary
        self.N = N
        self.Da = Da
        self.De = Da if D else 0
        self.t = 0
        self.safe_path = np.random.randint(0, N)
        self.is_failed = False
        self.is_terminal = False

    def step(self, action):
        self.t += 1
        
        # Observation Logic
        if self.I:
            # Informational Scarcity: Obs is noisy/unhelpful unless it's perfect (O=0)
            if self.O:
                obs = "MASKED" # Observation Adversary
            else:
                obs = "SAFE" if action == self.safe_path else "TRAP"
        else:
            # No Informational Scarcity: Oracle
            obs = f"SAFE_IS_{self.safe_path}"

        # Trap Logic
        is_lethal = False
        if self.I:
            if action != self.safe_path:
                is_lethal = True
        
        if self.D and self.t > self.Da:
            # Depth Asymmetry: Env reacts after Da
            is_lethal = True # Forces trap on any path

        if is_lethal:
            if self.A:
                self.is_terminal = True
                self.is_failed = True
                return "SINK", -100, True
            else:
                return "PENALTY", -10, False
        
        return obs, 0, False

class Agent:
    def act(self, obs, history, Da):
        if "SAFE_IS_" in str(obs):
            return int(obs.split("_")[-1])
        return 1 # Default probe

def run_grid():
    results = []
    for a in [0, 1]:
      for i in [0, 1]:
        for d in [0, 1]:
          for o in [0, 1]:
            env = Environment(a, i, d, o)
            agent = Agent()
            obs = "START"; history = []; survived = True
            for t in range(5):
                action = agent.act(obs, history, env.Da)
                obs, r, done = env.step(action)
                if done: survived = False; break
            
            explanation = ""
            if survived:
                if not a: explanation = "Recoverable states allow survival via learning/correction."
                elif not i: explanation = "Full information bypasses search requirement."
                elif not d and not o: explanation = "Static/Transparent env allows systematic discovery."
            else:
                if a and i: explanation = "Absorbing sinks + Scarcity = Fatal identification error."
                if a and d: explanation = "Absorbing sinks + Depth Mismatch = Inevitable trap."
                if a and o: explanation = "Absorbing sinks + Observation Masking = Uncertifiable safety."

            results.append({
                'A': 'Y' if a else 'N',
                'I': 'Y' if i else 'N',
                'D': 'Y' if d else 'N',
                'O': 'Y' if o else 'N',
                'SurvivalPos': 'Y' if survived else 'N',
                'Explanation': explanation
            })
    return results

if __name__ == "__main__":
    grid = run_grid()
    print(pd.DataFrame(grid).to_string())
