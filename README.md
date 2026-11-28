# Blacktable Studio by Brian

Blacktable is a local audio stem splitter for Windows 11 x64. Add a batch of audio files, split them one at a time in the background, audition each stem, and save individual WAV files or a ZIP per track.

## Install on Windows 11

1. Run **Blacktable-Studio-0.1.3-Windows-x64-Setup.exe**. Close any open copy of Blacktable before updating.
2. Open **Blacktable Studio** from Start. The installed `Blacktable Studio.exe` opens the workstation in your default browser.
3. Select your audio files, choose a separation mode, and click **Split full tracks**. Download the stems before closing the Blacktable window.

The installer bundles Python, FFmpeg, and Deezer's MIT-licensed Spleeter four-stem model. Audio processing runs offline on the device. If the AI engine reports a missing Windows library, install the latest [Microsoft Visual C++ Redistributable (x64)](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist) and retry. Diagnostics are in `%LOCALAPPDATA%\Blacktable Studio\blacktable.log`.

Each file can be up to 250 MiB. Files and outputs are temporary and the queue holds up to 100 jobs per session.

## Modes

| Mode | Outputs | Use |
| --- | --- | --- |
| Four stems | Vocals, drums, bass, other | Remixing and practice |
| Vocals + instrumental | Vocals and accompaniment | Karaoke and vocal sampling |
| Quick center + sides | Center and stereo sides | Fast stereo inspection. Center may include vocals, bass, kick, or any other centered sound. |

**Split full tracks** processes each song from start to finish by default. Turn on **30-second preview** to audition the start of a track. CPU inference speed varies by machine and track. Both AI modes use the same Spleeter checkpoint. Vocals + instrumental combines the drums, bass, and other estimates into one accompaniment WAV.

## Develop on Linux

With Python 3.12, FFmpeg, and ffprobe available, run `bash setup.sh` followed by `.venv/bin/python app.py`. Open the address printed by the server. Run `node --check web/app.js` for a JavaScript syntax check.

The interface bundles Instrument Serif under the [SIL Open Font License](web/instrument-serif-OFL.txt).

## Product comparison

[Demucs](https://github.com/adefossez/demucs) provides high-quality stem modes through a command-line workflow. [Ultimate Vocal Remover](https://github.com/Anjok07/ultimatevocalremovergui) adds a desktop interface with extensive model and ensemble controls. Blacktable uses Deezer's Spleeter model under the hood and emphasizes a short workflow with one shared setting for a batch, a 30-second audition option, inline playback, and ZIP export on each job.

## Build and verify a Windows installer

From the repository root, use Python 3.12 or 3.13, curl, and NSIS 3.11:

```text
python -m pip install ziglang==0.15.2
python windows/build.py
```

The build produces the setup executable and its SHA-256 checksum in `dist/`. Set `MAKENSIS` to the full compiler path if it is outside `PATH`. The Windows smoke test installs the package, launches the installed executable, verifies downloaded stems from all three modes, and uninstalls the program. Run it on a clean test account:

```text
python windows/smoke.py --installer dist/Blacktable-Studio-0.1.3-Windows-x64-Setup.exe --ai
```

The installer is an unsigned release candidate. The [release record](docs/RELEASE.md#before-commercial-distribution) lists the remaining work for a paid Microsoft Store launch, including trusted signing, hosting, the purchase flow, and a clean Windows 11 test. See the packaged [third-party notices](windows/Third-party%20notices.txt).

## Release paperwork

- [Model provenance and commercial license evidence](docs/MODEL-PROVENANCE.md)
- [Spleeter MIT notice](licenses/Spleeter-MIT.txt)
- [Third-party distribution notices](windows/Third-party%20notices.txt)
- [Privacy policy](docs/PRIVACY.md)
- [Build, validation, and signing record](docs/RELEASE.md)
- [Microsoft Store submission worksheet](docs/MICROSOFT-STORE.md)
