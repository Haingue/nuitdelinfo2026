# Dockerfile pour Quality Factory
# Image de base: Ubuntu 24.04
FROM ubuntu:24.04

# Métadonnées
LABEL maintainer="Fabien Haingue"
LABEL description="Quality Factory - Usine de tests pour Nuit de l'Info 2026"
LABEL version="1.0.0"

# Configuration de l'environnement
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# --- Installation des dépendances système ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      git \
      jq \
      unzip \
      sudo \
      ca-certificates \
      gnupg \
      && rm -rf /var/lib/apt/lists/*

# --- Installation de Java (OpenJDK 21) ---
ENV JAVA_VERSION=21
RUN apt-get install -y openjdk-${JAVA_VERSION}-jdk-headless && \
    update-alternatives --set java /usr/lib/jvm/java-${JAVA_VERSION}-openjdk-amd64/bin/java && \
    update-alternatives --set javac /usr/lib/jvm/java-${JAVA_VERSION}-openjdk-amd64/bin/javac

ENV JAVA_HOME=/usr/lib/jvm/java-${JAVA_VERSION}-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# --- Installation de Python 3.11 ---
ENV PYTHON_VERSION=3.11
RUN apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --set python3 /usr/bin/python${PYTHON_VERSION}

ENV PYTHON_HOME=/usr
ENV PATH="$PYTHON_HOME/bin:$PATH"

# --- Installation de Node.js via nvm ---
ENV NODE_VERSION=20
ENV NVM_DIR=/usr/local/nvm
ENV NVM_VERSION=v0.40.1

# Installer nvm
RUN mkdir -p $NVM_DIR && \
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default

# Ajouter nvm au PATH
ENV PATH="$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH"

# Installer pnpm globalement
RUN npm install -g pnpm@9.15.9

# --- Installation de Maven ---
RUN apt-get install -y maven

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

# --- Point d'entrée ---
ENTRYPOINT ["/run.sh"]

# Commande par défaut
CMD ["--help"]
