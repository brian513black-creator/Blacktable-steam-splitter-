# Blacktable Studio release record

## Version 0.1.3

The Windows 11 x64 candidate bundles the MIT-licensed Spleeter four-stem checkpoint and runs offline after installation. Use the release branch and its [Windows installer workflow](../.github/workflows/windows-installer.yml) to reproduce and verify the build. The [model provenance record](MODEL-PROVENANCE.md) identifies the exact model, license statement, and digests. The [third-party notices](../windows/Third-party%20notices.txt) ship in the installer.

The Windows smoke test checks installation, launch, protection against updating or uninstalling during an active session, a three-minute audio file through all three split modes, the 30-second preview, damaged input, upload replay, WAV range requests, ZIP contents, and clean uninstall. Each generated installer is accompanied by a SHA-256 file.

The 0.1.3 workflow cross-built the installer on Linux, verified the transferred checksum on its Windows runner, then passed the installed-app smoke test and uploaded the tested unsigned installer. [Passing Windows workflow](https://github.com/brian513black-creator/Blacktable-steam-splitter-/actions/runs/45951368825)

The separately cross-built workspace installer passed its archive and payload checks. Its copy of the Spleeter graph, index, and weight data matched the pinned hashes. Its installer SHA-256 is `f69d99d82d94fa1c4c18345d58dadb66a6fc460010eda616de89a8285e641e14`.

The [0.1.3 verification report](QA-0.1.3.md) records the expanded input-format, signal, browser, recovery, accessibility, and Store packaging checks.

## Before commercial distribution

The November 28, 2026 review found version 0.1.3 ready for internal testing. The paid Microsoft Store release remains blocked by the items below.

| Release gate | Status |
| --- | --- |
| Functional QA and model licensing | Windows CI passed and the local installer matched its checksum. The exact Deezer Spleeter weights and MIT notice matched the release record. The package includes the bundled dependency notices, including the FFmpeg LGPL notice and source links. |
| Trusted EXE signing | The installer and Blacktable launcher have empty embedded certificate tables. Across the installer and extracted payload, 167 of 201 PE files had empty embedded certificate tables. Embedded certificate data on the other files establishes presence only. Verify trusted signatures on all required PE files and the generated uninstaller on Windows. |
| Hosted package | The reviewed package is a local build and the GitHub repository has no public release asset. Supply a direct, versioned HTTPS URL for the signed EXE. |
| Paid purchase | The app has no checkout or purchase unlock. Microsoft's EXE/MSI pricing guide describes **Paid** as a one-time in-app purchase. Microsoft documents Store checkout and hosting with MSIX. Choose the package and commerce route before configuring the paid listing. |
| Clean Windows 11 acceptance | TensorFlow imports `MSVCP140.dll` and the installer has no copy under that name. The Windows CI runner passed with its existing runtime. Verify AI splits on a clean Windows 11 x64 desktop and resolve the Visual C++ runtime dependency for the final package. |
| Partner Center draft | The privacy policy, Properties worksheet, and certification notes are ready. The publisher still needs to confirm identity, pricing, complete listing fields and assets, and applicable customer license terms in Partner Center. Confirm the payout and tax profile if using Microsoft commerce. |

After signing, compute a fresh SHA-256 for the customer-facing installer and retain the clean-install evidence with the release record. Preserve the included license notices and corresponding-source access information for the bundled FFmpeg build. [Microsoft EXE/MSI package requirements](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/app-package-requirements) · [EXE/MSI pricing](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/set-app-pricing) · [Microsoft Store packaging and commerce](https://learn.microsoft.com/windows/apps/publish/faq/get-started-with-the-microsoft-store) · [TensorFlow Windows requirements](https://www.tensorflow.org/install/pip)

Use the [Partner Center worksheet](MICROSOFT-STORE.md) for the current EXE draft.
