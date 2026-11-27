# Blacktable Studio release record

## Version 0.1.3

The Windows 11 x64 candidate bundles the MIT-licensed Spleeter four-stem checkpoint and runs offline after installation. Use the release branch and its [Windows installer workflow](../.github/workflows/windows-installer.yml) to reproduce and verify the build. The [model provenance record](MODEL-PROVENANCE.md) identifies the exact model, license statement, and digests. The [third-party notices](../windows/Third-party%20notices.txt) ship in the installer.

The Windows smoke test checks installation, launch, protection against updating or uninstalling during an active session, a three-minute audio file through all three split modes, the 30-second preview, damaged input, upload replay, WAV range requests, ZIP contents, and clean uninstall. Each generated installer is accompanied by a SHA-256 file.

## Before commercial distribution

Use the publisher's Authenticode identity to sign the application, installer, and uninstaller. Calculate the published SHA-256 after signing. Validate the signed package on a clean Windows 11 x64 desktop and retain the installer hash and test run with the release record. Preserve the bundled third-party notices and license texts when distributing the package.

Publisher signing details and customer sales terms depend on the publisher and sales channel.
