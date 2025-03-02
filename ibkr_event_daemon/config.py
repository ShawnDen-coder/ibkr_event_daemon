from ib_async.ib import StartupFetch
from ib_async.ib import StartupFetchALL
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Config(BaseSettings):  # noqa: D101
    model_config = SettingsConfigDict(env_prefix="IB_")

    # IB Connection Settings
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1
    timeout: float = 4.0
    readonly: bool = False
    account: str = ""
    raise_sync_errors: bool = False
    fetch_fields: StartupFetch = StartupFetchALL
