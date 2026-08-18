# Homebrew Cask for MyAppsLibrary - a one-command install with a proper
# /Applications entry, Launchpad/Spotlight icon, and `brew upgrade`/
# `uninstall` lifecycle, in place of the manual git-clone-from-source path.
#
# NOT a Gatekeeper bypass, despite an earlier assumption to the contrary:
# tested for real, Homebrew Cask deliberately re-applies
# com.apple.quarantine to every app it installs (a security policy in
# Homebrew's own source, cask/quarantine.rb - not overridable via
# --no-quarantine/HOMEBREW_CASK_OPTS, both tried: `xattr` still shows the
# flag present after install either way). That flag, not code-signing
# status alone, is what makes Finder/`open` actually show the Gatekeeper
# warning on first launch (`spctl -a` evaluates the code signature
# unconditionally and reports "rejected" regardless of quarantine, so it
# isn't the right thing to test here - the quarantine attribute itself,
# and a real `open`, are). Since the app stays unsigned/unnotarized (see
# README.md's Roadmap on why), a one-time right-click → Open (or
# `xattr -cr /Applications/MyAppsLibrary.app`) is still needed
# on first launch, exactly as it would be for a plain zip download - this
# Cask is about install/update convenience, not about removing that step.
#
# NOTE: this file lives here so it's versioned alongside the app it
# describes, but `brew install --cask my-apps-library` (bare name) needs
# a Homebrew tap - a separate GitHub repo named `homebrew-<something>`.
# That tap is live: github.com/rodolphe37/homebrew-my-apps-library -
# `brew tap rodolphe37/my-apps-library && brew install --cask
# my-apps-library` works today, verified for real against the actual
# public repo (not just a local test tap).
#
# `version`/`sha256` are kept in sync with the tap automatically -
# .github/workflows/release.yml's update-homebrew-tap job bumps both
# this file and the tap's copy after every release (see
# packaging/homebrew/bump_cask.py and packaging/homebrew/README.md for
# the one remaining manual step, a repo secret it needs).
cask "my-apps-library" do
  arch arm: "ARM64", intel: "X64"

  version "0.14.1"
  sha256 arm:   "f01d6ed8346614e38f59474b58d81457d985f1db7460c5fc31abde77882f82c0",
         intel: "6a401db8b9a29553fbc9f80cf2e7393d7a6919ed5b6201db9712402c1db2c25b"

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
    "~/Library/Caches/MyAppsLibrary",
    "~/Library/Preferences/com.myappslibrary.*.plist",
  ]
end
