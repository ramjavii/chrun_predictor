import logging

logger = logging.getLogger(__name__)


def explain(features: list[float], model_version: str) -> dict[str, float]:
    logger.info("SHAP explanation not yet implemented")
    return {}
