# Microsoft Store submission for Blacktable Studio by Brian

Use these entries for the Partner Center **Properties** page for the Windows 11 x64 EXE submission.

## Category and privacy

| Field | Entry |
| --- | --- |
| Primary category | Multimedia design |
| Subcategory | Music production |
| Secondary category | Music |
| Privacy policy | Select **Provide privacy policy text** and paste the [privacy policy](PRIVACY.md), including the title and contact information. |

Microsoft lists Music production under Multimedia design. Use Music as the primary category if the form does not present Multimedia design. [Microsoft category list](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/categories-and-subcategories)

## Support and contact details

| Field | Entry |
| --- | --- |
| Website | Optional. Leave blank until you have a public product page on your own website. |
| Support contact info | `https://github.com/brian513black-creator/Blacktable-steam-splitter-/issues` |
| Email address | An inbox monitored by the actual publisher for Microsoft Store correspondence. |
| Phone number | The actual publisher’s customer contact number, including country code if requested. |
| Address | The actual publisher’s contact address, including city, region, postal code, and country. |

Review Partner Center’s display and market requirements before entering publisher contact details. The support URL opens a public GitHub issue list. Customers need a GitHub account to file an issue. [Microsoft support fields](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/support-info)

## Product declarations

| Declaration | Selection |
| --- | --- |
| Non-Microsoft drivers or NT services | Leave unchecked. The local workspace and audio worker run as ordinary app processes. |
| Tested to meet accessibility guidelines | Leave unchecked until the complete Microsoft accessibility test checklist passes. |
| Pen and ink input | Leave unchecked. The app uses standard browser controls and has no pen or ink feature. |
| Generative AI | Leave unchecked for the current audio separator. Spleeter separates audio that the user supplies. The certification notes describe that AI processing so reviewers can see exactly what it does. |

[Microsoft product declarations and accessibility checklist](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/product-declarations)

## Notes for certification

Paste [the plain-text certification notes](STORE-CERTIFICATION-NOTES.txt). They are within Microsoft’s 2,000-character limit. [Microsoft certification notes guidance](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/product-declarations#notes-for-certification)

## System requirements

| Feature | Minimum hardware or software | Recommended |
| --- | --- | --- |
| Operating system | Windows 11 x64, build 22000 or later. The installer targets native Intel or AMD x64. | A current, supported Windows 11 x64 release. |
| Processor | x64 processor with AVX for TensorFlow AI separation. | Four or more logical cores with AVX. |
| Memory | Leave the optional minimum blank until tested on a lower-memory Windows PC. | 16 GB for full tracks and batches. |
| Storage | Allow 3 GB free for setup. The installed files take about 1.8 GiB. Temporary audio and exports need additional space. | 10 GB free for batches, with more for unusually long or large jobs. |
| Graphics | Leave dedicated GPU, video memory, and DirectX fields blank. Splitting uses the CPU. | No dedicated GPU requirement. |
| Browser | A current desktop browser set as the Windows default. | Current Microsoft Edge or Google Chrome. |

Enter processor and memory as supported by the form. Put the operating system, storage and browser details in the Store listing’s additional system requirements if no corresponding field is available here. The memory and storage figures are planning recommendations. [Microsoft system requirements fields](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/system-requirements) · [TensorFlow hardware requirements](https://www.tensorflow.org/install/pip#hardware_requirements)

## Packages page before submission

| Field | Entry |
| --- | --- |
| App type | EXE |
| Architecture | x64 |
| Language | English (United States), `en-US` |
| Installer parameters | `/S` |
| Package URL | The signed installer’s direct, versioned HTTPS download URL. Keep the file at that URL fixed after submission. |

Version 0.1.3 is an unsigned release candidate. Microsoft requires the EXE installer and its PE files to carry trusted code signatures. Complete publisher signing and test the signed package on Windows 11 before submitting its URL. A GitHub Actions artifact link requires access and expires. Host the signed installer at a direct HTTPS download URL that remains available to Microsoft’s certification testers and customers. [Microsoft package requirements](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/app-package-requirements) · [Microsoft package fields and installer parameters](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msi/upload-app-packages)
