import sqlite3


def init_db(path):
    def check_table(cursor, tablename):
        query = "SELECT name FROM sqlite_master WHERE type='table' and name=?"
        return cursor.execute(query, (tablename,)).fetchone()

    with sqlite3.connect(path) as conn:
        c = conn.cursor()
        if not check_table(c, "Games"):
            c.execute("CREATE TABLE Games\n"
                      "            (gameid INTEGER PRIMARY KEY ASC,\n"
                      "             gamename TEXT,\n"
                      "             UNIQUE (gamename)"
                      "             )")
        if not check_table(c, "Deds"):
            c.execute("CREATE TABLE Deds\n"
                      "            (dedid INTEGER PRIMARY KEY ASC,\n"
                      "             gameid INTEGER, \n"
                      "             description text,\n"
                      "             FOREIGN KEY (gameid) REFERENCES Games(gameid)\n"
                      "             )")
        if not check_table(c, "Info"):
            c.execute("CREATE TABLE Info\n"
                      "             (infoid INTEGER PRIMARY KEY ASC,\n"
                      "              infokey TEXT,\n"
                      "              strval TEXT,\n"
                      "              intval INTEGER,\n"
                      "              UNIQUE (infokey)\n"
                      "             )")


def get_deds(path, game=""):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if "" == game:
            _game = c.execute('SELECT strval FROM Info WHERE infokey="CurrentGame"').fetchone()["strval"]
        else:
            _game = game
        dedcnt = c.execute('SELECT COUNT(*) as Cnt FROM Deds d\n'
                           '                JOIN Games g on g.gameid = d.gameid\n'
                           'WHERE g.gamename=?', (_game,)).fetchone()["Cnt"]
        print(dedcnt)
        if 0 == dedcnt:
            msg = f"No Deds found for {_game}."
        else:
            msg = f"Deds count for {_game} is: {dedcnt}"
        return msg


def add_ded(path, game, desc):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        _gameid = None
        if "" == game:
            res = c.execute('SELECT intval, strval FROM Info\n'
                                'WHERE infokey="CurrentGame"').fetchone()
            _gameid = res["intval"]
            game = res["strval"]
        else:
            res = c.execute('SELECT gameid FROM Games\n'
                            'WHERE gamename = ?', (game,)).fetchone()
            if res:
                _gameid = res["gameid"]

        if _gameid:
            if not desc:
                _desc = "No ded infos."
            else:
                _desc = desc
            c.execute('INSERT INTO Deds\n'
                      '(gameid, description)'
                      'VALUES (?, ?)', (_gameid, _desc))
            conn.commit()
            newcnt = get_deds(path, game)
            msg = f"Added ded to {game}\nDed Count: {newcnt}"
        else:
            msg = f"Deds for {game} are not tracked."
        return msg


def add_game(path, game):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        num = c.execute('INSERT OR IGNORE INTO Games (gamename)\n'
                        'VALUES (?)', (game,)).rowcount
        conn.commit()
        if num > 0:
            return f"Now tracking deds for {game}"
        else:
            return f"Already tracking deds for {game}"


def set_current(path, game):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("INSERT INTO INFO\n"
                  "(infokey)\n"
                  "SELECT 'CurrentGame'\n"
                  "WHERE NOT EXISTS (SELECT 1 FROM INFO WHERE infokey = 'CurrentGame')\n")
        conn.commit()
        res = c.execute("SELECT gameid\n"
                        "FROM Games\n"
                        "WHERE gamename = ?", (game,)).fetchone()
        if res:
            gameid = res["gameid"]
        else:
            return f"Game {game} is not tracked."

        c.execute("UPDATE INFO\n"
                  "SET strval = ?,\n"
                  "    intval = ?\n", (game, gameid))

        conn.commit()
        return f"{game} is now the current game!"
