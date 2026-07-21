# Provenance DAG Contract

Every stage artifact is a node with artifact/type/schema/content/configuration/study identity, parents, sources, creation identity, evidence class, claim permission, and validation state. Every edge states its dependency reason. `provenance verify` rejects missing parents, parent-hash changes, cycles, source-hash changes, and unregistered files in the study result root. JSON and DOT outputs are deterministic. This DAG is the lineage source for reports, certificates, rankings, replay, and claim validation. Pre-run claim permission is always false.
