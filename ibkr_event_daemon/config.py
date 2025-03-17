from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing_extensions import Optional


class IbkrSettings(BaseSettings):  # noqa: D101
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="IBKR_",
    )

    host: str = Field(default="127.0.0.1", validation_alias="ibkr_host", alias="host")
    port: int = Field(default=7497, validation_alias="ibkr_port", alias="port")
    clientid: int = Field(default=1, validation_alias="ibkr_clientid", alias="clientId")
    timeout: int = Field(default=4, validation_alias="ibkr_timeout", alias="timeout")
    readonly: bool = Field(default=False, validation_alias="ibkr_readonly", alias="readonly")
    account: str = Field(default="", validation_alias="ibkr_account", alias="account")
    raisesyncerrors: bool = Field(default=False, validation_alias="ibkr_raisesyncerrors", alias="raiseSyncErrors")

    paths: Optional[str] = None
