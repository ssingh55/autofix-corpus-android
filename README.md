# autofix-corpus-android

A test corpus for the Appknox autofix CLI. Every vulnerability in this app is planted on
purpose. `expected.yaml` lists each planted Sherlock id and what the fixer should do with it.
Do not harden the plants.

- `build-check` runs on every push. It runs the scorer tests, builds both flavors and asserts
  that the plant-bearing files are in the APK.
- `corpus-run` is dispatch-only because every run spends model budget. It scans `baseRef`,
  runs `appknox autofix` for both flavors onto one PR, rescans that PR's head and writes a
  scorecard.

## Cleanup after a corpus run

Nothing is cleaned up automatically. After you have read the scorecard, remove these by hand
(`<id>` is the workflow run id):

- close the autofix PR (base `corpus-run/<id>`, head `appknox-autofix/autofix-<id>`);
- delete the branch `corpus-run/<id>`;
- delete the branch `appknox-autofix/autofix-<id>`.

```sh
gh pr close --delete-branch appknox-autofix/autofix-<id> -R ssingh55/autofix-corpus-android
git push origin --delete corpus-run/<id>
```
