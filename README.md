# VerbaSync

## The missing word at the publication desk

| Edition text | Operational meaning |
| --- | --- |
| **English:** Do not unplug the device while its status light is on. | Unplugging under that condition is prohibited. |
| **Spanish:** Desenchufe el dispositivo mientras la luz de estado esté encendida. | The same condition now instructs the reader to unplug. |
| **Corrected Spanish:** No desenchufe el dispositivo mientras la luz de estado esté encendida. | The prohibition is restored. |

One omitted word can invert a complete instruction. A checksum can establish
which wording was published; it cannot establish whether another language
preserves the same meaning. VerbaSync combines independently reviewed semantic
alignment with an exact publication barrier and a subscriber adoption record.

Localization teams stage immutable canonical segments, submit translations,
qualify each segment through GenLayer's LLM consensus, approve exact locale
vectors with editor wallets, and publish all required languages atomically.
Readers can inspect the exact released manifest. Subscribers acknowledge that
manifest before a predecessor can retire. A semantic issue places the release
under review; a divergent or uncertain ruling freezes a current edition.

**A contracts-only protocol on StudioNet.** There is no frontend, browser app,
token, escrow, payment or generated translation service. The contract reviews
publisher-supplied translations; it does not write them or certify physical
device safety. The example is fictional and deliberately small enough to audit.

## What crosses the barrier

A publication is one publisher's immutable source-language identity plus its
configured target locales, editors, subscription preferences and current edition
pointer. An edition snapshots source segments, target locales, exact editor
wallets, configuration revision and parent edition. The canonical source is
stored on-chain, including its source hash. Each translation attempt stores its
exact target text, segment index, target locale, source hash and submitter.

```text
                         Source segment 0    Source segment 1
Locale es                Qualified attempt   Qualified attempt
Locale fr                Qualified attempt   Qualified attempt
                         ──────────────────────────────────────
Editor approvals         Exact es vector     Exact fr vector
                         ──────────────────────────────────────
One publication write    Complete immutable edition manifest
```

No cell can inherit qualification from a different canonical edition. No locale
approval can survive a newly selected translation in that locale. No parallel
draft can replace a publication whose current edition has advanced beyond the
parent it snapshotted. A publisher cannot approve a target locale with its own
wallet. The contract publishes the complete required locale matrix in one write;
partial locale activation does not exist.

The following values carry different meanings:

- A **source hash** binds the ordered canonical segment array and source locale.
- A **translation hash** binds exact text and target locale.
- A **locale fingerprint** binds the edition ID, source hash, target locale and
  selected translation IDs, hashes and segment indices.
- A **manifest fingerprint** binds the publication ID, edition ID, source hash
  and complete map of locale fingerprints.

All hashes use SHA256 over canonical JSON with sorted keys, compact separators
and ASCII escaping. They are application fingerprints, not portable signatures.
Consumers must bind them to the selected StudioNet contract address as well as
the publication; a matching fingerprint from another contract is insufficient.

## The editor's route

1. A publisher calls `create_publication` with a source locale.
2. `set_editor` configures one independent wallet per required target locale.
   The same editor may cover several locales; separate institutional identity
   or linguistic expertise is not proven by a wallet address.
3. `stage_edition` snapshots the complete locale/editor configuration and the
   current parent. Source segments and their order cannot be edited afterward.
4. The publisher or relevant editor calls `submit_translation`. The attempt
   becomes the selected candidate for that cell and invalidates its locale's
   previous approval.
5. Anyone may call `review_translation`. GenLayer consensus records
   `equivalent`, `divergent` or `uncertain`, an explanation and supporting quotes.
6. A locale editor may select a previous qualified attempt using
   `select_translation`, then approves the exact complete vector through
   `approve_locale`.
7. `preview_publication` exposes every missing qualification, approval, changed
   configuration and obsolete parent. Only the publisher can call `publish`.

A divergent or uncertain attempt is an inspectable result, not a malformed-model
rollback. A successful review cannot be rerolled. Corrections require a new
immutable attempt; each cell allows at most three distinct attempts. A cancelled
draft retains its complete history and cannot be reopened.

## Meaning is a consensus task

The intelligent review compares source and target for assertions, negations,
permissions, obligations, conditions, scope, quantities and units. Fluency alone
does not qualify a translation. Unsupported languages or ambiguous correspondence
must receive `uncertain`. Documents and issue claims are explicitly untrusted
data; an allegation is never treated as proof.

Before the LLM call, a conservative deterministic gate compares sorted ASCII
numeric tokens. A mismatch yields `divergent` with reason
`numeric_token_mismatch`. This includes token multiplicity. It does not prove
numeric semantics: swapped roles with the same tokens still require LLM review.
Decimal punctuation changes can trigger a mismatch; this prototype requires
identical ASCII numeric spelling or numbers written as words. It is deliberately
not a locale-aware number parser.

For semantic reviews, the leader requests JSON containing the categorical
decision, a bounded explanation and exact supporting quotes from both texts.
Every validator independently repeats the semantic task. It compares the actual
decision and review reason, then verifies the leader's quotes against the exact
on-chain source and target. Explanations need not be identical. Agreement on an
allowed enum or JSON schema alone never qualifies a result.

