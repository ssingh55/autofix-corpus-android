# Autofix corpus: design

Status: approved 2026-09-23. Implementation plan: `autofix-corpus-plan.md`.
Companion to `autofix-test-inventory.md`, the 20 repos already tested.

## 1. Goal

Measure autofix against three things:

1. **Every Android static vulnerability that Sherlock detects.** There are 55 ids, from
   `sherlock/analyzers/android/static`, resolved through `mycroft/core/constants.py`.
2. **Very large single files**, where the fixer's tools have hard limits.
3. **Different app architectures**: project structure, native code and ABIs,
   cross-platform frameworks, and iOS.

A run succeeds when every planted id is detected in the baseline scan and every id gets
a scored outcome. The outcome can be a failure. A missed fix is useful data. A planted id
that never fires is a defect in the corpus.

## 2. Fixer limits this corpus is designed to expose

These were read from `appknox-go` `feat/autofix-cli-gate` @ 4f69cc6:

| Limit | Where | What the corpus expects |
|---|---|---|
| `read_file` truncates at 256 KB and has no offset or range | `agent/fsutil.go:12` | stress S1 and S3b are **missed** |
| `grep` returns `path:line` only, capped at 40 results | `agent/tools.go` | the fixer can't see text past the cap |
| `edit` needs an `old_string` that occurs exactly once | `agent/edit.go:55` | stress S2's duplicate lines test recovery from that rejection |
| `.dart`, `.plist` and `.rs` are not fixable source | `agent/fsutil.go:25` (`sourceSuffixes`) | Flutter, iOS plist and Rust findings are **missed** |
| Build files and signing are refused | `helper/verify_patch.go` (`buildFileRE`) | 104, 117, 11 and 95 are **declined as expected** |
| No new files are created | by design | 92 and 133 are **missed** today |

Fixing these limits is a separate change in appknox-go. The corpus has to show them failing first.

## 3. Sub-projects, in order

| SP | Scope | New repos or forks |
|---|---|---|
| **SP-5** | Purpose-built corpus: coverage and stress (sections 4–6) | 2 new repos |
| **SP-1** | Tag the existing forks by project structure. No new forks | none |
| **SP-2** | Native code and ABIs | tailscale-android (Go), deltachat-android (Rust), android/ndk-samples; allsafe-android is already forked |
| **SP-3** | Cross-platform frameworks: Flutter and React Native first, then KMP, Capacitor, MAUI | see section 8 |
| **SP-4** | iOS | separate pipeline on macOS runners |

**Unity is dropped.** Every CI build path needs a Unity account secret.

## 4. Repositories

Both repos are **public, under `ssingh55`**.

### 4.1 `ssingh55/autofix-corpus-android` (coverage)

```
app/src/main/AndroidManifest.xml
app/src/full/res/xml/{network_security_config,config}.xml
app/src/full/res/layout/*.xml
app/src/full/res/values/strings.xml
app/src/full/java/com/appknox/corpus/v<ID>/*.kt     # one package per vulnerability id
app/src/full/java/org/apache/cordova/FakeCordova.kt # PhoneGap detection, ids 29-33
app/src/full/java/redis/clients/jedis/Jedis.kt      # id 37
app/src/legacy/java/com/appknox/corpus/v{11,82,95}/ # legacy flavor
expected.yaml
tools/score.py, tools/test_score.py
.github/workflows/{build-check,corpus-run}.yaml
docs/design.md                                      # this spec
```

Two flavors, because some ids can't share an APK. (The flavor is named `full`, not `main`, because `main` is Gradle's shared source set.)

| Flavor | minSdk / targetSdk | Carries | Why it's separate |
|---|---|---|---|
| `full` | 24 / 34 | every id except 11, 95 and 82 | – |
| `legacy` | 16 / 16, no AndroidX, no `javax.crypto` | 11, 95, 82 | 11 requires min and target ≤16; 95 requires min <21; 82 is suppressed whenever crypto is used anywhere, and `full` carries 16 (`Cipher.getInstance`) |

Build: release variant, **unminified** (104 must fire), and signed **v1+v2** with the CI runner's
throwaway debug keystore (117 needs v1). Upload the **APK**: Sherlock re-signs an AAB with
bundletool, which would decide 117 instead of our signing.

Layout rules:
- Every construct lives under `com.appknox.corpus.*`. Ids 17, 88, 89 and 93 only look at
  the app package, and 127 ignores `androidx`, `kotlin` and `android` classes.
