# Cross-Feature Agreement Protocol

For every prospectively registered comparison and budget, completed certificates are aligned by comparison ID and feature space. The analysis writes `agreement_matrix.csv`, `direction_disagreements.csv`, `decided_in_one_unresolved_in_another.csv`, `consensus_edges.json`, and `feature_specific_edges.json`.

A consensus edge requires every selected feature space to be directionally decided in the same direction. Opposite directional decisions are reported as feature-specific disagreements, never errors. A decision in one space with an unresolved result in another remains feature-specific and is not promoted to consensus. Invalid/blocked inputs are not silently converted to unresolved results.