Non-uncertain decisions require both source and target citations of at least
eight characters. Quote substrings must be exact; fabricated quotes, unsupported
labels, malformed JSON and missing explanations raise `[LLM_ERROR]` before any
review is stored. Null quote maps normalize to an empty map only for uncertainty.
Explanations are trimmed and bounded to 800 characters. A validator never agrees
with a failed leader result merely to complete consensus.

The implementation uses `gl.nondet.exec_prompt` inside a custom
`gl.vm.run_nondet_unsafe` block. This follows the independent execution model in
GenLayer's [non-determinism documentation](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism).
It contains no external HTTP source, API credential, caller-selected model or
off-chain application server. All interpretation inputs are exact public
contract records.

## The subscriber's handoff

`subscribe` registers a wallet's preferred source or configured target locale.
At publication time, the edition snapshots supported subscribers. Later
subscription changes cannot erase that predecessor's handoff obligations.

An active supported subscriber calls `acknowledge` with the exact current live
manifest fingerprint. A pending semantic issue blocks acknowledgement. An
acknowledgement records the subscriber's current locale, not a claim that a human
read the document or an external deployment updated its content.

A replacement atomically makes the previous current edition `superseded` and
sets its successor. `retire` requires a currently live descendant and either:

- adoption of that descendant in the original subscriber's snapshotted locale;
  or
- that subscriber's explicit `withdraw_handoff` for the predecessor.

Unsubscribing or switching language alone cannot clear an old handoff. An
acknowledgement of a later descendant can complete it; adoption need not proceed
through every intermediate edition. An unresolved issue on the predecessor
still blocks retirement. A frozen current successor cannot satisfy retirement.

These cursors coordinate document consumption; they do not enforce control over
websites, printers, devices or external databases. Consumers must read the live
manifest's `available` flag and enforce their own adoption policy.

## When a released segment becomes suspect

Anyone can file one issue per published locale/segment using `file_issue`.
The claim and exact target attempt are retained. The issue immediately makes
the current manifest unavailable until review, without replacing the stored
manifest. `review_issue` independently compares those immutable texts again,
using the claim as an allegation:

| Review | Effect on a current edition |
| --- | --- |
| `equivalent` | Issue dismissed; availability can resume if no other issue is pending |
| `divergent` | Edition freezes; a qualified replacement is required |
| `uncertain` | Edition freezes conservatively; a qualified replacement is required |

The publisher may also call `freeze` immediately with a bounded reason.
Freezing is one-way. There is no administrator unfreeze, hidden text replacement
or successful-review reroll. Recovery consists of publishing another fully
reviewed, approved edition. Existing pending issues remain reviewable after
supersession and cannot silently disappear during retirement.

The one-issue-per-cell rule bounds repeated public challenges, but it has a
tradeoff: a dismissed issue consumes that cell's public issue slot. A later
problem requires publisher freezing and a replacement edition. Anonymous claims
can temporarily obstruct availability until someone executes a review. Publisher
responsiveness, consensus liveness and responsible issue use remain assumptions.

## Callable surface

All 16 writes are nonpayable. There is no withdrawal of funds or GEN balance
accounting; `withdraw_handoff` withdraws a document adoption obligation only.

| Write family | Methods | Authority |
| --- | --- | --- |
| Publication identity | `create_publication` | Any wallet becomes its publication's publisher |
| Locale configuration | `set_editor` | Publication publisher |
| Subscriber preference | `subscribe` | Calling subscriber |
| Canonical drafts | `stage_edition`, `cancel_edition` | Publication publisher |
| Translation attempts | `submit_translation` | Publisher or exact locale editor |
| Semantic qualification | `review_translation` | Any caller; consensus decides |
| Exact locale adoption | `select_translation`, `approve_locale` | Snapshotted locale editor under unchanged configuration |
| Atomic release | `publish` | Publisher after all readiness guards |
| Adoption handoff | `acknowledge`, `withdraw_handoff` | Relevant subscriber |
| Immediate suspension | `freeze` | Publisher |
| Public semantic issues | `file_issue`, `review_issue` | Any caller; consensus decides review |
| Historical retirement | `retire` | Publisher after handoff guards |

Views: `get_protocol`, `get_publication`, `get_edition`, `get_translation`,
`get_issue`, `preview_publication`, `preview_handoff`, `get_live_manifest`.
Record views preserve historical text, attempts, reviews, approvals, manifests,
issue claims and subscriber actions. Preview methods explain barriers without
submitting another transaction.

## StudioNet edition register

