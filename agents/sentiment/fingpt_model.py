import logging

from transformers import pipeline

logger = logging.getLogger(__name__)

# Lazy-loaded sentiment model
_sentiment_pipeline = None
_pipeline_load_failed = False


def _get_pipeline():
    global _sentiment_pipeline, _pipeline_load_failed
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
        return "NEUTRAL"
    result = pipe(text)[0]
    return result['label']
