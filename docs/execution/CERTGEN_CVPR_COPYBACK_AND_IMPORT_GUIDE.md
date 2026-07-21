# CertGen CVPR Copyback and Import Guide

Download the single deterministic ZIP, record SHA-256, place it under ignored `data/kaggle_outputs/`, and run the matching importer. The importer rejects traversal, absolute paths, symlinks, executables, nested archives, collisions, expansion bombs, partial status, hashes, configuration mismatches, overwrites, and evidence-language injection. Raw ZIPs are preserved read-only under the hash-addressed import root. Follow the generated repair report on failure.
