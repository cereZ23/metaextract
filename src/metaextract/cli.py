"""Command-line interface for metaextract."""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from metaextract import __version__
from metaextract.core.models import FileType, ScanResults
from metaextract.download.downloader import AsyncDownloader
from metaextract.export.html import HTMLExporter
from metaextract.export.json import JSONExporter
from metaextract.processing.processor import ResultProcessor
from metaextract.search.duckduckgo import DuckDuckGoSearch

console = Console()

BANNER = r"""
[bold blue]
 __  __      _        _____      _                  _
|  \/  | ___| |_ __ _| ____|_  _| |_ _ __ __ _  ___| |_
| |\/| |/ _ \ __/ _` |  _| \ \/ / __| '__/ _` |/ __| __|
| |  | |  __/ || (_| | |___ >  <| |_| | | (_| | (__| |_
|_|  |_|\___|\__\__,_|_____/_/\_\__|_|  \__,_|\___|\__|
[/bold blue]
[dim]Document Metadata Extraction for OSINT - v{version}[/dim]
"""


@click.command()
@click.option(
    "-d", "--domain",
    help="Domain to search for documents",
)
@click.option(
    "-t", "--filetypes",
    default="pdf,doc,docx,xls,xlsx,ppt,pptx",
    help="File types to search (comma-separated)",
)
@click.option(
    "-l", "--limit",
    default=200,
    type=int,
    help="Limit of search results per file type",
)
@click.option(
    "-n", "--download-limit",
    default=50,
    type=int,
    help="Maximum number of files to download per type",
)
@click.option(
    "-o", "--output-dir",
    default="./downloads",
    type=click.Path(),
    help="Directory to save downloaded files",
)
@click.option(
    "-f", "--output-file",
    type=click.Path(),
    help="Output report file (HTML or JSON based on extension)",
)
@click.option(
    "--local",
    is_flag=True,
    help="Analyze local files only (no search/download)",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Force JSON output format",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Verbose output",
)
@click.option(
    "--delay",
    default=3.0,
    type=float,
    help="Delay between searches in seconds (default: 3.0, helps avoid rate limiting)",
)
@click.option(
    "--no-rotate-ua",
    is_flag=True,
    help="Disable User-Agent rotation",
)
@click.version_option(version=__version__)
def main(
    domain: str | None,
    filetypes: str,
    limit: int,
    download_limit: int,
    output_dir: str,
    output_file: str | None,
    local: bool,
    json_output: bool,
    verbose: bool,
    delay: float,
    no_rotate_ua: bool,
) -> None:
    """MetaExtract - Document metadata extraction for OSINT.

    Search for and download documents from a domain, then extract metadata
    including usernames, email addresses, software versions, and file paths.

    Examples:

        # Search a domain for documents
        metaextract -d example.com -t pdf,docx -n 50 -f report.html

        # Analyze local files
        metaextract --local -o ./documents -f report.json
    """
    console.print(BANNER.format(version=__version__))

    output_path = Path(output_dir)

    if local:
        # Local analysis mode
        if not output_path.exists():
            console.print(f"[red]Error: Directory {output_dir} does not exist[/red]")
            raise click.Abort()

        results = analyze_local_files(output_path, verbose)
    else:
        # Online search mode
        if not domain:
            console.print("[red]Error: Domain (-d) is required for online search[/red]")
            console.print("[dim]Use --local for local file analysis[/dim]")
            raise click.Abort()

        types = [t.strip().lower() for t in filetypes.split(",")]

        # Validate file types
        valid_types = {ft.value for ft in FileType}
        invalid = [t for t in types if t not in valid_types]
        if invalid:
            console.print(f"[yellow]Warning: Invalid file types ignored: {invalid}[/yellow]")
            types = [t for t in types if t in valid_types]

        if not types:
            console.print("[red]Error: No valid file types specified[/red]")
            raise click.Abort()

        output_path.mkdir(parents=True, exist_ok=True)

        results = asyncio.run(
            search_and_extract(
                domain=domain,
                file_types=types,
                search_limit=limit,
                download_limit=download_limit,
                output_dir=output_path,
                verbose=verbose,
                delay=delay,
                rotate_ua=not no_rotate_ua,
            )
        )

    # Display results
    display_results(results)

    # Export results
    if output_file:
        export_path = Path(output_file)

        if json_output or export_path.suffix.lower() == ".json":
            exporter = JSONExporter()
        else:
            exporter = HTMLExporter()

        exporter.export(results, export_path)
        console.print(f"\n[green]Report saved to: {export_path}[/green]")


