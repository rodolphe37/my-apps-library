# Homebrew Cask for MyAppsLibrary — a one-command install with a proper
# /Applications entry, Launchpad/Spotlight icon, and `brew upgrade`/
# `uninstall` lifecycle, in place of the manual git-clone-from-source path.
#
# NOT a Gatekeeper bypass, despite an earlier assumption to the contrary:
# tested for real, Homebrew Cask deliberately re-applies
# com.apple.quarantine to every app it installs (a security policy in
# Homebrew's own source, cask/quarantine.rb — not overridable via
# --no-quarantine/HOMEBREW_CASK_OPTS, both tried: `xattr` still shows the
# flag present after install either way). That flag, not code-signing
# status alone, is what makes Finder/`open` actually show the Gatekeeper
# warning on first launch (`spctl -a` evaluates the code signature
# unconditionally and reports "rejected" regardless of quarantine, so it
# isn't the right thing to test here — the quarantine attribute itself,
# and a real `open`, are). Since the app stays unsigned/unnotarized (see
# README.md's Roadmap on why), a one-time right-click → Open (or
# `xattr -cr /Applications/MyAppsLibrary.app`) is still needed
# on first launch, exactly as it would be for a plain zip download — this
# Cask is about install/update convenience, not about removing that step.
#
# NOTE: this file lives here so it's versioned alongside the app it
# describes, but `brew install --cask my-apps-library` (bare name) only
# works once it's copied into a Homebrew tap — a separate GitHub repo
# named `homebrew-<something>` (e.g. rodolphe37/homebrew-my-apps-library).
# Modern Homebrew refuses to install a cask from a bare local file path
# (confirmed: `brew install --cask ./Casks/my-apps-library.rb` errors
# with "Homebrew requires casks to be in a tap") — verifying this formula
# locally requires a local test tap (`brew tap-new`, no GitHub involved).
# See README.md's Installation section for the current state of tap
# publishing (a manual, one-time step not done yet).
#
# Bump `version`/`sha256` on every release — both macOS zips' checksums
# change every time release.yml runs. Not yet automated (a
# `brew bump-cask-pr`-style CI step would be the natural follow-up).
cask "my-apps-library" do
  arch arm: "ARM64", intel: "X64"

  version "0.5.2"
  sha256 arm:   "4540100fbd2520a189e2b31f4c32c55d618af80d5c4c3b0634ad9fd8e1e63c03",
         intel: "00952e792d4d4050ff270dea8a41ce1f45a654877605f7a3f3222981587f655b"

  url "https://github.com/rodolphe37/my-apps-library/releases/download/v#{version}/MyAppsLibrary-macOS-#{arch}.zip",
      verified: "github.com/rodolphe37/my-apps-library/"
  name "MyAppsLibrary"
  desc "Plugin-extensible launcher for organizing and opening your coding projects"
  homepage "https://github.com/rodolphe37/my-apps-library"

  auto_updates false
  depends_on macos: :big_sur

  app "MyAppsLibrary.app"

  zap trash: [
    "~/Library/Application Support/MyAppsLibrary",
    "~/Library/Preferences/com.myappslibrary.*.plist",
    "~/Library/Caches/MyAppsLibrary",
  ]
end
