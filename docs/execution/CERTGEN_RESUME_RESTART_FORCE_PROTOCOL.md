# Resume, Restart, and Force-New Protocol

- `resume`: reuse only completed, hash-validated samples/shards under the identical run, configuration, input and asset identities. Continue at the next incomplete unit.
- `restart`: quarantine the mutable prior run directory, preserve immutable inputs/logs, and recreate the same identity from zero.
- `force_new_run`: create a distinct timestamped run directory; never overwrite or merge it with an earlier run.

Changed configuration, reference, asset, preprocessing, revision or seed assignment is never resumable. Existing final ZIPs are immutable: identical content can be reused; changed content requires a new path. Quarantine is diagnostic state and is excluded from release archives.
