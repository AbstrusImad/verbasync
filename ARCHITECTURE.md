# Version vectors and publication barriers

VerbaSync is one atomic intelligent contract. All durable record bodies are
canonical JSON strings stored in `TreeMap[str, str]`; class-level `u256` counters
allocate IDs. Python dictionaries and arrays are transient decoded values, never
declared storage slots. There are no asynchronous cross-contract writes.

## Boundaries between subsystems

`publications` holds owner identity, source locale, mutable future-editor
configuration, subscribers and current edition. `editions` holds immutable
source snapshots and the translation matrix, approvals and publication history.
`translations` holds immutable candidate text and one persisted semantic review.
`issues` holds one public allegation per published cell and its independently
derived review. A publication write updates an edition, its parent and the
publication pointer atomically.

## Readiness predicates

For every required locale, every source segment must select an attempt whose
decision is equivalent. The full locale vector must have the exact fingerprint
approved by that edition's editor. The publication's current parent and editor
configuration revision must still equal the staged snapshots. The edition must
remain a draft. Any mismatch prevents publication without modifying the parent.

Changing a selected candidate always clears the affected locale approval, even
when selecting an older qualified attempt. Translation and source histories
cannot be rewritten to preserve an approval. A successful review is never
repeated; another attempt or canonical edition is a new protocol object.

## Three kinds of immutability

Text immutability fixes source and translation input. Manifest immutability fixes
the edition's published vector. Historical accountability preserves issues,
acknowledgements, withdrawal decisions and the successor chain. These do not mean
that availability is immutable: pending issues suspend availability and reviewed
divergence or uncertainty freezes the current edition.

## Replacement and retirement

A frozen edition can be superseded by another fully qualified draft; there is no
unfreeze. A predecessor retires only when a currently live descendant has been
acknowledged in each original snapshotted subscriber's locale, or the relevant
subscriber explicitly withdraws that handoff. Original unresolved issues also
block retirement. A publisher cannot erase subscriber requirements by altering
current subscriptions.

## Consensus authority

The model decides semantic correspondence only. It cannot set editor addresses,
release content, select arbitrary attempts, update counters, waive subscriber
requirements or move money. Deterministic code performs every state transition
after consensus has returned a normalized, independently checked verdict.
