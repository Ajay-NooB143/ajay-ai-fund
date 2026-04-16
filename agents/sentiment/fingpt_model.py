import logging
import threading

from transformers import pipeline

logger = logging.getLogger(__name__)

DEFAULT_SENTIMENT = "NEUTRAL"

# Lazy-loaded sentiment model
_sentiment_pipeline = None
_pipeline_load_failed = False
_pipeline_lock = threading.Lock()


def _get_pipeline():
    global _sentiment_pipeline, _pipeline_load_failed
    if _sentiment_pipeline is None and not _pipeline_load_failed:
        with _pipeline_lock:
            if _sentiment_pipeline is None and not _pipeline_load_failed:
                try:
                    _sentiment_pipeline = pipeline("sentiment-analysis")
                except Exception as e:
                    _pipeline_load_failed = True
                    logger.warning("Failed to load sentiment model: %s", e)
    return _sentiment_pipeline


def fingpt_sentiment(text):
    pipe = _get_pipeline()
    if pipe is None:
        return DEFAULT_SENTIMENT
    result = pipe(text)[0]
    return result['label']