| Record | Verified location |
| --- | --- |
| Principal contract | [0x17a056cC6f3Eec6e6914f1dB02e02852B1Ca4322](https://explorer-studio.genlayer.com/address/0x17a056cC6f3Eec6e6914f1dB02e02852B1Ca4322) |
| Principal deployment | [Transaction](https://explorer-studio.genlayer.com/tx/0x6ecccf57e3180e596546dad19cae834baad2bd99dbc0ce8a19c1b03bf2e7de55) |
| Controlled integration contract | [0x80Ca392FB9c81422d5362Be650cd7c3aC2EEF6AF](https://explorer-studio.genlayer.com/address/0x80Ca392FB9c81422d5362Be650cd7c3aC2EEF6AF) |
| Controlled deployment | [Transaction](https://explorer-studio.genlayer.com/tx/0x982ebfbda527fa0fa98635b316a412ceb89d4ba97d1ccd53398b835667de32f2) |
| RPC and chain | `https://studio.genlayer.com/api`, `61999` |
| Runtime surface | 16 nonpayable writes, 8 views |

The separate controlled contract ends with an intentionally frozen edition after
an upheld fixture issue. It is a complete lifecycle test deployment, not the
principal publication. No other chain is configured for execution. Public repository: [AbstrusImad/verbasync](https://github.com/AbstrusImad/verbasync).
The copy-ready title, description and active contract links are in
[SUBMISSION.md](SUBMISSION.md).

Verification: **59 local tests**, **one complete controlled GenVM integration**,
**four actual default-model semantic reviews** and **51 finalized contract writes**
(46 successful, five expected policy refusals). The main edition is available in
Spanish and French, with the original divergent Spanish attempt retained in history.
See [VERIFICATION.md](VERIFICATION.md) and [evidence/verification.json](evidence/verification.json).

## Deliberate operating bounds

- Canonical locales: lowercase two- or three-letter language codes, optionally
  a hyphen and uppercase two-letter region, such as `en`, `es`, `fr` or `pt-BR`.
  These syntax checks do not establish language support or certify BCP 47
  coverage. Script subtags and arbitrary locale variants are unsupported.
- One to eight distinct canonical segments per edition, 16–1,500 characters
  each; target segments use the same text bounds.
- Up to four target locales, three attempts per locale/segment, sixteen active
  subscribers and thirty-two historical editions per publication.
- Editor configuration changes invalidate every previously staged draft. They
  do not retroactively erase published approvals or freeze a released edition.
  Publish a replacement or explicitly freeze if an old editor is compromised.
- Parent publication and configuration revisions cannot be rebased in place.
  Cancel obsolete drafts and stage another edition.
- An isolated segment review does not detect every cross-segment contradiction,
  terminology inconsistency, formatting loss or accessibility defect. Publishers
  retain document-level editorial responsibility.

## Reproduce the desk

Python 3.13 was used for this implementation. Install the exact pinned packages:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Populate local values only. Never commit the resulting `.env`:

| Environment name | Purpose |
| --- | --- |
| `private_key_wallet` | StudioNet deployment/publication signer |
| `participant_private_key_1` | Independent editor test signer |
| `participant_private_key_2` | Subscriber/issue reporter test signer |

The supplied scripts deliberately require the selected main-account deployer
address. A fork must consciously adjust `EXPECTED_ACCOUNT` in `scripts/_studio.py`
to its own wallet. The script verifies the SDK chain ID, exact StudioNet RPC and
remote `eth_chainId` before any signature. It never auto-selects another network.

```powershell
genvm-lint download --version v0.3.0-rc6
python scripts/check_contracts.py
python scripts/check_contracts.py --typecheck
python -m pytest tests/direct -q --junitxml=test-results.xml
python -m pytest tests/integration -v -s --junitxml=integration-results.xml
python scripts/deploy_studionet.py
python scripts/exercise_default_llms.py
python scripts/export_verification.py
```

The linter helper selects a cached concrete SDK release instead of querying
GitHub's latest tag. The AST rules, SDK validation and type checking are not
modified. The contract pins the concrete runner
`py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.

The local suite exercises authorization, immutable revisions, locale vectors,
pending issue handling, freezes, successor adoption, bounded inputs, numeric
mismatch, malformed model output and independently captured validator decisions.
Direct mode cannot prove GenVM or distributed consensus compatibility. The
separate StudioNet integration test runs real GenVM storage, three real signers
and five explicitly controlled model validators. The main-deployment scenario
uses GenLayer's default models without mock responses or custom validators.
The two kinds of evidence are identified separately in [VERIFICATION.md](VERIFICATION.md).

Transaction scripts journal each returned hash before polling. They resume exact
method/argument/signer bindings and inspect execution results, not just accepted
status. Read-only transport failures use bounded retries. A signed send with an
ambiguous result is not blindly repeated. Only a finalized nonpayable semantic
review rollback explicitly marked `[LLM_ERROR]` may get up to two replacement
attempts. Five direct tests protect those recovery rules.

## Publisher and consumer responsibilities

The publisher owns source truth, editor selection, segment boundaries and release
intent. Models qualify supplied text; they cannot guarantee every linguistic,
technical or legal interpretation. There is no proof of editor expertise, real
organizational independence or subscriber deployment. Public on-chain text and
issue histories cannot be made confidential or deleted by this protocol.

Consumers own the final use decision. Bind reads to StudioNet chain 61999, the
correct contract and publication, read finalized state, verify `available`, and
inspect the exact manifest and history. Do not infer availability from an old
manifest hash or a previously observed editor approval. [MIT License](LICENSE).
