# Blacktable Studio 0.1.3 verification

The November 28, 2026 review covered the Blacktable desktop launcher, browser workspace, bundled Spleeter engine, and Windows installer. The Windows workflow tested its cross-built installer on a Windows Server 2025 runner. Local regression checks used the application and checkpoint extracted from the separately cross-built workspace installer. [Completed Windows run](https://github.com/brian513black-creator/Blacktable-steam-splitter-/actions/runs/45951368825)

| Check | Result |
| --- | --- |
| Installer integrity | The workspace installer matched its SHA-256 file and passed the archive integrity test. Ten extracted application, web, and license files matched the Git checkout. The Spleeter graph, index, and weight shard matched their pinned hashes. |
| Windows installation | Silent setup and first launch passed. Setup and uninstall refused to change the installation during an active session. Uninstall passed after the app stopped. |
| Full tracks and previews | Each mode produced exact-duration WAV and ZIP exports for a 180-second input and its 30-second preview. Playback byte ranges and archive contents passed. |
| Signal and window boundaries | A 72-second speech and instrument fixture retained its final samples. The vocals WAV was identical in both AI modes. Their accompaniment comparison differed by at most one 16-bit PCM count. The summed chunked output differed from the same Spleeter graph run without chunking by about −66.6 dB relative RMS. The largest original-graph reconstruction transient on this fixture occurred in the first 43 milliseconds. |
| Input formats | WAV, AIFF, FLAC, MP3, M4A, raw AAC, Ogg Opus, WebM Opus, WMA, AC-3, and Wave64 produced 44.1 kHz stereo PCM WAVs in Quick mode. The sweep included 24-bit mono and stereo inputs. |
| Recovery | Empty and truncated inputs were rejected. A deliberately damaged copy of the model produced a readable error and Quick mode accepted the next job. Upload replay reused the original job. Silent single-frame and one-second inputs retained their lengths and silence. ZIP CRC checks and bounded WAV range checks passed. |
| Browser | Keyboard focus and activation, mixed batch drag and drop, playback, and Unicode ZIP filenames passed. Compact layouts fit 320 px. A disconnect disabled stale controls and reconnecting restored them. The observed page requests used the loopback address. |

## Accessibility

The Chromium checks covered keyboard navigation and emulated forced colors. Axe reported zero automatic violations in the regular theme and left contrast items for manual review. In light forced colors, Axe reported the authored gold and cream values for several nodes. Chromium's computed styles and the captured screen showed black text on white for the inspected controls. Windows Narrator, Contrast Themes, and other manual Microsoft accessibility checks remain open. Keep the Store accessibility declaration unchecked until those checks are complete. [Microsoft accessibility declaration guidance](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/product-declarations)

## Store packaging

The installer and launcher PE headers had empty Authenticode certificate tables. The Store build needs publisher signing, a stable direct HTTPS package URL, and a signed-install check on a clean Windows 11 x64 PC. [Microsoft package requirements](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/app-package-requirements)
