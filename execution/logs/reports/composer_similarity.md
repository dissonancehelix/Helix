# OPERATOR: COMPOSER SIMILARITY

**Type**: Operator  
**Status**: Verified  
**Origin**: Helix Music Lab  
**Domain Coverage**: Full Library Probabilistic Attribution  

## Mechanism

The Composer Similarity operator computes the stylistic distance between an unknown track and known composer fingerprints. It uses a **Bayesian Gaussian** model to assign attribution probabilities.

### Algorithm:
1. Load unknown track vector $V_t$.
2. For each composer profile $C_i$:
   - Compute Likelihood: $P(V_t | C_i)$ using Gaussian multivariate scoring.
   - Apply Musicological Prior: $P(C_i)$ from known credits/metadata.
3. Normalize to obtain Posterior Probability.

## Usage

```bash
RUN experiment:composer_attribution track:"Angel Island Zone"
```

## Evidence

- Successfully distinguishes between Brad Buxer and Jun Senoue on S3&K datasets with >80% confidence on key tracks (IceCap, Hydrocity).

## Linked Experiments

- [composer_attribution](file:///c:/Users/dissonance/Desktop/Helix/labs/music_lab/experiments/composer_attribution.py)
- [s3k_analysis](file:///c:/Users/dissonance/Desktop/Helix/labs/music_lab/experiments/s3k_analysis.py)
