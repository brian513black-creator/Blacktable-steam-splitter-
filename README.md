# Blacktable Studio by Brian

Blacktable is a local audio stem splitter targeting Windows 10 and 11 x64. Add a batch of audio files, split them one at a time in the background, audition each stem, and save individual WAV files or a ZIP per track.

## Start on Windows

1. Install 64-bit Python 3.12 with the Windows Python launcher enabled.
2. Install FFmpeg and ffprobe. With Windows Package Manager, run `winget install --id Gyan.FFmpeg --exact`. Open a new terminal and check `ffmpeg -version` and `ffprobe -version`.
3. Extract the project to a writable folder and double-click **Start-Blacktable.cmd**. The launcher installs the Python dependencies on first use and opens the local workstation in your default browser.
4. Select files, choose a separation mode, and click **Split audio**. Download the output before closing the launcher.

The first AI split downloads the official HTDemucs model into `.models`. Audio is processed on the device. Once the dependencies and model are present, splitting works offline. Each file can be up to 250 MiB. Files and outputs are temporary and the queue holds up to 100 jobs per session.

## Modes

| Mode | Outputs | Use |
| --- | --- | --- |
| Four stems | Vocals, drums, bass, other | Remixing and practice |
| Vocals + instrumental | Vocals and accompaniment | Karaoke and vocal sampling |
| Quick center + sides | Center and stereo sides | Fast stereo inspection. Center may include vocals, bass, kick, or any other centered sound. |

Use **First 30 seconds only** to audition a shorter split before processing a full track. CPU inference speed varies by machine and track. The two AI modes use the same separation model.

## Develop on Linux

With Python 3.12, FFmpeg, and ffprobe available, run `bash setup.sh` followed by `.venv/bin/python app.py`. Open the address printed by the server. Run `node --check web/app.js` for a JavaScript syntax check.

The interface bundles Instrument Serif under the [SIL Open Font License](web/instrument-serif-OFL.txt).

## Product comparison

[Demucs](https://github.com/adefossez/demucs) provides high-quality stem modes through a command-line workflow. [Ultimate Vocal Remover](https://github.com/Anjok07/ultimatevocalremovergui) adds a desktop interface with extensive model and ensemble controls. Blacktable uses Demucs under the hood and emphasizes a short workflow with one shared setting for a batch, a 30-second audition option, inline playback, and ZIP export on each job.

## Windows release status

This is a source build for development and validation. Before sale, validate on clean Windows x64 machines, measure CPU speed and separation quality with representative licensed tracks, and create and test a signed installer. Review third-party licenses and distribution terms for the actual bundled components and model weights, and include any required notices. The launcher downloads components from their upstream sources during setup. No customer installer or payment system is included.
