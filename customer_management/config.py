from dataclasses import dataclass
import os
from typing import Any, Mapping, Optional


@dataclass
class Settings:
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls.from_sources(env=os.environ)

    @classmethod
    def from_sources(
        cls,
        *,
        env: Optional[Mapping[str, str]] = None,
        secrets: Optional[Mapping[str, Any]] = None,
    ) -> "Settings":
        env_values = os.environ if env is None else env
        return cls(
            database_url=_get_required_setting(
                "DATABASE_URL", env=env_values, secrets=secrets
            )
        )


def _get_required_setting(
    key: str, *, env: Mapping[str, str], secrets: Optional[Mapping[str, Any]]
) -> str:
    value = _get_optional_setting(key, env=env, secrets=secrets)
    if value is None:
        raise KeyError(key)
    return value


def _get_optional_setting(
    key: str, *, env: Mapping[str, str], secrets: Optional[Mapping[str, Any]]
) -> Optional[str]:
    env_value = env.get(key)
    if env_value is not None:
        return env_value
    if secrets is not None:
        try:
            if key in secrets:
                value = secrets[key]
                if value is None:
                    return None
                return str(value)
        except Exception:
            pass
    return None
