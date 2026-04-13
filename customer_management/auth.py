ACTOR_TYPE_KEY = "actor_type"
ACTOR_ID_KEY = "actor_id"
ACTOR_NAME_KEY = "actor_name"


def set_authenticated_actor(session_state, *, actor_type: str, actor_id: int, actor_name: str):
    session_state[ACTOR_TYPE_KEY] = actor_type
    session_state[ACTOR_ID_KEY] = actor_id
    session_state[ACTOR_NAME_KEY] = actor_name


def clear_authenticated_actor(session_state):
    session_state.pop(ACTOR_TYPE_KEY, None)
    session_state.pop(ACTOR_ID_KEY, None)
    session_state.pop(ACTOR_NAME_KEY, None)


def get_authenticated_actor(session_state):
    actor_type = session_state.get(ACTOR_TYPE_KEY)
    actor_id = session_state.get(ACTOR_ID_KEY)
    actor_name = session_state.get(ACTOR_NAME_KEY)
    if actor_type is None or actor_id is None or actor_name is None:
        return None
    return {
        "actor_type": actor_type,
        "actor_id": actor_id,
        "actor_name": actor_name,
    }
