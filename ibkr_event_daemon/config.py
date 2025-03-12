from ib_async.ib import StartupFetch
from ib_async.ib import StartupFetchALL
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class IBConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IB_")

    # IB Connection Settings
    host: str = "127.0.0.1"
    port: int = 7497
    clientId: int = 1
    timeout: float = 4.0
    readonly: bool = False
    account: str = ""
    raiseSyncErrors: bool = False
    fetchFields: StartupFetch = StartupFetchALL

class DaemonConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IB_")
    tasks: str = ""
    log_level: str = "INFO"

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IB_")
    ib: IBConfig = IBConfig()
    daemon: DaemonConfig = DaemonConfig()


if __name__ == "__main__":
    config = Config()

    print(config.model_dump())
