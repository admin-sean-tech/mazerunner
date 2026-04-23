# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

MazeRunner is a 2D game where the character explores mazes to find the exit.
There are stages with different mazes and items. Once the character reaches the exit, it enters the next stage.

## Tooling

- Python requirement: `>=3.15` (per `pyproject.toml`). `.python-version` pins the local interpreter.
- Build system: `pyproject.toml` only; no `uv.lock`/`poetry.lock` yet — the package manager choice is still open.
- Run the entrypoint: `uv run`.
- Game engine: `pygame-ce >=2.5.7`
