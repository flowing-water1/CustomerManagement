from customer_management.db import Base
from customer_management import models  # noqa: F401


def create_schema(engine) -> None:
    Base.metadata.create_all(engine)
