# Spleeter model provenance

Blacktable Studio 0.1.3 uses Deezer Research's original four-stem Spleeter inference checkpoint. The Windows installer includes the graph, index, and data shard from the official v1.4.0 release. Blacktable verifies the archive and each bundled component against pinned SHA-256 digests. [Official release](https://github.com/deezer/spleeter/releases/tag/v1.4.0) · [Pinned digests and inference entry point](../spleeter_engine.py)

| Item | Value |
| --- | --- |
| Publisher | Deezer SA |
| Release asset | `v1.4.0/4stems.tar.gz` |
| Archive SHA-256 | `3adb4a50ad4eb18c7c4d65fcf4cf2367a07d48408a5eb7d03cd20067429dfaa8` |
| License | MIT |
| Copyright and license text | [Spleeter MIT notice](../licenses/Spleeter-MIT.txt) |

Deezer Research's published Spleeter paper states that its “source code and pre-trained models are available on github and distributed under a MIT license.” The MIT text grants permission to use, copy, modify, distribute, sublicense, and sell copies. It requires preserving the copyright and license notice, which ships with Blacktable. This is the license basis for bundling the exact checkpoint above. [Published paper](https://doi.org/10.21105/joss.02154) · [Paper source statement](https://github.com/deezer/spleeter/blob/master/paper.md) · [Deezer's v1.4.0 MIT license](https://github.com/deezer/spleeter/blob/v1.4.0/LICENSE)

Blacktable runs the unmodified checkpoint with TensorFlow on the user's CPU. It processes overlapping audio windows and crossfades their boundaries. The four outputs are vocals, drums, bass, and other. The two-stem mode uses the vocals output and sums drums, bass, and other for accompaniment. The checkpoint estimates separation below about 11 kHz, so its sound and high-frequency response can differ from the earlier HTDemucs engine. [Spleeter audio parameters](https://github.com/deezer/spleeter/wiki/3.-Models#audio-parameters)

Version 0.1.2 and earlier used HTDemucs. The new runtime has no HTDemucs dependency. Old model caches from an earlier install belong to the user and may still exist in their profile. This provenance record applies to the exact Spleeter checkpoint above.
