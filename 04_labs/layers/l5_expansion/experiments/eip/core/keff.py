import torch
import torch.nn as nn
from typing import Optional, Tuple, Union

def measure_keff(
    model: nn.Module,
    x: torch.Tensor,
    target_class: Optional[Union[int, torch.Tensor]] = None,
    eps: float = 1e-20
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Computes the effective participation dimension (k_eff) for a PyTorch model at a given input x.
    
    The metric k_eff = (||∇q||₁)² / (||∇q||₂)² measures how distributed the decision gradient is.
    - Low k_eff (e.g. ~1-10): The model's decision relies on a compressed, sparse subspace of features.
    - High k_eff (e.g. ~n): The model's decision is distributed broadly across the input features.
    
    Phase 3 experiments have demonstrated that distributed decisions (high k_eff) are 
    vulnerable to correlated adversarial shifts, even when standard L∞ PGD says the model is robust.

    Args:
        model: A PyTorch model (nn.Module or callable).
        x: Input tensor of shape (batch_size, ...).
        target_class: The class index to compute the gradient for (if output is multi-class logits).
                      If None, uses the model's top prediction for each example.
                      If the model outputs a scalar (binary classification), this is ignored.
        eps: Small value to prevent division by zero in the denominator.
                      
    Returns:
        k_eff: Tensor of shape (batch_size,) containing the k_eff values.
        grad_norm2: Tensor of shape (batch_size,) containing the scalar L2 norms (||∇q||₂).
    """
    # Clone and require grad to leave the original tensor unaffected
    x_in = x.clone().detach().requires_grad_(True)
    
    # Forward pass
    outputs = model(x_in)
    
    # Standardize output to shape (batch_size,)
    if outputs.dim() == 1 or (outputs.dim() == 2 and outputs.size(1) == 1):
        # Binary / Scalar output
        scores = outputs.view(-1)
    else:
        # Multi-class output (e.g., logits)
        if target_class is None:
            # By default, compute gradient with respect to what the model thinks is the correct class
            target_t = outputs.argmax(dim=-1, keepdim=True)
        elif isinstance(target_class, int):
            target_t = torch.full((outputs.size(0), 1), target_class, dtype=torch.long, device=outputs.device)
        else:
            # Tensor of targets matches batch dim
            target_t = target_class.view(-1, 1).long()
            
        scores = outputs.gather(1, target_t).view(-1)
        
    # Backward pass: compute gradient of the score w.r.t. the input
    # We use vector-Jacobian product to get gradients for the whole batch efficiently.
    v = torch.ones_like(scores)
    
    grad = torch.autograd.grad(
        outputs=scores,
        inputs=x_in,
        grad_outputs=v,
        create_graph=False,
        retain_graph=False,
        only_inputs=True
    )[0]
    
    # Flatten gradients per batch item (shape: [batch_size, num_features])
    grad_flat = grad.view(grad.size(0), -1)
    
    # Compute L1 norm: sum(|grad_i|)
    l1_norm = torch.sum(torch.abs(grad_flat), dim=1)
    
    # Compute squared L2 norm: sum((grad_i)^2)
    l2_sq = torch.sum(grad_flat ** 2, dim=1)
    
    # k_eff = (L1)^2 / (L2)^2
    k_eff = (l1_norm ** 2) / (l2_sq + eps)
    
    # Handle perfectly flat gradients (denominator ≈ 0)
    zero_mask = (l2_sq < eps)
    k_eff[zero_mask] = float('inf') # Follows C# harness convention
    
    grad_norm2 = torch.sqrt(l2_sq)
    
    return k_eff, grad_norm2
