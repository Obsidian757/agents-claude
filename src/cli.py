#!/usr/bin/env python3
"""
Command-line interface for Agents-Claude
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.agents.policy_analyzer import PolicyAnalyzer

app = typer.Typer(help="Federal AI Compliance Agents with Claude")
console = Console()


@app.command()
def analyze(
    question: str = typer.Argument(..., help="Compliance question to analyze"),
    policy: Optional[str] = typer.Option(None, "--policy", "-p", help="Specific policy to focus on"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed reasoning"),
):
    """Analyze a federal AI compliance question"""
    
    console.print(Panel.fit(
        "🏛️  Federal AI Policy Analyzer",
        style="bold blue"
    ))
    
    try:
        analyzer = PolicyAnalyzer()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Question:[/cyan] {question}")
    if policy:
        console.print(f"[cyan]Policy:[/cyan] {policy}")
    
    with console.status("[bold green]Analyzing with Claude..."):
        result = analyzer.analyze(question, policy)
    
    # Display results
    console.print(f"\n[bold]Confidence:[/bold] [{_confidence_color(result.confidence)}]{result.confidence}[/{_confidence_color(result.confidence)}]")
    
    if verbose and result.reasoning_steps:
        console.print("\n[bold]Reasoning:[/bold]")
        for i, step in enumerate(result.reasoning_steps, 1):
            console.print(f"  {i}. {step}")
    
    console.print(f"\n[bold]Answer:[/bold]\n{result.answer}\n")
    
    if result.recommendations:
        console.print("[bold]Recommendations:[/bold]")
        for rec in result.recommendations:
            console.print(f"  ✓ {rec}")
    
    if result.related_policies:
        console.print(f"\n[bold]Related:[/bold] {', '.join(result.related_policies)}")


def _confidence_color(confidence: str) -> str:
    """Get color for confidence level"""
    return {
        "High": "green",
        "Medium": "yellow",
        "Low": "red"
    }.get(confidence, "white")


@app.command()
def interactive():
    """Start interactive mode"""
    
    console.print(Panel.fit(
        "🏛️  Federal AI Policy Analyzer - Interactive Mode\n"
        "Type 'quit' to exit",
        style="bold blue"
    ))
    
    try:
        analyzer = PolicyAnalyzer()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    while True:
        console.print()
        question = console.input("[bold cyan]Question:[/bold cyan] ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            console.print("[green]Goodbye![/green]")
            break
        
        policy = console.input("[bold cyan]Policy (optional):[/bold cyan] ").strip() or None
        
        with console.status("[bold green]Analyzing..."):
            result = analyzer.analyze(question, policy)
        
        console.print(f"\n[bold]Confidence:[/bold] [{_confidence_color(result.confidence)}]{result.confidence}[/{_confidence_color(result.confidence)}]")
        console.print(f"[bold]Answer:[/bold]\n{result.answer}\n")


@app.command()
def version():
    """Show version"""
    console.print("Agents-Claude v0.1.0")


if __name__ == "__main__":
    app()
