# Execution evidence for VerbaSync

## Scope of each proof

Local tests verify deterministic invariants, the leader's output normalization
and captured validator agreement/disagreement. They cannot by themselves prove
real GenVM execution or distributed model consensus. The controlled integration
run uses actual StudioNet GenVM, persistent storage, signed transactions and five
configured validator fixtures, with explicitly mocked LLM responses. Those
fixtures verify state behavior, not actual translation accuracy.

The main-deployment scenario uses StudioNet's default models, no custom
validators, no model response fixtures and `leader_only=False`. Its exact English,
Spanish and French inputs live in the contract, not on an external webpage.
Journal files distinguish these two runs through their `mocked` field.

## Current contract locations

- [Principal deployment](https://explorer-studio.genlayer.com/address/0x17a056cC6f3Eec6e6914f1dB02e02852B1Ca4322)
- [Controlled integration deployment](https://explorer-studio.genlayer.com/address/0x80Ca392FB9c81422d5362Be650cd7c3aC2EEF6AF)

Both use StudioNet chain 61999 and the selected main-account deployer. The
normalized deployed source SHA256 is
`7c0532bbfe129efe20af60145c14c508c404ed194308bd52db39139bca7e6e56`.
`gen_getContractCode` was compared byte-for-byte with the exact normalized source
before each network scenario. The repository contract uses LF line endings.

## Deterministic and SDK checks

The direct suite contains 59 passing tests: 52 protocol/semantic tests, five
transaction resumption safety tests and two Windows atomic journal recovery
tests. Lint and SDK validation pass; Pyright reports zero errors and warnings.
The public surface is 16 nonpayable writes and eight views.

The tested barriers include publisher/editor authority, exact source and locale
fingerprints, complete locale matrices, changed editor configuration, changed
parent editions, bounded translation attempts, numeric mismatch, uncertainty,
malformed semantic JSON, fabricated quotes, independent validator disagreement,
conservative freezing, immutable history, late-descendant adoption, subscriber
locale changes and explicit handoff withdrawal.

## Controlled on-chain lifecycle

The complete integration scenario contains 33 finalized contract writes:
29 successful writes and four expected policy refusals. It exercises every write
family and every public view. It covers a cancelled draft, qualified publication,
subscriber adoption, dismissed issue, publisher freeze, corrected successor,
rejected extra translation, selection of a previous qualified attempt, exact
locale approval, blocked premature retirement, subscriber withdrawal, successful
retirement and a later upheld issue freezing the new current edition.

Its LLM fixtures deliberately control semantic outcomes, including an upheld
issue on an otherwise equivalent short text. This is a state-transition test,
not evidence that such an issue is linguistically justified. Actual linguistic
decisions belong to the separately identified default-model run.

## Actual default-model outcome

All 18 writes on the principal deployment are FINALIZED: 17 SUCCESS and one
expected publication refusal before qualification. Four actual semantic reviews
stored these outcomes:

| Input | Actual consensus decision |
| --- | --- |
| Spanish instruction missing the prohibition | `divergent` |
| Corrected Spanish prohibition | `equivalent` |
| French prohibition | `equivalent` |
| Allegation that the corrected Spanish permits unplugging | `equivalent`, issue dismissed |

The complete English-source edition is now available with approved Spanish and
French vectors. The subscriber's exact manifest acknowledgement is persisted.
The original bad attempt remains visible and was not selected for publication.
No model-format rollback or replacement review was needed. Across both contracts,
51 writes finalized: 46 successes and five expected policy refusals, plus two
successful deployments. There are no signed value transfers.

## Finality and recovery

A test only passes after every recorded transaction is FINALIZED and its leader
execution result matches the expected success or refusal. ACCEPTED alone is not
execution proof. The integration run hit a temporary Windows destination-file
lock during final journal saving after all signed writes had already executed.
The existing journal was resumed; no successful transaction was replayed. Local
atomic rename retries are separately tested and do not retry network sends.

The scripts may replace a semantic review only after proving a FINALIZED
`[LLM_ERROR]` rollback of a nonpayable review. Successful, business-rejected or
ambiguous transactions are never automatically repeated. A run records any such
replacement separately in the public evidence instead of hiding failures.

## Inspectable records

- [Local test report](test-results.xml)
- [Integration test report](integration-results.xml)
- [Lint report](lint-results.json)
- [Type-check report](typecheck-results.json)
- [Deployment journal](deployment.json)
- [Controlled finalized transaction journal](integration-activity.json)
- [Default-model transaction journal](default-model-activity.json)
- [Allowlisted verification bundle](evidence/verification.json)

The verification exporter compares exact local credential values and private-key
hex variants against public candidate files without printing them. `.env` and
local caches remain ignored. Public addresses, transaction hashes, document text
and resulting semantic verdicts are intentionally inspectable.
