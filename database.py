import mysql.connector
from mysql.connector import Error
import hashlib


DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "space_invaders_patalinghog_db"
}


def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as error:
        print("MySQL Error:", error)

    return None


def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def initialize_economy():
    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            ALTER TABLE players
            ADD COLUMN IF NOT EXISTS coins INT NOT NULL DEFAULT 0
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS owned_ships (
                id INT AUTO_INCREMENT PRIMARY KEY,
                player_id INT NOT NULL,
                ship_name VARCHAR(100) NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active TINYINT(1) NOT NULL DEFAULT 0,
                UNIQUE KEY unique_player_ship (player_id, ship_name),
                CONSTRAINT fk_owned_ships_player
                FOREIGN KEY (player_id)
                REFERENCES players(id)
                ON DELETE CASCADE
            )
            """
        )

        connection.commit()
        return True

    except Error as error:
        print("Economy initialization error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def register_player(username, email, password):

    connection = get_connection()

    if connection is None:
        return None

    cursor = connection.cursor()

    try:
        username = username.strip()
        email = email.strip().lower()
        password = password.strip()

        if not username or not email or not password:
            return None

        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE username = %s
            """,
            (username,)
        )

        if cursor.fetchone():
            return None

        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE email = %s
            """,
            (email,)
        )

        if cursor.fetchone():
            return None

        hashed_password = hash_password(password)

        cursor.execute(
            """
            INSERT INTO players
            (
                username,
                email,
                password,
                high_score,
                profile_picture,
                total_games,
                total_score
            )
            VALUES
            (
                %s,
                %s,
                %s,
                0,
                NULL,
                0,
                0
            )
            """,
            (
                username,
                email,
                hashed_password
            )
        )

        connection.commit()

        player_id = cursor.lastrowid

        return player_id

    except Error as error:
        print("Register error:", error)
        connection.rollback()
        return None

    finally:
        cursor.close()
        connection.close()


def login_player(username, password):

    connection = get_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        username = username.strip()
        password = password.strip()

        hashed_password = hash_password(password)

        query = """
        SELECT
            id,
            username,
            email,
            high_score,
            profile_picture,
            total_games,
            total_score,
            COALESCE(coins, 0) AS coins,
            created_at
        FROM players
        WHERE
            (
                username = %s
                OR email = %s
            )
            AND password = %s
        """

        cursor.execute(
            query,
            (
                username,
                username.lower(),
                hashed_password
            )
        )

        return cursor.fetchone()

    except Error as error:
        print("Login error:", error)
        return None

    finally:
        cursor.close()
        connection.close()


def get_player(player_id):

    connection = get_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                username,
                email,
                high_score,
                profile_picture,
                total_games,
                total_score,
                COALESCE(coins, 0) AS coins,
                created_at
            FROM players
            WHERE id = %s
            """,
            (player_id,)
        )

        return cursor.fetchone()

    except Error as error:
        print("Profile error:", error)
        return None

    finally:
        cursor.close()
        connection.close()


