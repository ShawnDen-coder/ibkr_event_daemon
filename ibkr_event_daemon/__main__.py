"""Command-line interface for the IBKR event daemon.

This module provides a command-line interface using Click to manage the IBKR event daemon.
It supports commands for starting the daemon, configuring logging, and managing hooks.
The CLI can be accessed either through the installed command 'ibkr-daemon' or by running
the module directly.

Example:
    Using the installed command (recommended):
        >>> # Start the daemon with default settings
        >>> ibkr-daemon start
        >>> # Start with debug logging to file
        >>> ibkr-daemon start --log-level DEBUG --log-file logs/daemon.log
        >>> # Show current configuration
        >>> ibkr-daemon config show
        >>> # Show version
        >>> ibkr-daemon --version

    Using the Python module directly:
        >>> python -m ibkr_event_daemon start
        >>> python -m ibkr_event_daemon config show

Commands:
    start: Start the IBKR event daemon
    config show: Display current configuration
    config init: Create a new .env file with default settings
"""

import os
from importlib.metadata import version
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from ibkr_event_daemon.config import IbkrSettings
from ibkr_event_daemon.constants import ENV_PREFIX
from ibkr_event_daemon.core import IBKRClient
from ibkr_event_daemon.utils import setup_logger


try:
    __version__ = version("ibkr_event_daemon")
except Exception:
    # 如果包未安装，则使用开发版本号
    __version__ = "0.0.0.dev0"


@click.group()
@click.version_option(version=__version__)
def cli():
    """IBKR Event Daemon - A flexible event handler for Interactive Brokers TWS/Gateway."""
    pass


@cli.command()
@click.option(
    "--log-level",
    type=click.Choice(["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level.",
)
@click.option(
    "--log-file",
    type=click.Path(),
    help="Log file path. If not specified, logs will only go to console.",
)
@click.option(
    "--log-rotation",
    default="100 MB",
    help="Log rotation size (e.g., '100 MB', '1 GB')",
)
@click.option(
    "--log-retention",
    default="1 week",
    help="Log retention period (e.g., '1 week', '1 month')",
)
@click.option(
    "--host",
    help="TWS/Gateway host address",
)
@click.option(
    "--port",
    type=int,
    help="TWS/Gateway port number",
)
@click.option(
    "--client-id",
    type=int,
    help="Client ID for TWS/Gateway connection",
)
def start(
    log_level: str,
    log_file: Optional[str],
    log_rotation: str,
    log_retention: str,
    host: Optional[str],
    port: Optional[int],
    client_id: Optional[int],
):
    """Start the IBKR event daemon.

    This command starts the daemon with the specified configuration.
    If options are not provided, they will be read from environment
    variables or default values will be used.
    """
    # Setup logging
    if log_file:
        log_file = Path(log_file)
    setup_logger(
        log_level=log_level,
        log_file=log_file,
        rotation=log_rotation,
        retention=log_retention,
    )

    # Create settings with CLI options overriding env vars
    settings_dict = {}
    if host:
        settings_dict["host"] = host
    if port:
        settings_dict["port"] = port
    if client_id:
        settings_dict["clientid"] = client_id
    
    config = IbkrSettings(**settings_dict)
    
    logger.info(f"Starting IBKR daemon with config: {config.model_dump()}")
    
    client = IBKRClient(config=config)
    client.excute()


@cli.group()
def config():
    """Manage daemon configuration."""
    pass


@config.command(name="show")
def show_config():
    """Show current configuration settings."""
    # Load current settings
    settings = IbkrSettings()
    click.echo("Current Configuration:")
    click.echo("-" * 50)
    
    # Show environment variables
    click.echo("Environment Variables:")
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX):
            click.echo(f"  {key}={value}")
    
    click.echo("\nEffective Settings:")
    for key, value in settings.model_dump().items():
        click.echo(f"  {key}={value}")


@config.command(name="init")
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing .env file",
)
def init_config(force: bool):
    """Initialize a new .env file with default settings."""
    env_file = Path(".env")
    
    if env_file.exists() and not force:
        click.echo("Error: .env file already exists. Use --force to overwrite.")
        return
    
    settings = IbkrSettings()
    with env_file.open("w") as f:
        for key, value in settings.model_dump().items():
            env_key = f"{ENV_PREFIX}{key.upper()}"
            f.write(f"{env_key}={value}\n")
    
    click.echo(f"Created .env file at {env_file.absolute()}")


if __name__ == "__main__":
    cli()
