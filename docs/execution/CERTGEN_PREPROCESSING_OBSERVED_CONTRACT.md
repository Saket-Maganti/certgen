# Observed Preprocessing Contract

The expected contract fixes extractor ID, model identifier and revision, processor class, input/resize/crop sizes, crop mode, interpolation, antialiasing, pixel range, RGB order, mean, standard deviation, feature normalization, precision, output dimension and package versions.

Workers derive an observed contract from the instantiated torchvision or Transformers processor. Expected and observed normalized objects must be exactly equal before feature extraction. A machine-readable difference report identifies every field mismatch. `TBD`, `UNKNOWN`, missing revision, or an unobserved processor blocks configuration freeze; declared YAML alone is not runtime proof.
