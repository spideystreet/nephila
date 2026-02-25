from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class PipelineSettings(BaseSettings):

    # PostgreSQL
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # ChromaDB
    chroma_host: str
    chroma_port: int

    # Local paths
    bronze_dir: Path = Path("data/bronze")

    # Official data source URLs
    bdpm_base_url: str = "https://base-donnees-publique.medicaments.gouv.fr/telechargement.php"
    ansm_thesaurus_page_url: str = (
        "https://ansm.sante.fr/documents/consultation/thesaurus-des-interactions-medicamenteuses"
    )

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
