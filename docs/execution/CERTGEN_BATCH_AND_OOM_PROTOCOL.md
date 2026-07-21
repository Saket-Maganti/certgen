# Batch and OOM Protocol

Generation uses a real batch API when the model capability registry declares batching and per-image generator-list support. Sample IDs and seeds are immutable and ordered. A batch is accepted only after every temporary image decodes, has the expected RGB mode and dimensions, and receives a SHA-256 hash; files are then atomically promoted and appended to the manifest.

On a CUDA OOM the worker logs the event, clears the model/runtime cache, halves the batch, and retries the same sample identities. It stops at the frozen minimum batch size. Existing complete samples are reused only when sample ID, seed, model revision, configuration hash and image hash agree. Duplicate IDs/seeds and conflicting manifests fail closed.
