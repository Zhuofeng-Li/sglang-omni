"""Use the frozen SeedTTS snapshot for the common qualification client."""
import runpy

from benchmarks.dataset import seedtts

load_samples = seedtts.load_seedtts_samples


def load_pinned_samples(*args, **kwargs):
    kwargs["revision"] = "27f4c1adee83b5b29b7c4b375f6b976324bda308"
    return load_samples(*args, **kwargs)


seedtts.load_seedtts_samples = load_pinned_samples
runpy.run_module("benchmarks.eval.benchmark_tts_seedtts", run_name="__main__")
