#!/usr/bin/env bash
# GitHub CLI shim for the managed-agent sandbox.
#
# Installs the gh CLI on first use (cached under /workspace for environment
# reuse), then execs it with a dummy token. The dummy value only satisfies the
# CLI's local auth check: the sandbox egress proxy injects the real credentials
# at the network layer (Bearer on api.github.com, Basic on github.com), so no
# secret exists inside this environment.
set -euo pipefail

GH_VERSION="${GH_VERSION:-2.63.2}"
GH_ROOT="/workspace/.gh-cli"
GH_BIN="$GH_ROOT/gh_${GH_VERSION}_linux_amd64/bin/gh"

if [ ! -x "$GH_BIN" ]; then
  mkdir -p "$GH_ROOT"
  curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz" \
    | tar -xz -C "$GH_ROOT"
fi

export GH_TOKEN="${GH_TOKEN:-dummy-token-proxy-injects-real-auth}"
export GIT_TERMINAL_PROMPT=0
export GH_PROMPT_DISABLED=1
export GH_NO_UPDATE_NOTIFIER=1
exec "$GH_BIN" "$@"