async def search_and_extract(
    domain: str,
    file_types: list[str],
    search_limit: int,
    download_limit: int,
    output_dir: Path,
    verbose: bool,
    delay: float = 3.0,
    rotate_ua: bool = True,
) -> ScanResults:
    """Run the full search, download, and extraction workflow."""
    processor = ResultProcessor(domain=domain)

    search_engine = DuckDuckGoSearch(domain, delay=delay, rotate_ua=rotate_ua)

    try:
        for file_type in file_types:
            console.print(f"\n[cyan]Searching for {file_type.upper()} files on {domain}...[/cyan]")

            # Search
            with console.status("[bold green]Searching..."):
                try:
                    search_results = await search_engine.search_files(file_type, search_limit)
                except Exception as e:
                    console.print(f"[red]Search error: {e}[/red]")
                    continue

            if not search_results:
                console.print(f"[yellow]No {file_type} files found[/yellow]")
                continue

            console.print(f"[green]Found {len(search_results)} results[/green]")

            # Download
            urls = [r.url for r in search_results]
            downloader = AsyncDownloader(
                output_dir,
                max_concurrent=5,
                timeout=30,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Downloading {file_type.upper()} files...",
                    total=min(download_limit, len(urls)),
                )

                download_results = await downloader.download_files(urls, download_limit)

                progress.update(task, completed=len(download_results))

            # Count successful downloads
            successful = [r for r in download_results if r.success]
            console.print(f"[green]Downloaded {len(successful)}/{len(download_results)} files[/green]")

            # Extract metadata
            for dl_result in download_results:
                if dl_result.success and dl_result.local_path:
                    file_path = Path(dl_result.local_path)
                    processor.process_file(file_path, source_url=dl_result.url)

                    if verbose:
                        console.print(f"  [dim]Processed: {file_path.name}[/dim]")
                elif not dl_result.success:
                    processor.results.failed.append((dl_result.url, dl_result.error or "Download failed"))

    finally:
        await search_engine.close()

    return processor.get_results()


def analyze_local_files(directory: Path, verbose: bool) -> ScanResults:
    """Analyze files in a local directory."""
    console.print(f"\n[cyan]Analyzing files in {directory}...[/cyan]")

    processor = ResultProcessor(domain="local")

    # Get supported extensions
    supported_extensions = {ft.value for ft in FileType}

    # Find all supported files
    files = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lstrip(".").lower() in supported_extensions
    ]

    if not files:
        console.print("[yellow]No supported files found in directory[/yellow]")
        return processor.get_results()

    console.print(f"[green]Found {len(files)} files to analyze[/green]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting metadata...", total=len(files))

        for file_path in files:
            processor.process_file(file_path)
            progress.advance(task)

            if verbose:
                console.print(f"  [dim]Processed: {file_path.name}[/dim]")

    return processor.get_results()


def display_results(results: ScanResults) -> None:
    """Display results in formatted tables."""
    console.print("\n")

    # Summary panel
    stats = results.stats
    summary = f"""
[bold]Documents analyzed:[/bold] {stats['total_documents']}
[bold]Failed extractions:[/bold] {stats['failed_extractions']}
[bold]Unique users:[/bold] {stats['unique_users']}
[bold]Unique software:[/bold] {stats['unique_software']}
[bold]Unique emails:[/bold] {stats['unique_emails']}
[bold]Unique paths:[/bold] {stats['unique_paths']}
"""
    console.print(Panel(summary.strip(), title="[bold]Summary[/bold]", border_style="blue"))

    # Users table
    if results.unique_users:
        table = Table(title="[bold cyan]Users Found[/bold cyan]")
        table.add_column("Username", style="cyan")
        for user in results.unique_users[:20]:  # Limit display
            table.add_row(user)
        if len(results.unique_users) > 20:
            table.add_row(f"... and {len(results.unique_users) - 20} more")
        console.print(table)
        console.print()

    # Software table
    if results.unique_software:
        table = Table(title="[bold green]Software Found[/bold green]")
        table.add_column("Software", style="green")
        for soft in results.unique_software[:20]:
            table.add_row(soft)
        if len(results.unique_software) > 20:
            table.add_row(f"... and {len(results.unique_software) - 20} more")
        console.print(table)
        console.print()

    # Emails table
    if results.unique_emails:
        table = Table(title="[bold yellow]Emails Found[/bold yellow]")
        table.add_column("Email", style="yellow")
        for email in results.unique_emails[:20]:
            table.add_row(email)
        if len(results.unique_emails) > 20:
            table.add_row(f"... and {len(results.unique_emails) - 20} more")
        console.print(table)
        console.print()

    # Paths table
    if results.unique_paths:
        table = Table(title="[bold magenta]Paths & Servers Found[/bold magenta]")
        table.add_column("Path", style="magenta")
        for path in results.unique_paths[:20]:
            table.add_row(path)
        if len(results.unique_paths) > 20:
            table.add_row(f"... and {len(results.unique_paths) - 20} more")
        console.print(table)


if __name__ == "__main__":
    main()
