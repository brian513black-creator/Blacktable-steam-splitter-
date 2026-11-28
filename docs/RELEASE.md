# Blacktable Studio release record

## Version 0.1.3

The Windows 11 x64 candidate bundles the MIT-licensed Spleeter four-stem checkpoint and runs offline after installation. Use the release branch and its [Windows installer workflow](../.github/workflows/windows-installer.yml) to reproduce and verify the build. The [model provenance record](MODEL-PROVENANCE.md) identifies the exact model, license statement, and digests. The [third-party notices](../windows/Third-party%20notices.txt) ship in the installer.

The Windows smoke test checks installation, launch, protection against updating or uninstalling during an active session, a three-minute audio file through all three split modes, the 30-second preview, damaged input, upload replay, WAV range requests, ZIP contents, and clean uninstall. Each generated installer is accompanied by a SHA-256 file.

The 0.1.3 workflow cross-built the installer on Linux, verified the transferred checksum on its Windows runner, then passed the installed-app smoke test and uploaded the tested unsigned installer. [Passing Windows workflow](https://github.com/brian513black-creator/Blacktable-steam-splitter-/actions/runs/45951368825)

The separately cross-built workspace installer passed its archive and payload checks. Its copy of the Spleeter graph, index, and weight data matched the pinned hashes. Its installer SHA-256 is `f69d99d82d94fa1c4c18345d58dadb66a6fc460010eda616de89a8285e641e14`.

## Before commercial distribution

Use the publisher's Authenticode identity to sign the application, installer, and uninstaller. Calculate the published SHA-256 after signing. Validate the signed package on a clean Windows 11 x64 desktop and retain the installer hash and test run with the release record. Preserve the bundled third-party notices and license texts when distributing the package.

Publisher signing details and customer sales terms depend on the publisher and sales channel.

For a Microsoft Store EXE submission, complete the [Partner Center worksheet](MICROSOFT-STORE.md), then provide a direct versioned HTTPS URL to the signed package.
