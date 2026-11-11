# Dockerfile pour Quality Factory
FROM ubuntu:24.04

# Métadonnées
LABEL maintainer="Fabien Haingue"
LABEL description="Quality Factory - Usine de tests pour Nuit de l'Info 2026"
LABEL version="1.0.0"

# Configuration de l'environnement
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# --- Installation de TOUTES les dépendances système en UNE SEULE couche ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      git \
      jq \
      unzip \
      sudo \
      ca-certificates \
      gnupg \
      # Java
      openjdk-21-jdk-headless \
      # Python 3.12 (version par défaut sur Ubuntu 24.04)
      python3 \
      python3-venv \
      python3-dev \
      # Maven
      maven \
      && rm -rf /var/lib/apt/lists/*

# --- Configuration Java ---
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"
RUN update-alternatives --set java $JAVA_HOME/bin/java && \
    update-alternatives --set javac $JAVA_HOME/bin/javac

# --- Configuration Python ---
# Sur Ubuntu 24.04, python3 pointe vers python3.12
RUN python3 --version
ENV PYTHON_HOME=/usr
ENV PATH="$PYTHON_HOME/bin:$PATH"

# --- Installation de Node.js via nvm ---
ENV NODE_VERSION=20
ENV NVM_DIR=/usr/local/nvm
ENV NVM_VERSION=v0.40.1

# Installer nvm
RUN mkdir -p $NVM_DIR && \
    # Installer nvm
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && \
    # Installer Node.js
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default && \
    # Installer pnpm
    npm install -g pnpm@9.15.9

# Ajouter nvm au PATH - nvm installe dans NVM_DIR/versions/node/v<VERSION>/bin
ENV PATH="$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH"

# --- Installation de Gradle ---
ENV GRADLE_VERSION=8.8
RUN curl -fsSL https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip -o /tmp/gradle.zip && \
    unzip -q /tmp/gradle.zip -d /opt && \
    rm /tmp/gradle.zip && \
    ln -s /opt/gradle-${GRADLE_VERSION} /opt/gradle

ENV GRADLE_HOME=/opt/gradle
ENV PATH="$GRADLE_HOME/bin:$PATH"

# --- Configuration du conteneur ---
WORKDIR /quality_factory

# Copier les fichiers de Quality Factory
COPY . .

# Créer l'environnement virtuel Python et installer les dépendances
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copier le script d'entrée
COPY run.sh /run.sh
RUN chmod +x /run.sh

# --- Script d'entrée qui charge nvm ---
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '. "$NVM_DIR/nvm.sh"' >> /entrypoint.sh && \
    echo 'nvm use default' >> /entrypoint.sh && \
    echo 'exec python3 -u "/quality_factory/main.py" "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# --- Point d'entrée ---
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--help"]