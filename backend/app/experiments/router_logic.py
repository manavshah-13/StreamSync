import hashlib
from typing import Union

def assign_experiment_variant(identifier: Union[str, int], experiment_id: Union[str, int]) -> str:
    """
    Statelessly assigns a user_id or session_id to an experiment variant (A or B)
    using deterministic MD5 hashing.
    
    Args:
        identifier: A unique identifier for the subject (e.g. user_id or session_id).
        experiment_id: A unique key identifying the active experiment.
        
    Returns:
        'A' or 'B' representing the assigned group.
    """
    # Coerce arguments to strings
    id_str = str(identifier)
    exp_str = str(experiment_id)
    
    # Combine identifier and experiment_id to make bucket assignments specific to each experiment
    combined = f"{id_str}:{exp_str}"
    
    # Compute the MD5 hash
    hasher = hashlib.md5(combined.encode("utf-8"))
    hex_digest = hasher.hexdigest()
    
    # Convert hex digest to integer and bucket into 100 groups (0-99)
    hash_int = int(hex_digest, 16)
    bucket = hash_int % 100
    
    # Strict 50/50 split
    if bucket < 50:
        return "A"
    else:
        return "B"
