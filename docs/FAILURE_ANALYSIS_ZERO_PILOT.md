# Zero Pilot Failure Analysis

## Earlier failure found before the final heuristic revision

The first 36-question Zero Pilot run produced 14 intents and a cluster pair F1 of 0.585. Root cause: the deterministic fallback used broad overlapping concept aliases and greedy representative assignment, which created false merges and false splits.

## Fix

The fallback now uses narrower, non-overlapping concept aliases and a primary-concept scoring layer for strong anchors, while leaving ambiguous/no-anchor questions to the semantic fallback.

## Final controlled result

The same 36-question fixture now produces 8 intents and pair F1=1.0000.

## Important limitation

The fixture contains known concept structure and therefore does not prove general semantic performance. It proves that the deterministic offline fallback is internally consistent on this controlled scenario and gives us a better no-cloud demo baseline.

## Pilot implication

A real pilot must run with a large, unseen question corpus and compare against a manual baseline. Synthetic fixture performance must not be presented as customer validation.
