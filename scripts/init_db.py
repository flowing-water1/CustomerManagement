from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.config import Settings
from customer_management.db import make_engine, make_session_factory


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    engine = make_engine(settings.database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)


if __name__ == "__main__":
    main()