- Every construct is reachable from `MainActivity`.
- Each id gets its own exported component, so these conflicting pairs never share one:
  38 and 42, 39 and 43, 40 and 44, 41 and 45, 85, 128.
- id 10 uses `VIBRATE`, which is in androguard's permission map. CAMERA and
  RECORD_AUDIO are not in that map and would be ignored.

### 4.2 `ssingh55/autofix-corpus-stress`

The build matches `full`. Every file is produced by the seeded `tools/generate.py`.
`generate.py --check` fails CI if the committed output differs from a fresh run.

| Case | File | Size | Control (inside the cap) | Stress | Expected today |
|---|---|---|---|---|---|
| S1 | `HugeFile.kt` | ~17k lines, ~360 KB | `Random()` (127) at ~120 KB | `Log.d` (17) at ~330 KB | control fixed, stress **missed** |
| S2 | `GodActivity.kt` | ~6k lines, <256 KB | 17, 93, 127, 16 and 88 at 5%, 50% and 95% of the file | the same `Log.d("S2","user event")` line **3 times** | spread fixed; duplicates removed out of 3 is recorded |
| S3 | `AndroidManifest.xml` | ~500 components, ~39 KB | – | 39 at #482, 42 at #252 (indices chosen so each lands on a matching stub kind), everything else `exported=false` | both fixed, **0 unrelated lines changed** |
| S3b | `AndroidManifest.xml` in its own module | ~3,600 components, ~280 KB | – | 39 past 256 KB | **missed** |

Generated filler uses many small top-level functions. That keeps each method under the
JVM's 64 KB method limit, and shared strings keep the constant pool under 65,535 entries.

## 5. Coverage matrix (`expected.yaml`)

The trigger conditions come from the Sherlock analyzer code: the match logic in each
`static/*.py` file.

| Expected outcome | Ids | What is planted |
|---|---|---|
| `fix:code` | 5, 6, 7, 8, 9, 15, 16, 17, 46, 85, 86, 88, 89, 93, 94, 98, 127, 128 | empty `checkServerTrusted`; `HostnameVerifier { true }`; `SSLCertificateSocketFactory.getInsecure`; `AllowAllHostnameVerifier`; `onReceivedSslError` → `proceed()`; raw `Socket(host,80)`; `Cipher.getInstance("AES")`; `Log.d` with literal strings; `openFile` using `lastPathSegment`; an exported `PreferenceActivity`; `allowFileAccess=true` reachable from an exported activity; `registerReceiver`; implicit-Intent `startService`; `allowUniversalAccessFromFileURLs=true`; `setPluginState`; `Random()`; `getParcelableExtra` → `startActivity` |
| `fix:manifest` | 1, 2, 3, 10, 38–45, 84, 96, 118 | exported service with no intent-filter; `grant-uri-permission pathPrefix="/"`; `debuggable="true"`; unused VIBRATE permission; exported components with and without a normal-level permission; SEND intent-filter with the `file` scheme; `allowBackup` left unset; exported activity without `taskAffinity=""` |
| `fix:resource` | 113, 121, 122, 35, 36, 120 | NSC with `cleartextTrafficPermitted="true"` and `src="user"`; `<Button>` layout without `filterTouchesWhenObscured`; `inputType="textPersonName"`; `config.xml` with `loglevel=debug` and `<access origin="*">`; a fake `AKIA…` key in strings.xml and in code |
| `fix:add-code` | 83, 92, 133 | nothing planted: these are absence checks. 92 and 133 need new files, so they are **missed today** |
| `declined:build` | 104, 117, 11, 95 | unminified build, v1 signing, the SDK gates |
| `record-only` | 29–34, 37 | fake Cordova class plus `config.xml` (version defaults to "1"); a browsable activity plus a storage permission (34); a stub `redis.clients.jedis` class |
| `canary` | 4 | `<permission protectionLevel="normal">`. The analyzer compares against strings, but a compiled manifest likely stores an int. **UNVERIFIED**: if 4 never fires, that is a Sherlock false negative |
| `legacy` flavor | 11, 95, 82 | `addJavascriptInterface`; `ObjectInputStream`; contacts query with no crypto |

The planted secrets are fake values in AWS `AKIA…` format only. None use the `ghp_`/`github_pat_`,
`AIza` or `sk_live_` formats, because push protection would block the commit.

