# readme-term

Animated Homebrew-style terminal for a GitHub profile README. Fill in **`config.json`**, generate the SVG, drop it on your profile.

<p align="center">
  <img src="assets/boot.svg" alt="Demo terminal boot — replace the placeholders in config.json" width="720"/>
</p>

The preview is generic on purpose (`your_handle`, `your city`, birthday `2000-01-01`). Swap every example value for yours.

## Setup

1. Click **Use this template** and create a **public** repo.
2. Edit [`config.json`](config.json) — at least `window`, `whoami`, `profile`, and (if you want a package manager) `install`.
3. For a living `human` version, set `brew.packages[].version.birthday` to a real `YYYY-MM-DD`.
4. Enable the daily Action (see **Cron** below) or run locally:

```
python3 generate.py
```

Python **3.10+**. No packages to install.

5. Put this in your profile README (`username/username`):

```
<p align="center">
  <img src="https://raw.githubusercontent.com/YOU/readme-term/main/assets/boot.svg" width="720" alt="Terminal"/>
</p>
```

If `readme-term` *is* the profile repo, use `src="assets/boot.svg"`.

## Variants

`config.json` is macOS + Homebrew + boot. Copy another file on top of it if you want a different shell:

```
cp examples/no-install.json config.json
python3 generate.py
```

| File | What you get |
| --- | --- |
| [`config.json`](config.json) | `$ brew install` + `./boot.sh` (default) |
| [`examples/no-install.json`](examples/no-install.json) | no package manager — boot then `cat` |
| [`examples/no-boot.json`](examples/no-boot.json) | brew, no `./boot.sh` |
| [`examples/linux-apt.json`](examples/linux-apt.json) | `$ sudo apt install` |
| [`examples/windows-winget.json`](examples/windows-winget.json) | `PS> winget install` + `Get-Content` |
| [`examples/npm.json`](examples/npm.json) | `$ npm install -g` |
| [`examples/pip.json`](examples/pip.json) | `$ pip install` |
| [`examples/uv.json`](examples/uv.json) | `$ uv pip install` |
| [`examples/cargo.json`](examples/cargo.json) | `$ cargo install` |
| [`examples/nix.json`](examples/nix.json) | `$ nix profile install` |
| [`examples/mise.json`](examples/mise.json) | `$ mise use --global` |
| [`examples/asdf.json`](examples/asdf.json) | `$ asdf install` |

<p align="center">
  <img src="assets/no-install.svg" alt="No package manager" width="720"/>
</p>

<p align="center">
  <img src="assets/no-boot.svg" alt="No boot.sh" width="720"/>
</p>

<p align="center">
  <img src="assets/linux-apt.svg" alt="Linux apt terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/windows-winget.svg" alt="PowerShell winget terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/npm.svg" alt="npm terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/pip.svg" alt="pip terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/uv.svg" alt="uv terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/cargo.svg" alt="cargo terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/nix.svg" alt="nix terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/mise.svg" alt="mise terminal" width="720"/>
</p>

<p align="center">
  <img src="assets/asdf.svg" alt="asdf terminal" width="720"/>
</p>

`install.kind` can be `brew`, `apt`, `winget`, `npm`, `pip`, `uv`, `cargo`, `nix`, `mise`, `asdf`, or `none`. Omit the `boot` object to skip `./boot.sh`. Set `"shell": "powershell"` for `PS>` and `$env:USERNAME`.

## Cron (GitHub Actions)

The workflow [`.github/workflows/generate.yml`](.github/workflows/generate.yml) redraws `assets/boot.svg` and commits it when something changed (age/month versions, or you edited `config.json`).

GitHub **does not run scheduled workflows on a brand-new template copy** until Actions are allowed.

1. Repo **Settings → Actions → General**.
2. Under *Actions permissions*, allow Actions (default: *Allow all actions and reusable workflows*).
3. Under *Workflow permissions*, **Read and write** — the job must push `assets/boot.svg`.
4. Open the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.
5. **Generate terminal SVG → Run workflow** once, so you know the token and permissions work.
6. Leave the `schedule` in place. Default:

```
0 0 * * *
```

That is **00:00 UTC every day**. GitHub can delay a scheduled job by minutes or hours. It will not fire if Actions stay disabled.

### Change the time

Edit the `cron:` line in `.github/workflows/generate.yml`. GitHub cron is always UTC.

| When | cron |
| --- | --- |
| Every day at 00:00 UTC | `0 0 * * *` |
| Every day at 03:00 São Paulo (UTC−3) | `0 6 * * *` |
| First day of each month, 00:00 UTC | `0 0 1 * *` |
| Only by hand (no schedule) | delete the `schedule:` block, keep `workflow_dispatch` |

Daily is the right default if you use `type: age` or `type: anniversary` versions (the patch is months since a birthday). A monthly cron still works; the SVG just updates later.

### Turn it off

Delete `.github/workflows/generate.yml` and generate only on your machine with `python3 generate.py`.

## `config.json`

| Block | What to change |
| --- | --- |
| `window` | Title in the traffic-light bar (`you@github ~ /profile`) |
| `whoami` | Output of `$ whoami` |
| `boot` | `./boot.sh` steps (`key` / `value`) and the gold `ready` line |
| `install.kind` | `brew`, `apt`, `winget`, `npm`, `pip`, `uv`, `cargo`, `nix`, `mise`, `asdf`, or `none` |
| `install.packages` | Formulae: `name`, `version`, optional `note` |
| `install.keg_only` | Grey footnote under the summary (omit the key to hide it) |
| `shell` | `unix` (default) or `powershell` |
| `profile` | The `cat you.ts` object |

### Package extras

`version` is either a pin (`"1.0.0"`) or a living semver:

- `{ "type": "age", "birthday": "2000-01-01" }` — years as `X.Y`, months since last birthday as `Z` (replace the date)
- `{ "type": "anniversary", "month": 10, "day": 25, "version": "1.0.0", "as_of_year": 2025 }` — same monthly patch, `+0.1` on that date each year

`effect` (optional): `stall` (hangs at `stall_at`, default 87), `reverse` (fill from the right), `bursts` (jumps).

`ribbon: true` draws a small orange awareness bow instead of a text note.

Omit `boot`, `install`, or `profile` if you do not want that act. (`brew` still works as an alias of `install`.)

## License

MIT. Original profile: [github.com/flippelt](https://github.com/flippelt).
