# Pilot Stop/Go Protocol

Rules are frozen before the 1k outcomes. Any failed operational, control, metric, or certificate integrity gate yields `REPAIR`. If all gates pass but every primary comparison is unresolved, yield `STOP`. Otherwise yield `SCALE_TO_10K`, requiring a new prospective study version. `ADD_DINO`, `ADD_CFM`, or `ADD_SECOND_BENCHMARK` is eligible only after the corresponding real preflight/preregistration passes and the primary decision is `SCALE_TO_10K`. No representation disagreement is averaged away.
