DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS inventory;

CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT NOT NULL,
  frame TEXT NOT NULL,
  gold TEXT,
  inventory TEXT
);

-- https://www.w3schools.com/sql/sql_primarykey.asp
-- https://www.w3schools.com/sql/sql_foreignkey.asp
-- https://www.sqlite.org/foreignkeys.html
CREATE TABLE Inventory (
  user_id TEXT NOT NULL,
  item TEXT NOT NULL,
  quantity INT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES user(id),
  CONSTRAINT PK_Inventory PRIMARY KEY (user_id, item)
);