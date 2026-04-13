import streamlit as st

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.db import make_engine, make_session_factory


FLASH_MESSAGE_KEY = "flash_message"


def set_flash(session_state, message: str, *, level: str = "success"):
    session_state[FLASH_MESSAGE_KEY] = {"message": message, "level": level}


def render_flash(session_state):
    flash = session_state.pop(FLASH_MESSAGE_KEY, None)
    if flash is None:
        return
    level = flash["level"]
    if level == "error":
        st.error(flash["message"])
    elif level == "warning":
        st.warning(flash["message"])
    else:
        st.success(flash["message"])


@st.cache_resource
def get_session_factory(database_url: str):
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
    return session_factory
