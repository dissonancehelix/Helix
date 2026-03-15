import numpy as np

def test_interaction_depth_win_condition():
    """
    Demonstrates the 'Mismatch' where DCP holds but standard lookahead fails.
    Scenario: Agent has depth 3. Adversary has depth 4.
    Environment is adaptive (Axiom VIII/Interaction Depth).
    """
    print("--- INTERACTION DEPTH ASYMMETRY TEST ---")
    
    # Simulation Parameters
    agent_lookahead = 3
    adv_reaction_depth = 4
    
    # The 'Trap' is not static. It is a 'Moving Shadow'.
    # Even if the agent sees all static traps at depth 3, 
    # the adversary can react to the agent's probe by placing a trap at depth 4
    # that the agent will hit exactly when it finishes its current plan.
    
    def simulate_game(d_agent, d_adv):
        # The agent's plan: [a1, a2, a3]
        # The adversary's reaction: Move world to lethal state s' at d_agent + 1
        # based on the agent's first action.
        if d_agent < d_adv:
            return "FAILURE (Trapped by deep reaction)"
        else:
            return "SURVIVAL (Agent dominates reaction)"

    result_mismatch = simulate_game(agent_lookahead, adv_reaction_depth)
    print(f"Agent Depth {agent_lookahead} vs Adv Depth {adv_reaction_depth}: {result_mismatch}")
    
    # Compare with standard MCTS (which usually assumes static environment branches)
    print("\n--- COMPARISON ---")
    print("Standard Viability Theory: 'If safe path exists, BFS finds it.'")
    print("DCP Interaction Axiom: 'If environment reacts deeper than you, no local search is safe.'")
    
if __name__ == "__main__":
    test_interaction_depth_win_condition()
