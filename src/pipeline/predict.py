import logging

logger = logging.getLogger(__name__)


def predict_batch() -> None:
    logger.info("Batch prediction not yet implemented")


def predict_single(features: list[float]) -> float:
    logger.info("Single prediction not yet implemented")
    return 0.0
