"""
CLI interface for Okta MCP Server.

This module provides command-line interface for managing the server.
"""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from config import get_config, Config
from server import OktaMCPServer
from rbac.rbac_manager import initialize_rbac_manager
from models.schemas import Role
from utils.logging import configure_logging

app = typer.Typer(
    name="okta-mcp-server",
    help="Okta MCP Server - AI agent interface for Okta user and group management"
)
console = Console()


@app.command()
def start():
    """Start the MCP server."""
    console.print("[bold green]Starting Okta MCP Server...[/bold green]")

    try:
        asyncio.run(main_start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


async def main_start():
    """Async main function for starting server."""
    config = get_config()
    configure_logging(config.server.log_level)

    server = OktaMCPServer(config)
    await server.initialize()
    await server.run()


@app.command()
def health():
    """Check server health status."""
    console.print("[bold blue]Checking server health...[/bold blue]")

    try:
        asyncio.run(check_health())
    except Exception as e:
        console.print(f"[bold red]Health check failed:[/bold red] {str(e)}")
        sys.exit(1)


async def check_health():
    """Async health check."""
    config = get_config()
    configure_logging(config.server.log_level)

    server = OktaMCPServer(config)
    await server.initialize()

    health_status = await server.health_check()

    # Display health status
    table = Table(title="Health Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("Overall", health_status["status"])
    for component, status in health_status["components"].items():
        table.add_row(component, status)

    console.print(table)
    console.print("\n[bold green]✓ Server is healthy[/bold green]")


@app.command()
def config(
    validate: bool = typer.Option(
        False,
        "--validate",
        help="Validate configuration"
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration"
    )
):
    """Manage server configuration."""
    try:
        cfg = get_config()

        if validate:
            console.print("[bold blue]Validating configuration...[/bold blue]")
            errors = cfg.validate_config()

            if errors:
                console.print("\n[bold red]Configuration errors:[/bold red]")
                for error in errors:
                    console.print(f"  • {error}")
                sys.exit(1)
            else:
                console.print("[bold green]✓ Configuration is valid[/bold green]")

        if show:
            console.print("[bold blue]Current Configuration:[/bold blue]\n")

            table = Table()
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="yellow")

            # Okta config
            table.add_row("Okta Domain", cfg.okta.domain)
            table.add_row("Okta Client ID", cfg.okta.client_id)
            table.add_row("Okta Redirect URI", cfg.okta.redirect_uri)

            # Redis config
            table.add_row("Redis URL", cfg.redis.url)
            table.add_row("Redis Enabled", str(cfg.redis.enabled))

            # Cache config
            table.add_row("Cache TTL", f"{cfg.cache.ttl}s")
            table.add_row("Cache Max Size", str(cfg.cache.max_size))

            # Server config
            table.add_row("Server Host", cfg.server.host)
            table.add_row("Server Port", str(cfg.server.port))
            table.add_row("Log Level", cfg.server.log_level)

            # RBAC config
            table.add_row("RBAC Policy Path", cfg.rbac.policy_path)
            table.add_row("Default Role", cfg.rbac.default_role)

            # OTel config
            table.add_row("Telemetry Enabled", str(cfg.otel.enabled))
            table.add_row("OTLP Endpoint", cfg.otel.exporter_otlp_endpoint)

            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def generate_rbac():
    """Generate and display RBAC policy information."""
    console.print("[bold blue]RBAC Policy Information[/bold blue]\n")

    try:
        config = get_config()

        # Check if policy files exist
        model_path = Path("rbac/model.conf")
        policy_path = Path(config.rbac.policy_path)

        if not model_path.exists():
            console.print(f"[red]Model file not found: {model_path}[/red]")
            sys.exit(1)

        if not policy_path.exists():
            console.print(f"[red]Policy file not found: {policy_path}[/red]")
            sys.exit(1)

        # Initialize RBAC manager
        rbac = initialize_rbac_manager(str(model_path), str(policy_path))

        # Display roles
        console.print("[bold]Available Roles:[/bold]")
        for role in Role:
            console.print(f"  • {role.value}")

        console.print("\n[bold]Permissions by Role:[/bold]\n")

        # Create table for each role
        for role in Role:
            permissions = rbac.get_permissions_for_role(role)

            if permissions:
                table = Table(title=f"Role: {role.value}")
                table.add_column("Resource", style="cyan")
                table.add_column("Action", style="green")

                for resource, action in permissions:
                    table.add_row(resource, action)

                console.print(table)
                console.print()

        console.print("[bold green]✓ RBAC policy loaded successfully[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def version():
    """Show version information."""
    console.print("[bold]Okta MCP Server[/bold]")
    console.print("Version: 1.0.0")
    console.print("Python MCP SDK")
    console.print("\nFor more information, visit:")
    console.print("  https://github.com/your-org/okta-mcp-server")


@app.callback()
def callback():
    """Okta MCP Server - Manage Okta users and groups via MCP protocol."""
    pass


if __name__ == "__main__":
    app()
