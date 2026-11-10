"""Typed, transport-independent errors for audio inspection."""

class AudioInspectionError(Exception):
    """Base class for safe audio-boundary failures."""

    code = "AUDIO_INSPECTION_ERROR"
    status_code = 400

    def __init__(self, message: str = "Audio inspection failed.") -> None:
        super().__init__(message)


class AudioConfigurationError(AudioInspectionError):
    code = "AUDIO_CONFIGURATION_ERROR"
    status_code = 500


class UnsupportedAudioContainerError(AudioInspectionError):
    code = "UNSUPPORTED_AUDIO_CONTAINER"
    status_code = 415


class UnsupportedAudioEncodingError(AudioInspectionError):
    code = "UNSUPPORTED_AUDIO_ENCODING"
    status_code = 415


class MalformedWaveError(AudioInspectionError):
    code = "MALFORMED_WAVE"
    status_code = 400


class EmptyWaveError(AudioInspectionError):
    code = "EMPTY_WAVE"
    status_code = 400


class AudioResourceLimitError(AudioInspectionError):
    code = "AUDIO_RESOURCE_LIMIT"
    status_code = 413


class NoMeasurableAudioSignalError(AudioInspectionError):
    code = "NO_MEASURABLE_AUDIO_SIGNAL"
    status_code = 422


class AudioMetricCalculationError(AudioInspectionError):
    code = "AUDIO_METRIC_CALCULATION_ERROR"
    status_code = 422


class SpeechAnalysisError(AudioInspectionError):
    """Base class for deterministic speech-boundary failures."""

    code = "SPEECH_ANALYSIS_ERROR"
    status_code = 422


class SpeechConfigurationError(SpeechAnalysisError):
    code = "SPEECH_CONFIGURATION_ERROR"
    status_code = 500


class SpeechAnalysisResourceError(SpeechAnalysisError):
    code = "SPEECH_ANALYSIS_RESOURCE_LIMIT"
    status_code = 422


class SpeechMetricCalculationError(SpeechAnalysisError):
    code = "SPEECH_METRIC_CALCULATION_ERROR"
