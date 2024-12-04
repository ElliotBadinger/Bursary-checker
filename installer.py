#!/usr/bin/env python3
import subprocess
import sys
import os
import platform
from pathlib import Path
from tempfile import TemporaryDirectory
from rich.console import Console
from rich.progress import track
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_step(step):
    console.print(Panel(f"[bold green]{step}[/bold green]"), style="bold cyan")


def check_python_version():
    print_step("Checking Python Version")
    if sys.version_info < (3, 7):
        console.print(
            "[bold red]Error:[/bold red] Python 3.7 or higher is required.",
            style="red")
        sys.exit(1)
    console.print("[bold green]Python version check passed.[/bold green]")


def install_pip():
    print_step("Ensuring pip is installed")
    try:
        import pip
    except ImportError:
        console.print("[yellow]Pip not found. Installing pip...[/yellow]")
        subprocess.check_call(
            [sys.executable, "-m", "ensurepip", "--default-pip"])
        console.print("[bold green]Pip installed successfully.[/bold green]")


def create_virtual_environment():
    print_step("Creating Virtual Environment")
    import venv
    venv_dir = "bursary_env"

    if os.path.exists(venv_dir):
        console.print(
            f"[yellow]Found existing virtual environment at {venv_dir}[/yellow]"
        )
        return venv_dir

    console.print(
        f"[cyan]Creating new virtual environment at {venv_dir}[/cyan]")
    venv.create(venv_dir, with_pip=True)
    console.print(
        f"[bold green]Virtual environment created at {venv_dir}[/bold green]")
    return venv_dir


def get_python_executable(venv_dir):
    if platform.system() == "Windows":
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_path = os.path.join(venv_dir, "bin", "python")
    return python_path


def install_requirements(python_path):
    print_step("Installing Required Packages")
    requirements = [
        "rich", "requests", "beautifulsoup4", "reportlab", "tqdm", "urllib3"
    ]

    # Upgrade pip first to ensure it's working correctly
    try:
        subprocess.check_call(
            [python_path, "-m", "pip", "install", "--upgrade", "pip"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        console.print("[yellow]Warning: Could not upgrade pip[/yellow]")

    for package in track(requirements, description="Installing packages..."):
        try:
            # Try installing without any additional flags
            subprocess.check_call(
                [python_path, "-m", "pip", "install", package],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            console.print(f"[green]Successfully installed {package}[/green]")
        except subprocess.CalledProcessError as e:
            # If standard install fails, try with more explicit options
            console.print(
                f"[yellow]Attempting alternative install for {package}...[/yellow]"
            )
            try:
                subprocess.check_call([
                    python_path, "-m", "pip", "install", "--no-cache-dir",
                    package
                ],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                console.print(
                    f"[green]Successfully installed {package}[/green]")
            except subprocess.CalledProcessError as e:
                console.print(
                    f"[bold red]Failed to install {package}[/bold red]",
                    style="red")
                console.print(
                    f"Error details: {e.stderr.decode('utf-8') if e.stderr else 'Unknown error'}",
                    style="red")
                sys.exit(1)

    console.print(
        "[bold green]All required packages installed successfully.[/bold green]"
    )


def main():
    console.print(
        Panel("[bold cyan]Welcome to the Bursary Checker Setup![/bold cyan]"))

    try:
        # Check Python version
        check_python_version()

        # Ensure pip is installed
        install_pip()

        # Create virtual environment
        venv_dir = create_virtual_environment()
        python_path = get_python_executable(venv_dir)

        # Install required packages
        install_requirements(python_path)

        # Ensure bursary_checker.py exists
        bursary_checker_path = Path("bursary_checker.py")
        if not bursary_checker_path.exists():
            console.print(
                Panel(
                    "[bold red]Error[/bold red]\n'bursary_checker.py' not found in the current directory. Please ensure the script is present and try again.",
                    style="red"))
            sys.exit(1)

        console.print(
            Panel("[bold green]Setup completed successfully![/bold green]"))
        console.print(
            f"\nYou can now run the bursary checker using:\n\n[cyan]{python_path} bursary_checker.py[/cyan]"
        )

        # Ask if user wants to run the script now
        response = console.input(
            "\nWould you like to run the bursary checker now? (y/n): ").lower(
            ).strip()
        if response == 'y':
            console.print(
                "\n[bold cyan]Starting Bursary Checker...[/bold cyan]")
            subprocess.call([python_path, str(bursary_checker_path)])
    except Exception as e:
        console.print(f"[bold red]Error during setup:[/bold red] {e}",
                      style="red")
        console.print(
            "[bold yellow]Please try running the setup script again.[/bold yellow]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
