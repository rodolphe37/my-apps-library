# Homebrew cask automation

`.github/workflows/release.yml`'s `update-homebrew-tap` job runs after every release: computes the new macOS zips' sha256, updates `Casks/my-apps-library.rb` in this repo (`packaging/homebrew/bump_cask.py`), and pushes the same file to the [`rodolphe37/homebrew-my-apps-library`](https://github.com/rodolphe37/homebrew-my-apps-library) tap.

The last part needs a token - the default `GITHUB_TOKEN` a workflow gets only has write access to the repo it's running in, not to the separate tap repo.

## One-time setup (not done yet)

1. [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) → **Fine-grained token**.
2. **Repository access** → Only select repositories → `rodolphe37/homebrew-my-apps-library`.
3. **Permissions** → Repository permissions → **Contents: Read and write** (nothing else needed).
4. Generate, copy the token.
5. In *this* repo (`my-apps-library`): **Settings → Secrets and variables → Actions → New repository secret** → name it `HOMEBREW_TAP_TOKEN`, paste the token.

Until this secret exists, the `update-homebrew-tap` job's last step logs a warning and exits cleanly (doesn't fail the release) - `Casks/my-apps-library.rb` in this repo still gets bumped correctly either way, it just doesn't reach the tap automatically until the token is set.

## Testing the bump script by hand

```bash
python3 packaging/homebrew/bump_cask.py \
  --version 0.6.0 \
  --arm-sha256 <64 hex chars> \
  --intel-sha256 <64 hex chars>
```

Fails loudly (non-zero exit) if it can't find exactly one match for each of `version`/`arm`/`intel` - a sign the Cask's formatting changed and the script's regexes need updating too.
