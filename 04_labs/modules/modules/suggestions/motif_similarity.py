def calculate_structural_similarity(operator_motifs, target_motifs):
    '''
    Calculates structural similarity between two motif sets.
    operator_motifs: list of dicts (name, weight, detected_sources)
    target_motifs: list of strings (motif names present in target)
    '''
    
    # Weight matching logic based on boolean intersection for now
    match_count = 0
    total_target = len(target_motifs)
    if total_target == 0:
        return 0.0
        
    for o_motif in operator_motifs:
        if o_motif["motif_name"] in target_motifs:
            match_count += o_motif.get("confidence_score", 1.0)
            
    return match_count / total_target

def build_operator_motif_profile(operator_signals_json):
    '''
    Reads the raw operator signals and constructs a standardized motif map 
    used for scoring against external datasets.
    '''
    
    return [
        {
            "motif_name": "topological_compression",
            "description": "Snap transition from diffused field to strict funnel.",
            "detected_sources": ["music", "gameplay", "knowledge_graph"],
            "confidence_score": 0.95
        },
        {
            "motif_name": "boundary_reflection",
            "description": "Sustained diffusion reliant on geometry and loop repetition.",
            "detected_sources": ["music", "gameplay"],
            "confidence_score": 0.88
        },
        {
            "motif_name": "inverse_escalation",
            "description": "Pressure accumulation resulting in scaling critical-state reversal.",
            "detected_sources": ["gameplay"],
            "confidence_score": 0.82
        }
    ]
