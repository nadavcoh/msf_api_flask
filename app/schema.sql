DROP TABLE IF EXISTS My_Users;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS Roster;
DROP TABLE IF EXISTS Teams;

CREATE TABLE My_Users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT NOT NULL,
  frame TEXT NOT NULL,
  gold TEXT,
  inventory TEXT,
  roster TEXT
);

-- https://www.w3schools.com/sql/sql_primarykey.asp
-- https://www.w3schools.com/sql/sql_foreignkey.asp
-- https://www.sqlite.org/foreignkeys.html
CREATE TABLE Inventory (
  user_id TEXT NOT NULL,
  item TEXT NOT NULL,
  quantity INT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES My_Users(id),
  CONSTRAINT PK_Inventory PRIMARY KEY (user_id, item)
);

CREATE TABLE Roster (
  user_id TEXT NOT NULL,
  char_id TEXT NOT NULL,
  tier INT NOT NULL,
  slots TEXT NOT NULL,
  yellow INT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES My_Users(id),
  CONSTRAINT PK_Roster PRIMARY KEY (user_id, char_id)
);

CREATE TABLE Teams (
  user_id TEXT NOT NULL,
  team_id SERIAL PRIMARY KEY,
  name TEXT,
  char1 TEXT,
  char2 TEXT,
  char3 TEXT,
  char4 TEXT,
  char5 TEXT,
  to_tier INT,
  FOREIGN KEY(user_id) REFERENCES My_Users(id)
);