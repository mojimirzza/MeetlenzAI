from __future__ import annotations
from pathlib import Path


class AudioService:
    """Optional local audio layer. It never sends audio to a remote service."""
    def __init__(self, model_name: str = "small") -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_name, device="auto", compute_type="auto")
        return self._model

    def transcribe(self, audio_path: str) -> list[dict]:
        model = self._load()
        segments, info = model.transcribe(audio_path, vad_filter=True, word_timestamps=True)
        return [
            {"start": s.start, "end": s.end, "text": s.text.strip(), "language": info.language}
            for s in segments
        ]


class DiarizationService:
    """Optional local speaker diarization, kept separate because model access/setup is heavier."""
    def __init__(self, token: str | None = None) -> None:
        self.token = token
        self._pipeline = None

    def diarize(self, audio_path: str) -> list[dict]:
        if self._pipeline is None:
            from pyannote.audio import Pipeline
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-community-1", token=self.token
            )
        output = self._pipeline(audio_path)
        return [
            {"start": turn.start, "end": turn.end, "speaker": speaker}
            for turn, _, speaker in output.speaker_diarization.itertracks(yield_label=True)
        ]
