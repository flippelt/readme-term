# readme-term

Animated Homebrew-style terminal for a GitHub profile README. You fill in **`config.json`**, run one Python script (or let Actions do it), and drop the SVG into your profile.

<p align="center">
  <img src="assets/boot.svg" alt="Demo terminal boot" width="720"/>
</p>

The demo above is fake (`alex`). Replace it with you.

## Use it

1. Click **Use this template** → create a public repo (or clone this one).
2. Edit [`config.json`](config.json): `whoami`, boot lines, brew formulae, the TypeScript object at the end.
3. Enable **Actions** on the repo (Settings → Actions → allow).
4. Run `python3 generate.py` locally, or wait for the daily Action / hit **Run workflow**.
5. Point your profile README at the SVG:

```markdown
<p align="center">
  <img src="https://raw.githubusercontent.com/YOU/readme-term/main/assets/boot.svg" width="720" alt="Terminal"/>
</p>
```

If this *is* your `username/username` profile repo, a relative path is enough: `src="assets/boot.svg"`.

Python **3.10+**. No packages to install.

## What you can put in `config.json`

| Block | Purpose |
| --- | --- |
| `window` | Title in the traffic-light bar |
| `whoami` | Output of `$ whoami` |
| `boot` | `./boot.sh` steps (`key` / `value`) and the gold `ready` line |
| `brew.packages` | Formulae: `name`, `version`, optional `note` |
| `brew.keg_only` | Grey caveat under the beer summary (omit to hide) |
| `profile` | The `cat something.ts` object |

### Package extras

`version` can be a string (`"1.89.0"`) or a living semver:

- `{ "type": "age", "birthday": "1999-04-20" }` — years as `X.Y`, months since last birthday as `Z` (37 years 6 months → `3.7.6`)
- `{ "type": "anniversary", "month": 10, "day": 25, "version": "1.3.0", "as_of_year": 2025 }` — same monthly patch, `+0.1` on that date each year

`effect` (optional):

- `stall` — bar hangs at `stall_at` (default 87) then finishes
- `reverse` — hashes fill from the right
- `bursts` — fills in jumps

`ribbon: true` draws a small orange awareness bow instead of a text note.

Omit `boot`, `brew`, or `profile` entirely if you do not want that act.

## GitHub Action

`.github/workflows/generate.yml` runs every day at 00:00 UTC, on push to `main`, and from **Actions → Generate terminal SVG → Run workflow**. It rewrites `assets/boot.svg` and commits only when the file changed (`[skip ci]` so it cannot loop).

Age/anniversary versions therefore move by themselves.

## License

MIT. Live profile of the original: [github.com/flippelt](https://github.com/flippelt).
