# Detection log

Detection gaps the corpus-run gate reported, how each was triaged, and the scorecards of each
green run. Buckets (spec §5): **plant wrong** (fix the plant), **Sherlock can't detect**
(`outcome: canary`), **SDK/AGP limit** (`outcome: record-only`).

## Gaps

### id 92 (FLAG_SECURE absence), full, run 35947935448

- **Symptom:** `detection gaps (full): [92]` after androidx.core was added to the full flavor.
- **Cause:** `sherlock/analyzers/android/static/flagsecure.py` reports 92 only when *no*
  `Window.setFlags`/`addFlags` call carrying 0x2000 exists anywhere in the APK, library code
  included. androidx.core ships such calls, so bundling it silenced the absence check.
- **Why androidx.core is there:** autofix's id-88 fix calls
  `androidx.core.content.ContextCompat.registerReceiver`; without the dependency the fix branch
  does not compile (run 35937725757, `DynamicReceiver.kt: Unresolved reference 'core'`).
- **Bucket:** none of the three — a build-config interaction, not a plant or analyzer defect.
  Fixed by `"fullCompileOnly"("androidx.core:core-ktx:1.13.1")` (c3004e5): the fix compiles,
  androidx stays out of the APK (0 `Landroidx/core/` dex references on the base full APK), 92
  fires again. Safe because the corpus is static-only and the APK is never executed.
- **Note for Sherlock:** real apps almost always bundle androidx.core, so 92 is likely a false
  negative on most production apps (library FLAG_SECURE calls mask the app's own omission).

No other gaps: the full gate passed on run 35902146570 (the first to reach it), and both
flavors passed on run 35951819778.

## Pipeline failures that were not detection gaps

| run | failure | fix |
|---|---|---|
| 35902146570 | `bad file id` on the 2nd upload | appknox-go 4f69cc6 leaves `~/.config/appknox.json` empty and then prints a warning on **stdout**; workflow seeds `{}` (c805edd). Fixed upstream on appknox-go `develop` 8351c46, not yet on `feat/autofix-cli-gate` |
| 35937725757 | fix branch did not compile; Score step aborted | androidx.core added (f79e20e, then compileOnly c3004e5); `grep -c` zero-count exit under `bash -e` (2113712) |
| 35947935448 | `detection gaps (full): [92]` | see id 92 above |

## Run 35951819778 (corpus c3004e5, appknox-go 4f69cc6)

#### Autofix corpus scorecard (full)

- appknox-go: 4f69cc604e6a7403e113f192455a7dfb409b1728
- corpus base: c3004e5c5130e8c4b403303d71dcbddcf1044fbf
- fix branch head: feca2bb5e7fb5d5a6514342a2ff387bb1e6df53d
- file ids: before 75, after 78
- findings skipped by autofix: full 0, legacy 0

| id | expected | result |
|---|---|---|
| 1 | fix:manifest | fixed-as-expected |
| 2 | fix:manifest | missed |
| 3 | fix:manifest | fixed-as-expected |
| 4 | canary | recorded-cleared |
| 10 | fix:manifest | fixed-as-expected |
| 34 | record-only | recorded-present |
| 38 | fix:manifest | fixed-as-expected |
| 39 | fix:manifest | fixed-as-expected |
| 40 | fix:manifest | fixed-as-expected |
| 41 | fix:manifest | blocked-by-shared |
| 42 | fix:manifest | fixed-as-expected |
| 43 | fix:manifest | fixed-as-expected |
| 44 | fix:manifest | fixed-as-expected |
| 45 | fix:manifest | fixed-as-expected |
| 84 | fix:manifest | missed |
| 96 | fix:manifest | fixed-as-expected |
| 118 | fix:manifest | blocked-by-shared |
| 5 | fix:code | fixed-as-expected |
| 6 | fix:code | fixed-as-expected |
| 7 | fix:code | fixed-as-expected |
| 8 | fix:code | fixed-as-expected |
| 9 | fix:code | fixed-as-expected |
| 15 | fix:code | missed |
| 83 | fix:add-code | fixed-as-expected |
| 113 | fix:resource | fixed-as-expected |
| 46 | fix:code | missed |
| 85 | fix:code | fixed-as-expected |
| 86 | canary | recorded-cleared |
| 88 | fix:code | fixed-as-expected |
| 89 | fix:code | fixed-as-expected |
| 94 | fix:code | fixed-as-expected |
| 98 | fix:code | missed |
| 128 | fix:code | fixed-as-expected |
| 16 | fix:code | fixed-as-expected |
| 17 | fix:code | missed |
| 29 | record-only | recorded-present |
| 30 | record-only | recorded-present |
| 31 | record-only | recorded-present |
| 32 | record-only | recorded-present |
| 33 | record-only | recorded-present |
| 35 | fix:resource | missed |
| 36 | fix:resource | missed |
| 37 | record-only | recorded-present |
| 92 | fix:add-code | missed-known-gap |
| 93 | fix:code | missed |
| 104 | declined:build | declined-as-expected |
| 117 | declined:build | declined-as-expected |
| 120 | fix:resource | missed |
| 121 | fix:resource | missed |
| 122 | fix:resource | fixed-as-expected |
| 127 | fix:code | fixed-as-expected |
| 133 | fix:add-code | missed-known-gap |

Regressions (new ids after the fix): none

#### Autofix corpus scorecard (legacy)

- appknox-go: 4f69cc604e6a7403e113f192455a7dfb409b1728
- corpus base: c3004e5c5130e8c4b403303d71dcbddcf1044fbf
- fix branch head: feca2bb5e7fb5d5a6514342a2ff387bb1e6df53d
- file ids: before 76, after 79
- findings skipped by autofix: full 0, legacy 0

| id | expected | result |
|---|---|---|
| 11 | declined:build | declined-as-expected |
| 82 | canary | recorded-cleared |
| 95 | declined:build | declined-as-expected |

Regressions (new ids after the fix): none
