from pathlib import Path
import yaml


class ConfigError(Exception):
    pass


def load_portals_config(portals_yml_path: str) -> dict:
    path = Path(portals_yml_path)
    if not path.exists():
        raise ConfigError(f"portals.yml not found: {path}")
    try:
        with path.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse portals.yml: {exc}") from exc
    if not isinstance(config, dict):
        raise ConfigError("portals.yml must be a YAML mapping")
    return config


def get_title_filter(config: dict) -> dict:
    tf = config.get("title_filter", {})
    return {
        "positive": [str(k).lower() for k in tf.get("positive", [])],
        "negative": [str(k).lower() for k in tf.get("negative", [])],
        "seniority_boost": [str(k).lower() for k in tf.get("seniority_boost", [])],
    }


def get_enabled_queries(config: dict, source: str) -> list[dict]:
    prefix = source.lower()
    return [
        q for q in config.get("search_queries", [])
        if q.get("enabled", False) and q.get("name", "").lower().startswith(prefix)
    ]
