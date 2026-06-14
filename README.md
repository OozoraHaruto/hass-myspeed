# MySpeed for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

A custom integration that connects Home Assistant to one or more
[MySpeed](https://github.com/gnmyt/MySpeed) instances (the self-hosted
speed-test analysis app) and exposes their data as entities.

## Multiple instances

Add the integration once **per** MySpeed instance. Each instance becomes its own
device with its own set of entities, so you can monitor several connections
(e.g. different sites, ISPs, or remote nodes) side by side.

## Entities (per instance)

| Platform | Entity | Notes |
|---|---|---|
| Sensor | Download | Mbps, from the latest successful test |
| Sensor | Upload | Mbps |
| Sensor | Ping | ms |
| Sensor | Jitter | ms |
| Sensor | Test duration | seconds (diagnostic) |
| Sensor | Last test | timestamp of the most recent result |
| Sensor | Server | the test server name (diagnostic) |
| Sensor | Test type | `auto` or `custom` (diagnostic) |
| Binary sensor | Test running | a test is currently executing |
| Binary sensor | Paused | the scheduler is paused (diagnostic) |
| Binary sensor | Last test failed | the most recent result has an error |
| Switch | Pause tests | pause indefinitely / resume |
| Button | Run speed test | triggers a manual (custom) test |
| Update | Version | installed vs. latest GitHub release (informational) |

Speed/ping/jitter sensors read from the most recent **successful** test, so a
single failed run won't wipe their values; the *Last test failed* binary sensor
and *Last test* timestamp always reflect the newest result.

## Installation via HACS (custom repository)

1. In Home Assistant, open **HACS**.
2. Top-right **⋮ menu → Custom repositories**.
3. Paste this repository's URL, choose category **Integration**, and click **Add**.
4. Search for **MySpeed** in HACS, open it, and click **Download**.
5. **Restart Home Assistant.**

> Once this repo is accepted into the HACS default store, steps 2–3 are no longer
> needed — users can just search for it.

### Manual installation (without HACS)

Copy `custom_components/myspeed` into your Home Assistant
`config/custom_components/` directory and restart.

## Configuration

1. **Settings → Devices & Services → Add Integration → MySpeed**.
2. Enter the URL, e.g. `http://192.168.1.50:5216` (the scheme and the default
   port `5216` are added automatically if omitted).
3. Enter the password **only** if your instance is password-protected.
4. Repeat for any additional instances.

The poll interval (default 300 s) can be changed under the integration's
**Configure** (options) menu.

## How it talks to MySpeed

The integration uses MySpeed's local REST API:

- `GET /api/speedtests?limit=N` — recent results
- `GET /api/speedtests/status` — `{paused, running}`
- `GET /api/info/version` — `{local, remote}`
- `POST /api/speedtests/run` — start a manual test
- `POST /api/speedtests/pause` / `/continue` — pause or resume

Authentication, when enabled, is the plaintext password sent in the `password`
request header (matching MySpeed's own clients). All traffic stays on your local
network — the integration's IoT class is `local_polling`.

---

## Maintainer setup (before you publish)

This repo is HACS-ready, but a few values are placeholders you must replace with
your own GitHub details so it passes validation:

1. **`custom_components/myspeed/manifest.json`** — replace `@YOUR_GITHUB_USERNAME`
   in `codeowners` and the `YOUR_GITHUB_USERNAME/...` paths in `documentation`
   and `issue_tracker` with your real handle / repo URL.
2. **`LICENSE`** — set your name (or change the license entirely).
3. **GitHub repository settings** — give the repo a **description** and at least
   one **topic** (HACS requires both).
4. **Create a GitHub release** (a real release, not just a tag), e.g. `v1.0.0`,
   matching the `version` in `manifest.json`. HACS uses releases for versioning.
5. **Brand assets (optional but recommended).** To get a proper icon/logo instead
   of the default placeholder and silence Home Assistant's "logo not found"
   warning, submit `icon.png` (256×256) and `logo.png` to
   [home-assistant/brands](https://github.com/home-assistant/brands) under
   `custom_integrations/myspeed/`. Not required to install as a custom repo.

### Validation

The included workflow at `.github/workflows/validate.yml` runs the **HACS Action**
and **hassfest** — the same checks HACS itself uses — on every push and daily.
A green run means the repository structure, `hacs.json`, and `manifest.json` are
valid.

### Submitting to the HACS default store (optional)

After the validation workflow passes and you've published a release, follow
[the HACS default-inclusion guide](https://www.hacs.xyz/docs/publish/include/)
to open a PR against `hacs/default`. Brand assets in `home-assistant/brands` are
required for default inclusion.

## Disclaimer

Community project; not affiliated with the MySpeed author. MySpeed is MIT-licensed.
