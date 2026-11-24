
import math
import random
import wave
import hashlib
from array import array
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def generate_music(theme, destination, duration=30):

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date().isoformat()

    seed = hashlib.sha256(
        f"{today}-{theme}".encode()
    ).hexdigest()

    rng = random.Random(seed)

    settings = {
        "morning": (95, [60, 62, 64, 67, 69]),
        "afternoon": (110, [60, 64, 65, 67, 72]),
        "evening": (75, [57, 60, 62, 64, 67]),
        "night": (60, [48, 52, 55, 57, 60]),
    }

    bpm, notes = settings[theme]
    bpm += rng.randint(-5, 5)

    sample_rate = 22050
    beat = 60 / bpm

    total_samples = int(duration * sample_rate)
    samples = array("h")

    melody = [
        rng.choice(notes)
        for _ in range(
            int(duration / beat) + 2
        )
    ]

    for i in range(total_samples):

        t = i / sample_rate
        note_index = int(t / beat)
        local_time = t % beat

        note = melody[note_index]

        frequency = 440 * (
            2 ** ((note - 69) / 12)
        )

        envelope = min(
            1.0,
            local_time / 0.06
        )

        envelope *= math.exp(
            -2.5 * local_time
        )

        tone = math.sin(
            2 * math.pi * frequency * local_time
        )

        harmonic = 0.20 * math.sin(
            4 * math.pi * frequency * local_time
        )

        bass = 0.25 * math.sin(
            2 * math.pi * (frequency / 2) * local_time
        )

        fade = min(
            1.0,
            t / 1.5,
            (duration - t) / 2.0
        )

        value = (
            (tone + harmonic + bass)
            * envelope
            * fade
            * 6500
        )

        samples.append(
            int(max(-32767, min(32767, value)))
        )

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with wave.open(str(destination), "wb") as audio:

        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(samples.tobytes())

    print(
        f"Music created: {destination}",
        flush=True
    )

    return destination


if __name__ == "__main__":

    for theme in [
        "morning",
        "afternoon",
        "evening",
        "night"
    ]:

        generate_music(
            theme,
            f"output/music_{theme}.wav"
        )

    print("ALL 4 MUSIC FILES CREATED")