## 6. CI and scoring

- **`build-check.yaml`** runs on push and PR. It builds every flavor, runs
  `generate.py --check` (stress repo only) and runs `test_score.py`. It uses no secrets.
- **`corpus-run.yaml`** runs on `workflow_dispatch` only, because each run spends model budget.
  1. Build the release from the fixed `corpus-base` tag.
  2. Upload it to `autofix.staging.appknox.io` and wait for the static scan.
  3. **Detection gate:** every id in `expected.yaml` must be reported. Otherwise stop and list the gaps.
  4. Run `appknox autofix --file-id` from `feat/autofix-cli-gate`. It opens a PR into `corpus-run/<run-id>`.
  5. Build the PR head, rescan, then score.
- **`tools/score.py`** reads the before and after analyses, the PR diff and `expected.yaml`.
  - It assigns each id one outcome: `fixed-as-expected`, `declined-as-expected`, `missed`,
    `regression` or `detection-gap`.
  - Stress metrics: duplicates removed (out of 3), unrelated manifest lines changed, and
    whether the finding past the cap was reached.
  - It writes a markdown scorecard to the job summary and uploads `scorecard.json` as an artifact.
- Secrets: `APPKNOX_AUTOFIX_TOKEN`, plus the `id-token: write` permission for the
  Sherrinford OIDC exchange, as in the existing template.
- `main` is never modified. Every run branches from `corpus-base`.

## 7. SP-1: structure tags for the existing forks

Add these columns to the inventory: Kotlin/Java share, UI (XML/Compose/both), module
count, DSL, flavors, native code, framework. The values come from the survey on
2026-09-23. They already cover Java-only, Kotlin-only and mixed code; XML-only,
Compose-only and both; 2 to 269 modules; Groovy and KTS; and flavored and unflavored builds.

## 8. SP-2 to SP-4 candidates

These were verified on 2026-09-23 against upstream CI.

- **Native (SP-2):** tailscale/tailscale-android (Go gomobile, CI green 09-22);
  deltachat/deltachat-android (Rust, CI green 09-23; `.rs` gap); android/ndk-samples;
  t0thkr1s/allsafe-android (vulnerable, CMake); plus an ABI-split build of element-x (4 ABIs).
- **Flutter (SP-3):** Ostorlab insecure Flutter app (vulnerable; Flutter 3.7.12), sebsnyk/dvfa
  (vulnerable), OpenNutriTracker (CI green), localsend (Flutter plus Rust). `.dart` gap.
- **React Native (SP-3):** waseeq14/Damn-Vulnerable-React-Native (3 RN versions),
  Commando-X/vuln-bank-mobile, laurent22/joplin (CI green, unsigned assembleRelease).
- **KMP:** StreetComplete (already forked), JetBrains/kotlinconf-app, joreilly/PeopleInSpace.
- **Capacitor:** aeharding/voyager, ionic-team/ionic-conference-app. We write our own
  `cap sync` and `assembleDebug` steps.
- **MAUI:** dotnet/eShop (windows runner, CI green 09-21).
- **iOS (SP-4):** wikipedia-ios (SPM, simulator CI green); iGoat-Swift and DVIA-v2, which
  have no CI and old CocoaPods pins (UNVERIFIED on current Xcode).
  - **Open question:** does Appknox accept an unsigned IPA (`CODE_SIGNING_ALLOWED=NO`,
    zipped into `Payload/`)?

## 9. Out of scope

- Unity.
- Fixing the appknox-go limits in section 2.
- Classic Xamarin.
- WordPress-iOS, duckduckgo/apple-browsers and any runner that isn't a stock GitHub runner.

## 10. Risks

- **Legacy flavor.** AGP 8 at minSdk 16 must build with no AndroidX. If AGP refuses, 11
  and 95 move to `declined:build` and are recorded as not triggerable.
- **Lint blocks release builds.** Hardcoding `debuggable="true"` (id 3) fails release
  lint with `HardcodedDebugMode`, and targetSdk 16 raises lint errors too. The corpus
  sets `lint { disable += "HardcodedDebugMode"; abortOnError = false }`, and it is the
  only build-file deviation.
- **Id 4** may be undetectable. That is covered by the canary row.
- **Scan time.** Each corpus run is two uploads and two scans. KnoxIQ can take 15–120 minutes.
- **Throwaway signing key.** It's generated per run, so 117's severity depends on the
  signing schemes, not on the key.