def update_profile(player_id, username, email):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        username = username.strip()
        email = email.strip().lower()

        if not username or not email:
            return False

        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE username = %s
            AND id != %s
            """,
            (
                username,
                player_id
            )
        )

        if cursor.fetchone():
            return False

        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE email = %s
            AND id != %s
            """,
            (
                email,
                player_id
            )
        )

        if cursor.fetchone():
            return False

        cursor.execute(
            """
            UPDATE players
            SET
                username = %s,
                email = %s
            WHERE id = %s
            """,
            (
                username,
                email,
                player_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Error as error:
        print("Update profile error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def update_profile_picture(player_id, picture_path):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE players
            SET profile_picture = %s
            WHERE id = %s
            """,
            (
                picture_path,
                player_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Error as error:
        print("Profile picture error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def update_password(player_id, new_password):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        new_password = new_password.strip()

        if len(new_password) < 6:
            return False

        hashed_password = hash_password(new_password)

        cursor.execute(
            """
            UPDATE players
            SET password = %s
            WHERE id = %s
            """,
            (
                hashed_password,
                player_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Error as error:
        print("Password update error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def save_score(player_id, score):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE id = %s
            """,
            (player_id,)
        )

        if cursor.fetchone() is None:
            return False

        cursor.execute(
            """
            INSERT INTO scores
            (
                player_id,
                score
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                player_id,
                score
            )
        )

        cursor.execute(
            """
            UPDATE players
            SET
                high_score = GREATEST(
                    high_score,
                    %s
                ),
                total_games = total_games + 1,
                total_score = total_score + %s
            WHERE id = %s
            """,
            (
                score,
                score,
                player_id
            )
        )

        connection.commit()

        return True

    except Error as error:
        print("Score error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def get_leaderboard():

    connection = get_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                username,
                profile_picture,
                high_score,
                COALESCE(total_games, 0) AS total_games,
                COALESCE(total_score, 0) AS total_score,
                COALESCE(coins, 0) AS coins
            FROM players
            ORDER BY high_score DESC
            LIMIT 20
            """
        )

        return cursor.fetchall()

    except Error as error:
        print("Leaderboard error:", error)
        return []

    finally:
        cursor.close()
        connection.close()


def get_player_scores(player_id):

    connection = get_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                score,
                created_at
            FROM scores
            WHERE player_id = %s
            ORDER BY score DESC
            """,
            (player_id,)
        )

        return cursor.fetchall()

    except Error as error:
        print("Score history error:", error)
        return []

    finally:
        cursor.close()
        connection.close()


def delete_player(player_id):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM scores
            WHERE player_id = %s
            """,
            (player_id,)
        )

        cursor.execute(
            """
            DELETE FROM owned_ships
            WHERE player_id = %s
            """,
            (player_id,)
        )

        cursor.execute(
            """
            DELETE FROM players
            WHERE id = %s
            """,
            (player_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    except Error as error:
        print("Delete player error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def username_exists(username):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        username = username.strip()

        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE username = %s
            """,
            (username,)
        )

        return cursor.fetchone() is not None

    except Error as error:
        print("Username check error:", error)
        return False

    finally:
        cursor.close()
        connection.close()


def email_exists(email):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        email = email.strip().lower()

        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE email = %s
            """,
            (email,)
        )

        return cursor.fetchone() is not None

    except Error as error:
        print("Email check error:", error)
        return False

    finally:
        cursor.close()
        connection.close()


def get_balance(player_id):

    connection = get_connection()

    if connection is None:
        return 0

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(coins, 0)
            FROM players
            WHERE id = %s
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        if result:
            return int(result[0])

        return 0

    except Error as error:
        print("Balance error:", error)
        return 0

    finally:
        cursor.close()
        connection.close()


def add_coins(player_id, amount):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        amount = int(amount)

        if amount <= 0:
            return False

        cursor.execute(
            """
            UPDATE players
            SET coins = COALESCE(coins, 0) + %s
            WHERE id = %s
            """,
            (
                amount,
                player_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except (Error, ValueError) as error:
        print("Add coins error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def spend_coins(player_id, amount):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        amount = int(amount)

        if amount <= 0:
            return False

        cursor.execute(
            """
            UPDATE players
            SET coins = coins - %s
            WHERE id = %s
            AND COALESCE(coins, 0) >= %s
            """,
            (
                amount,
                player_id,
                amount
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except (Error, ValueError) as error:
        print("Spend coins error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def get_owned_ships(player_id):

    connection = get_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                ship_name,
                purchased_at,
                active
            FROM owned_ships
            WHERE player_id = %s
            ORDER BY purchased_at ASC
            """,
            (player_id,)
        )

        return cursor.fetchall()

    except Error as error:
        print("Owned ships error:", error)
        return []

    finally:
        cursor.close()
        connection.close()


def owns_ship(player_id, ship_name):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM owned_ships
            WHERE player_id = %s
            AND ship_name = %s
            """,
            (
                player_id,
                ship_name
            )
        )

        return cursor.fetchone() is not None

    except Error as error:
        print("Ship ownership error:", error)
        return False

    finally:
        cursor.close()
        connection.close()


def buy_ship(player_id, ship_name, price):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        price = int(price)

        if price < 0 or not ship_name:
            return False

        cursor.execute(
            """
            SELECT id
            FROM owned_ships
            WHERE player_id = %s
            AND ship_name = %s
            """,
            (
                player_id,
                ship_name
            )
        )

        if cursor.fetchone():
            return False

        cursor.execute(
            """
            SELECT COALESCE(coins, 0)
            FROM players
            WHERE id = %s
            """,
            (player_id,)
        )

        balance = cursor.fetchone()

        if balance is None:
            return False

        if int(balance[0]) < price:
            return False

        cursor.execute(
            """
            UPDATE players
            SET coins = coins - %s
            WHERE id = %s
            """,
            (
                price,
                player_id
            )
        )

        cursor.execute(
            """
            INSERT INTO owned_ships
            (
                player_id,
                ship_name,
                active
            )
            VALUES
            (
                %s,
                %s,
                0
            )
            """,
            (
                player_id,
                ship_name
            )
        )

        connection.commit()

        return True

    except (Error, ValueError) as error:
        print("Buy ship error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def set_active_ship(player_id, ship_name):

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM owned_ships
            WHERE player_id = %s
            AND ship_name = %s
            """,
            (
                player_id,
                ship_name
            )
        )

        if cursor.fetchone() is None:
            return False

        cursor.execute(
            """
            UPDATE owned_ships
            SET active = 0
            WHERE player_id = %s
            """,
            (player_id,)
        )

        cursor.execute(
            """
            UPDATE owned_ships
            SET active = 1
            WHERE player_id = %s
            AND ship_name = %s
            """,
            (
                player_id,
                ship_name
            )
        )

        connection.commit()

        return True

    except Error as error:
        print("Active ship error:", error)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def get_active_ship(player_id):

    connection = get_connection()

    if connection is None:
        return None

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT ship_name
            FROM owned_ships
            WHERE player_id = %s
            AND active = 1
            LIMIT 1
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    except Error as error:
        print("Active ship error:", error)
        return None

    finally:
        cursor.close()
        connection.close()


def test_connection():

    connection = get_connection()

    if connection:
        connection.close()
        return True

    return False


if __name__ == "__main__":
    if test_connection():
        print("MySQL CONNECTION SUCCESSFUL")
        initialize_economy()
        print("Economy tables initialized.")
    else:
        print("MySQL CONNECTION FAILED")