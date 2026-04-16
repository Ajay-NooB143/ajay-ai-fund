from transformers import pipeline

# Load sentiment model
sentiment_pipeline = pipeline("sentiment-analysis")


def fingpt_sentiment(text):
    result = sentiment_pipeline(text)[0]
    return result['label']
