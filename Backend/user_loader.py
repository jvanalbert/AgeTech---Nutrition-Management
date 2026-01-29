# Backend/user_loader.py
import json

USER_DATA_FILE = "data/sample_user.json"


def load_user_data(path=USER_DATA_FILE):
    """Load full user JSON (elderly + caretakers)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_user_data(data, path=USER_DATA_FILE):
    """Save full user JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_elderly_users(path=USER_DATA_FILE):
    """Return only elderly users (for displays / planning)."""
    data = load_user_data(path)
    return data.get("elderly_users", [])


def username_exists(username, path=USER_DATA_FILE):
    """Check if username exists across ALL users."""
    data = load_user_data(path)

    for e in data.get("elderly_users", []):
        if e["account"]["username"] == username:
            return True

    for c in data.get("caretaker_users", []):
        if c["account"]["username"] == username:
            return True

    return False

def load_users(path=USER_DATA_FILE):
    """Return all users (elderly + caretaker) in a single list."""
    data = load_user_data(path)
    return data.get("elderly_users", []) + data.get("caretaker_users", [])

def load_elderly_users_with_caretakers(path=USER_DATA_FILE):
    """
    Return elderly users with their caretaker object attached
    as 'caretaker' key.
    """
    data = load_user_data(path)
    caretakers_by_id = {c['id']: c for c in data.get("caretaker_users", [])}

    elderly_users = []
    for e in data.get("elderly_users", []):
        user_copy = e.copy()
        caretaker_id = e.get("caretaker_id")
        if caretaker_id and caretaker_id in caretakers_by_id:
            user_copy["caretaker"] = caretakers_by_id[caretaker_id]
        else:
            user_copy["caretaker"] = None
        elderly_users.append(user_copy)

    return elderly_users

