from dataclasses import dataclass
import chromadb
import os
from textwrap import dedent
from chromadb.utils import embedding_functions

MIN_MSG_LENGTH = 5
MESSAGE_LINK_FORMAT = "https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
MODEL_NAME = os.environ.get("HF_MODEL_NAME", "deutsche-telekom/gbert-large-paraphrase-cosine")


@dataclass
class SearchResult:
    guild_id: int
    channel_id: int
    message_id: int
    message: str


class EmbeddingSearch:
    def __init__(self):
        self.db = chromadb.PersistentClient()
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
        if "messages" in [c.name for c in self.db.list_collections()]:
            self.db.delete_collection("messages")
        self.messages = self.db.create_collection("messages", embedding_function=self.ef)  # type: ignore
        print(f"Using collection {self.messages.name} for documents. Searching with {MODEL_NAME} embeddings.")

    async def search(self, query_str: str, guild_id: int, k: int = 3) -> list[SearchResult]:
        """
        Given a query string show matching messages
        """
        try:
            results = self.messages.query(
                query_texts=[query_str],
                n_results=k,
                where={"guild_id": {"$eq": str(guild_id)}},
            )

            if results.get("documents", None) is not None and results.get("metadatas", None) is not None:
                metadata = results["metadatas"][0]  # type: ignore
                res_docs = results["documents"][0]  # type: ignore
                return [
                    SearchResult(
                        int(m["guild_id"]),
                        int(m["channel_id"]),
                        int(m["message_id"]),
                        d,
                    )
                    for m, d in zip(metadata, res_docs)
                ]

            return []

        except Exception as e:
            print(e)
            return []

    async def build_response(self, results: list[SearchResult]) -> str:
        if not results:
            return "No results found."

        result_list = ""
        for result in results:
            result_list += f"> {result.message} {MESSAGE_LINK_FORMAT.format(guild_id=result.guild_id, channel_id=result.channel_id, message_id=result.message_id)} \n"
            result_list += "---\n"

        return dedent(
            f"""  
                    {result_list}
            """
        )

    async def embed_message(self, message: str, message_id: int, channel_id: int, guild_id: int):
        stripped_msg = message.strip() if message else ""
        if len(stripped_msg) < MIN_MSG_LENGTH:
            return

        self.messages.add(
            ids=[str(message_id)],
            documents=[message],
            metadatas=[
                {
                    "channel_id": str(channel_id),
                    "message_id": str(message_id),
                    "guild_id": str(guild_id),
                }
            ],
        )

    async def batch_embed_messages(
        self,
        messages: list[str],
        message_ids: list[int],
        channel_ids: list[int],
        guild_ids: list[int],
        recreate: bool = True,
    ):
        self.db.delete_collection("messages")
        self.messages = self.db.get_or_create_collection("messages")

        stripped_msgs = [msg.strip() if msg else "" for msg in messages]
        valid_indices = [i for i, msg in enumerate(stripped_msgs) if len(msg) >= MIN_MSG_LENGTH]

        self.messages.add(
            ids=[str(message_ids[i]) for i in valid_indices],
            documents=[messages[i] for i in valid_indices],
            metadatas=[
                {
                    "channel_id": str(channel_ids[i]),
                    "message_id": str(message_ids[i]),
                    "guild_id": str(guild_ids[i]),
                }
                for i in valid_indices
            ],
        )

        return len(valid_indices)
