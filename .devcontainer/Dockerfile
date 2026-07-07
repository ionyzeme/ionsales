# .NET SDK base — needed for plugins, pac modelbuilder early-bound classes,
# and to install the pac CLI as a global dotnet tool.
FROM mcr.microsoft.com/devcontainers/dotnet:1-8.0-bookworm

# The bookworm dotnet image ships a pre-configured Yarn apt repository
# (/etc/apt/sources.list.d/yarn.list). Yarn has since rotated its package
# signing key, so the keyring baked into the image no longer verifies it:
#   GPG error: https://dl.yarnpkg.com/debian stable InRelease: NO_PUBKEY 62D54FD4003F6525
#   E: The repository 'https://dl.yarnpkg.com/debian stable InRelease' is not signed.
# Because EVERY devcontainer feature runs `apt-get update` on startup, that one
# unsigned repo fails the whole build (the dotnet feature just happens to be
# first). Yarn isn't used here — the Node feature provides npm/corepack — so we
# simply drop the stale source. Running apt-get update here also surfaces any
# remaining repo problems at image-build time rather than mid-feature.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
 && apt-get update \
 && rm -rf /var/lib/apt/lists/*
