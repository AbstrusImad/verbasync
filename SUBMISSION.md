# GenLayer submission

## Title

VerbaSync ? Atomic Multilingual Publishing

## Description

VerbaSync is a contract-only multilingual publishing protocol on GenLayer StudioNet. GenLayer LLM consensus checks that translations preserve prohibitions, conditions, quantities and obligations. Editors approve exact locale versions before an entire edition publishes atomically. Subscribers acknowledge the immutable manifest; semantic issues can suspend or freeze releases, and replacements retain full history. Verified with 59 local tests, a complete controlled on-chain lifecycle and four real-model reviews that detected an inverted prohibition and qualified Spanish and French translations.

Description length: 598 characters (maximum 800).

## Links

- Repository: [AbstrusImad/verbasync](https://github.com/AbstrusImad/verbasync)
- Principal contract (StudioNet): [Explorer](https://explorer-studio.genlayer.com/address/0x17a056cC6f3Eec6e6914f1dB02e02852B1Ca4322)
- Controlled integration contract (StudioNet): [Explorer](https://explorer-studio.genlayer.com/address/0x80Ca392FB9c81422d5362Be650cd7c3aC2EEF6AF)

## Verification context

The principal contract used GenLayer's default models without model or validator mocks. Actual reviews rejected a Spanish instruction that inverted a prohibition, qualified the corrected Spanish and French translations, and dismissed a claim against the corrected text. The separate integration contract exercised the complete lifecycle with explicitly controlled five-validator model fixtures. Across both contracts, 51 writes finalized: 46 successes and five expected policy refusals. See [VERIFICATION.md](VERIFICATION.md) and [evidence/verification.json](evidence/verification.json).
