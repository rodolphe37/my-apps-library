# winget manifest — not published yet

The `manifests/` folder here is laid out exactly as `microsoft/winget-pkgs` (the community repo Windows Package Manager pulls from) expects — `manifests/<first-letter>/<publisher>/<package>/<version>/*.yaml` — specifically so it can be copied straight into a PR against that repo with no restructuring.

**Not submitted yet.** Publishing means opening a PR against [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs) with this `manifests/` subtree — a manual, one-time step (their automated + human validation pipeline isn't something this repo's CI can drive). Until that PR is merged, `winget install rodolphe37.MyAppsLibrary` won't resolve for anyone.

Could not be validated locally either — `winget validate` needs Windows, unavailable in the environment these manifests were written in. Written correctly against the documented schema (1.6.0) and this project's actual release artifact shape (a zip containing a portable `.exe`, not an MSI — see the installer manifest's comment), but genuinely unverified beyond that.

Bump `PackageVersion` (new version folder + `InstallerSha256`) on every release. Not automated yet.
