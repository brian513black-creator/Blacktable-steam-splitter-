# Data handling

Blacktable Studio opens its workstation in your browser and serves it from a loopback address on your computer. It processes audio with the model bundled in the installer. The app does not send audio, stems, or usage analytics to an external service.

Source audio is staged in a temporary job directory. Blacktable removes the uploaded source and working WAV after successful processing. Stems and ZIPs stay in session storage until normal shutdown, so save your exports before closing the app. A forced shutdown may leave temporary files behind. Files you download remain at the destination selected by your browser.

The Windows launcher writes diagnostics to `%LOCALAPPDATA%\Blacktable Studio\blacktable.log`. Diagnostics may contain local file paths and error messages. Building the installer or preparing a development checkout downloads dependencies and the model from their upstream sources.
