import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "player_economy.json")
DEFAULT_SHIP = "starter"


def _read_data():
    if not os.path.isfile(DATA_PATH):
        return {}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_data(data):
    temp_path = DATA_PATH + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
        os.replace(temp_path, DATA_PATH)
        return True
    except Exception:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return False


def _key(player_id):
    return str(player_id) if player_id is not None else "guest"


def _database_player(player_id):
    if player_id is None:
        return None
    try:
        import database
        getter = getattr(database, "get_player", None)
        if callable(getter):
            return getter(player_id)
    except Exception:
        pass
    return None


def _database_set_coins(player_id, value):
    if player_id is None:
        return False
    try:
        import database
        for name in ("update_coins", "set_coins", "save_coins"):
            saver = getattr(database, name, None)
            if not callable(saver):
                continue
            try:
                result = saver(player_id, int(value))
            except TypeError:
                result = saver(player_id, coins=int(value))
            return result is not False
    except Exception:
        pass
    return False


def get_coins(player_id, default=0):
    player = _database_player(player_id)
    if isinstance(player, dict) and player.get("coins") is not None:
        try:
            value = max(0, int(float(player.get("coins", 0))))
            data = _read_data()
            record = data.setdefault(_key(player_id), {})
            record["coins"] = value
            _write_data(data)
            return value
        except Exception:
            pass

    data = _read_data()
    record = data.get(_key(player_id), {})
    try:
        return max(0, int(float(record.get("coins", default))))
    except Exception:
        return max(0, int(default))


def set_coins(player_id, value):
    value = max(0, int(value))
    data = _read_data()
    record = data.setdefault(_key(player_id), {})
    record["coins"] = value
    _write_data(data)
    _database_set_coins(player_id, value)
    return value


def add_coins(player_id, amount):
    amount = max(0, int(amount))
    if amount == 0:
        return get_coins(player_id)
    return set_coins(player_id, get_coins(player_id) + amount)


def spend_coins(player_id, amount):
    amount = max(0, int(amount))
    current = get_coins(player_id)
    if current < amount:
        return False, current
    new_balance = set_coins(player_id, current - amount)
    return True, new_balance


def get_owned_ships(player_id):
    player = _database_player(player_id)
    if isinstance(player, dict):
        raw = player.get("owned_ships")
        if raw:
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = [raw]
            if isinstance(raw, (list, tuple, set)):
                ships = list(dict.fromkeys(str(x) for x in raw if str(x).strip()))
                if ships:
                    data = _read_data()
                    data.setdefault(_key(player_id), {})["owned_ships"] = ships
                    _write_data(data)
                    return ships

    data = _read_data()
    record = data.setdefault(_key(player_id), {})
    raw = record.get("owned_ships", [DEFAULT_SHIP])
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = [raw]
    if not isinstance(raw, list):
        raw = [DEFAULT_SHIP]
    ships = list(dict.fromkeys(str(x) for x in raw if str(x).strip()))
    if not ships:
        ships = [DEFAULT_SHIP]
    record["owned_ships"] = ships
    _write_data(data)
    return ships


def is_ship_owned(player_id, ship_id):
    return str(ship_id) in get_owned_ships(player_id)


def own_ship(player_id, ship_id):
    ship_id = str(ship_id).strip()
    if not ship_id:
        return False
    ships = get_owned_ships(player_id)
    if ship_id in ships:
        return True
    ships.append(ship_id)
    data = _read_data()
    data.setdefault(_key(player_id), {})["owned_ships"] = ships
    _write_data(data)
    return True


def buy_ship(player_id, ship_id, price):
    ship_id = str(ship_id).strip()
    price = max(0, int(price))
    if is_ship_owned(player_id, ship_id):
        return False, "ALREADY OWNED", get_coins(player_id)
    success, balance = spend_coins(player_id, price)
    if not success:
        return False, "NOT ENOUGH COINS", balance
    own_ship(player_id, ship_id)
    return True, "PURCHASED", balance


def delete_player_data(player_id):
    key = _key(player_id)
    data = _read_data()
    if key in data:
        data.pop(key, None)
        _write_data(data)
        return True
    return False
