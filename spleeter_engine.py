"""Run Deezer's Spleeter 4-stem inference graph from the official v1.4.0 checkpoint."""
import argparse
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path
import shutil
import tarfile
from tempfile import TemporaryDirectory
from urllib.request import urlopen
import wave

MODEL_URL = "https://github.com/deezer/spleeter/releases/download/v1.4.0/4stems.tar.gz"
MODEL_ARCHIVE_SHA256 = "3adb4a50ad4eb18c7c4d65fcf4cf2367a07d48408a5eb7d03cd20067429dfaa8"
MODEL_FILES = {
    "model.meta": "f2c2843e3c8c84c737d0ba642fef798d24056f8dbb0b2e2d58a19de55b20034e",
    "model.index": "99ea41b3ef9bfbc6a34520409427af5ba7a883173e57ea25d6c487584b891b18",
    "model.data-00000-of-00001": "3823e0ef50835cca3907c386dc9667a6a9af77b40a20c3ab845a8d6c9592255d",
}
# Output nodes belong to this exact inference graph, as checked from its stem mask inputs.
OUTPUTS = {
    "vocals": "strided_slice_13:0",
    "drums": "strided_slice_23:0",
    "bass": "strided_slice_33:0",
    "other": "strided_slice_43:0",
}
SAMPLE_RATE = 44100
CHUNK_FRAMES = 32 * SAMPLE_RATE
OVERLAP_FRAMES = SAMPLE_RATE


def matches(path, sha256):
    if not path.is_file():
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == sha256


def verified_model(directory):
    return all(matches(directory / name, digest) for name, digest in MODEL_FILES.items())


def prepare_model(directory, cache):
    if verified_model(directory):
        return
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / "spleeter-v1.4.0-4stems.tar.gz"
    if not matches(archive, MODEL_ARCHIVE_SHA256):
        with TemporaryDirectory(prefix="spleeter-download-", dir=cache) as temporary:
            download = Path(temporary) / archive.name
            print("Downloading the official Spleeter four-stem checkpoint.", flush=True)
            with urlopen(MODEL_URL, timeout=60) as response, download.open("wb") as output:
                shutil.copyfileobj(response, output)
            if not matches(download, MODEL_ARCHIVE_SHA256):
                raise ValueError("The downloaded Spleeter archive did not match its pinned SHA-256.")
            download.replace(archive)

    directory.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="spleeter-checkpoint-", dir=directory.parent) as temporary:
        staging = Path(temporary)
        with tarfile.open(archive, "r:gz") as bundle:
            for name in MODEL_FILES:
                member = bundle.getmember(name)
                if not member.isfile():
                    raise ValueError(f"Invalid Spleeter archive entry {name}")
                with bundle.extractfile(member) as source, (staging / name).open("wb") as output:
                    shutil.copyfileobj(source, output)
        if not verified_model(staging):
            raise ValueError("The extracted Spleeter checkpoint did not match its pinned SHA-256.")
        directory.mkdir(exist_ok=True)
        for name in MODEL_FILES:
            (staging / name).replace(directory / name)


def separate(model, input_file, destination, mode):
    if not verified_model(model):
        raise RuntimeError("The Spleeter checkpoint is missing or damaged. Run Blacktable setup again.")

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import numpy as np
    import tensorflow as tf

    tf.compat.v1.disable_eager_execution()
    graph = tf.Graph()
    with graph.as_default():
        saver = tf.compat.v1.train.import_meta_graph(str(model / "model.meta"), clear_devices=True)
    threads = min(4, os.cpu_count() or 1)
    config = tf.compat.v1.ConfigProto(
        intra_op_parallelism_threads=threads, inter_op_parallelism_threads=1, device_count={"GPU": 0})
    labels = OUTPUTS if mode == "four" else ("vocals", "no_vocals")
    with tf.compat.v1.Session(graph=graph, config=config) as session, ExitStack() as files:
        saver.restore(session, str(model / "model"))
        source = files.enter_context(wave.open(str(input_file), "rb"))
        if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (2, 2, SAMPLE_RATE):
            raise ValueError("Spleeter requires a normalized 44.1 kHz stereo WAV.")
        total = source.getnframes()
        outputs = {}
        for label in labels:
            output = files.enter_context(wave.open(str(destination / f"{label}.wav"), "wb"))
            output.setparams((2, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
            outputs[label] = output

        # Overlap input windows so long tracks stay within a fixed inference memory budget.
        fade = np.linspace(0, 1, OVERLAP_FRAMES, dtype=np.float32)[:, None]
        tails = {}
        start = 0
        while start < total:
            source.setpos(start)
            length = min(CHUNK_FRAMES, total - start)
            pcm = source.readframes(length)
            samples = np.frombuffer(pcm, dtype="<i2").reshape(length, 2).astype(np.float32) / 32768
            stems = session.run(OUTPUTS, {"waveform:0": samples, "keras_learning_phase:0": False})
            if mode == "two":
                stems = {"vocals": stems["vocals"], "no_vocals": stems["drums"] + stems["bass"] + stems["other"]}

            final = start + length == total
            count = length if final else length - OVERLAP_FRAMES
            for label, stem in stems.items():
                if stem.shape != (length, 2) or not np.isfinite(stem).all():
                    raise RuntimeError(f"Spleeter returned invalid samples for {label}.")
                if label in tails:
                    end = min(length, OVERLAP_FRAMES)
                    blend = fade[:end]
                    stem[:end] = tails[label][:end] * (1 - blend) + stem[:end] * blend
                if not final:
                    tails[label] = stem[count:].copy()
                pcm_stem = np.rint(np.clip(stem[:count] * 32768, -32768, 32767)).astype("<i2")
                outputs[label].writeframesraw(pcm_stem.tobytes())
            start += count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("model", type=Path)
    prepare.add_argument("cache", type=Path)
    split = commands.add_parser("split")
    split.add_argument("model", type=Path)
    split.add_argument("input", type=Path)
    split.add_argument("output", type=Path)
    split.add_argument("mode", choices=("four", "two"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare_model(args.model, args.cache)
    else:
        separate(args.model, args.input, args.output, args.mode)


if __name__ == "__main__":
    main()
