FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

RUN apt-get update && apt-get install -y \
    git curl vim build-essential \
    && rm -rf /var/lib/apt/lists/*

USER vscode