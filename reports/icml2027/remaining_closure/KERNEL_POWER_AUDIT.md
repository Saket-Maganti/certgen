# Kernel/gamma power audit

50 cells (25 replicates each) compared prospectively fixed gamma values `[0.125, 0.25, 0.5, 1.0, 2.0]` at dimensions `[64, 768]` and budget 1000. No cell resolved under the current union-Hoeffding boundary; the 0/25 Wilson upper bound is approximately 0.1332.

Larger gamma increased absolute synthetic effects for symmetric multimodal shift (best tested 2.0) and mode dropping (best tested 1.0), but yielded no observed power at this budget. Gamma 0.5 remains frozen and unchanged. Any alternate gamma requires a new prospectively frozen study and independent validation; same-outcome tuning is prohibited. Full rows are in `reports/icml2027/power/KERNEL_POWER_AUDIT.csv`. `claim_allowed=false`.
