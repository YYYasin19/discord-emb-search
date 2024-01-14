# Discord Embedding Search

<img src="logo.png" width="35%">

Being somewhat dissatisfied with Discord's search functionality, I decided to make my own.
This is a simple Discord-Bot implemented in Python that will index messages using a `SentenceTransformer` embedding.

## Usage

### Configuration

Configuratio requires setting up a Discord bot.
After that, set the `BOT_TOKEN` environment variable (e.g. in a local `.env` file).

Finally, invite the bot to your server using the OAuth2 URL generated by the Discord Developer Portal.

You can also set which embeddings to use using the `HF_EMBEDDING_MODEL` environment variable, e.g. setting it to `deutsche-telekom/gbert-large-paraphrase-cosine` will use a German BERT model.

### with Docker

```bash
docker compose up -d --build
```

### locally

```bash
# create environment with (micro)mamba/conda
micromamba env create -f environment.yml

# activate environment
micromamba activate discord-bot

# install package
pip install -e .

# run bot
python -m discord-embed-bot
```

:warning: Note that the first usage might take a few minutes, because the model needs to be downloaded.
The volume mapping in the `docker-compose.yml` file is set up to cache the huggingface models, though.
