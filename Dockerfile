FROM mambaorg/micromamba:latest

ARG MAMBA_DOCKERFILE_ACTIVATE=1

ENV USER=$MAMBA_USER
ENV APP_HOME=/home/${USER}/web
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Copy just the env.yaml first. This means if only env.yaml changes, then cache for this step will be invalidated
COPY --chown=$USER:$USER environment.yml /tmp/environment.yml

# Install dependencies with micromamba
RUN micromamba install -y -n base -f /tmp/environment.yml && micromamba clean --all --yes

# Now copy the rest of the application. If these files change, the previous layers (micromamba environment) will remain cached
COPY --chown=$USER:$USER . $APP_HOME
WORKDIR $APP_HOME

# Install the project itself
RUN pip install -e .

# Debug: run a micromamba command
RUN micromamba --version
