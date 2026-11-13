# =============================================================================
# Quality Factory — Usine de tests pour la Nuit de l'Info 2026
#
# Image de base : buildpack-deps:noble (image officielle Docker, variante
# Ubuntu 24.04 — même base que les runners `ubuntu-latest` de GitHub Actions).
# Elle embarque déjà curl, git, gnupg, ca-certificates, build-essential et
# l'ensemble des bibliothèques de développement usuelles, ce qui évite les
# échecs de compilation des modules natifs (node-gyp, extensions C Python…).
#
# Build (contexte = racine du dépôt) :
#   docker build -t quality_factory -f quality_factory/Dockerfile .
# =============================================================================
FROM buildpack-deps:noble

LABEL maintainer="Fabien Haingue"
LABEL description="Quality Factory - Usine de tests pour Nuit de l'Info 2026"
LABEL version="2.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# Fait échouer le build dès qu'une commande d'un pipeline échoue (évite les
# installations silencieusement cassées du type `curl ... | bash`).
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# --- Certificats d'entreprise (optionnel) ------------------------------------
# Pour builder derrière un proxy avec inspection TLS, déposer les CA (.crt,
# format PEM) dans quality_factory/certs/ : ils sont ajoutés au magasin
# système AVANT tout téléchargement. Installés avant le JDK, ils sont aussi
# importés automatiquement dans le truststore Java par ca-certificates-java.
COPY quality_factory/certs/ /usr/local/share/ca-certificates/extra/
RUN rm -f /usr/local/share/ca-certificates/extra/.gitkeep \
          /usr/local/share/ca-certificates/extra/README.md && \
    update-ca-certificates

# --- Runtimes : Java 21, Python 3.12, Maven ----------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      jq \
      unzip \
      openjdk-21-jdk-headless \
      maven \
      python3 \
      python3-venv \
      python3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    # Lien indépendant de l'architecture (amd64/arm64) pour JAVA_HOME
    ln -s /usr/lib/jvm/java-21-openjdk-* /usr/lib/jvm/java-21

# --- Java -------------------------------------------------------------------
ENV JAVA_HOME=/usr/lib/jvm/java-21
ENV PATH="$JAVA_HOME/bin:$PATH"

# --- Node.js (tarball officiel nodejs.org, version épinglée + SHA-256) -------
# Pas de nvm (sourcing de shell fragile) ni de dépôt tiers : même approche que
# l'image officielle `node`. Binaires dans /usr/local/bin.
ENV NODE_VERSION=22.23.5
RUN ARCH="$(dpkg --print-architecture)" && \
    case "$ARCH" in \
      amd64) NODE_ARCH=x64;   NODE_SHA256=cdeb8670a0c81f51b4dc4ac61919f9b1ad917b304bf8221eb939570663d240f8 ;; \
      arm64) NODE_ARCH=arm64; NODE_SHA256=2babb9eb5264860d540849f4b064a6fbdebcdc323657d9d382ce23d313fd5e09 ;; \
      *) echo "Architecture non supportée : $ARCH" >&2; exit 1 ;; \
    esac && \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz" -o /tmp/node.tar.xz && \
    echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c - && \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --no-same-owner && \
    rm /tmp/node.tar.xz && \
    npm install -g pnpm@9.15.9

# Fait confiance au magasin système (CA d'entreprise inclus) pour les
# téléchargements effectués PENDANT l'exécution des tests (npm/pnpm, pip).
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

# --- Gradle -----------------------------------------------------------------
ENV GRADLE_VERSION=8.8
RUN curl -fsSL "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" -o /tmp/gradle.zip && \
    unzip -q /tmp/gradle.zip -d /opt && \
    rm /tmp/gradle.zip && \
    ln -s /opt/gradle-${GRADLE_VERSION} /opt/gradle

ENV GRADLE_HOME=/opt/gradle
ENV PATH="$GRADLE_HOME/bin:$PATH"

# --- Quality Factory --------------------------------------------------------
WORKDIR /quality_factory

# Dépendances Python d'abord (couche mise en cache si requirements.txt ne
# change pas), puis le code.
COPY quality_factory/requirements.txt ./requirements.txt
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

COPY quality_factory/ /quality_factory/

# --- Vérification de l'outillage (fait échouer le build si un outil manque) --
RUN set -eux; \
    java -version; \
    mvn -version; \
    gradle --version; \
    node --version; \
    npm --version; \
    pnpm --version; \
    python3 --version; \
    pytest --version

# --- Point d'entrée ----------------------------------------------------------
ENTRYPOINT ["/opt/venv/bin/python3", "-u", "/quality_factory/main.py"]
CMD ["--help"]
