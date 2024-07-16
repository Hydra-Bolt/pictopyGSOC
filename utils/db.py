import sqlite3
from typing import List, Dict, Tuple
from utils.fs import deleteFile, pathExist

def connectDB(dbPath: str) -> sqlite3.Connection:
    """Connects to the database at the given path.

    Args:
        dbPath: The path to the database file.

    Returns:
        A sqlite3.Connection object.
    """
    return sqlite3.connect(dbPath)

def createTable(conn: sqlite3.Connection, tableID: str, columns: List[str]) -> None:
    """Creates a table in the database with the given name and columns.

    Args:
        conn: A sqlite3.Connection object.
        tableID: The name of the table to create.
        columns: A list of column names.
    """
    query = f"CREATE TABLE IF NOT EXISTS {tableID} ({', '.join(columns)})"
    executeQuery(conn, query)

def createSchema(conn: sqlite3.Connection, tables: Dict[str, List[str]]) -> None:
    """Creates tables for MEDIA, JUNCTION, and CLASS in the database.

    Args:
        conn: A sqlite3.Connection object.
        tables: A dictionary where each key is a table name and each value is a list of column definitions.
    """
    for tableName, columns in tables.items():
        createTable(conn, tableName, columns)

def executeQuery(conn: sqlite3.Connection, query: str, params: List = ()) -> sqlite3.Cursor:
    """Executes a query on the database.

    Args:
        conn: A sqlite3.Connection object.
        query: The SQL query to execute.
        params: The parameters to be used in the query.

    Returns:
        A sqlite3.Cursor object.        
    """
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor

def closeConnection(conn: sqlite3.Connection) -> None:
    """Closes the connection to the database.

    Args:
        conn: A sqlite3.Connection object.
    """
    conn.commit()
    conn.close()

# NN
def hashExist(conn: sqlite3.Connection, hashValue: str) -> bool:
    """Checks if a hash value exists in the database.

    Args:
        conn: A sqlite3.Connection object.
        hashValue: The hash value to check.

    Returns:
        True if the hash value exists, False otherwise.
    """
    query = "SELECT EXISTS(SELECT 1 FROM MEDIA WHERE hash=?)"
    result = executeQuery(conn, query, [hashValue])
    return result[0][0] == 1

def groupByClass(conn: sqlite3.Connection, hidden: int = 0, fileType: str = "img", groupOf: str = "path") -> Dict[str, List[str]]:
    """Returns paths grouped by classes from the database.

    Args:
        conn: A sqlite3.Connection object.
        hidden: Filter media by hidden status.
        fileType: Filter media by file type ('img' or 'vid').
        groupOf: The column to be grouped.

    Returns:
        dict: A dictionary where each key is a class name and each value is a list of paths.
    """
    if fileType == "any":
        fileTypeCondition = ""
    else:
        fileTypeCondition = "AND i.fileType = ?"

    query = f"""
    SELECT c.class, GROUP_CONCAT(i.{groupOf})
    FROM CLASS c
    JOIN JUNCTION j ON c.classID = j.classID 
    JOIN MEDIA i ON j.mediaID = i.mediaID 
    WHERE i.hidden = ? {fileTypeCondition}
    GROUP BY c.class
    """
    result = {}
    if fileType == "any":
        cursor = executeQuery(conn, query, [hidden])
    else:
        cursor = executeQuery(conn, query, [hidden, fileType])
    
    for row in cursor.fetchall():
        result[row[0]] = row[1].split(',')
    
    return result

def groupByDir(conn: sqlite3.Connection, hidden: int = 0, fileType: str = "img", groupOf: str = "path") -> Dict[str, List[str]]:
    """Returns paths grouped by classes from the database.

    Args:
        conn: A sqlite3.Connection object.
        hidden: Filter media by hidden status.
        fileType: Filter media by file type ('img' or 'vid').
        groupOf: The column to be grouped.

    Returns:
        dict: A dictionary where each key is a class name and each value is a list of paths.
    """
    if fileType == "any":
        fileTypeCondition = ""
    else:
        fileTypeCondition = "AND fileType = ?"

    query = f"""
    SELECT directory, GROUP_CONCAT({groupOf}) 
    FROM MEDIA
    WHERE hidden = ? {fileTypeCondition}
    """
    result = {}
    if fileType == "any":
        cursor = executeQuery(conn, query, [hidden])
    else:
        cursor = executeQuery(conn, query, [hidden, fileType])
    
    for row in cursor.fetchall():
        result[row[0]] = row[1].split(',')
    
    return result

def toggleVisibility(conn: sqlite3.Connection, paths: List[str], hidden: int) -> None:
    """Switch visibility of media by changing value of hidden column.

    Args:
        conn: sqlite3.Connection object.
        paths: A list of paths to switch visibility.
        hidden: The new value of hidden column.
    """
    query = f"UPDATE MEDIA SET hidden=? WHERE path IN ({', '.join('?' * len(paths))})"
    executeQuery(conn, query, [hidden] + paths)

def listByClass(conn: sqlite3.Connection, classes: List[str], hidden: int = 0, groupOf: str = "path") -> List[str]:
    """Returns list of all paths associated with the given classes.

    Args:
        conn: sqlite3.Connection object.
        classes: A list of class names.
        hidden: Filter media by hidden status.
        groupOf: The column to be grouped.

    Returns:
        A list of paths.
    """
    result = []
    groups = groupByClass(conn, hidden, groupOf)
    for class_ in groups:
        if class_ in classes:
            result.extend(groups[class_])
    return result

def hideByClass(conn: sqlite3.Connection, classes: List[str]) -> None:
    """Hides media by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A list of class names.
    """
    toggleVisibility(conn, listByClass(conn, classes, 0), 1)

def unhideByClass(conn: sqlite3.Connection, classes: List[str]) -> None:
    """Unhides media by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A list of class names.
    """
    toggleVisibility(conn, listByClass(conn, classes, 1), 0)

def deleteFromDB(conn: sqlite3.Connection, paths: List[str]) -> None:
    """Deletes related rows from DB. Deletes files by path.

    Args:
        conn: sqlite3.Connection object.
        paths: A list of paths to delete.
    """
    query = f"DELETE FROM MEDIA WHERE path IN ({', '.join('?' * len(paths))})"
    executeQuery(conn, query, paths)
    deleteFile(paths)

def deleteByClass(conn: sqlite3.Connection, classes: List[str]) -> None:
    """Deletes media by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A list of class names.
    """
    deleteFromDB(conn, listByClass(conn, classes))

# def cleanDB(conn: sqlite3.Connection) -> None:
#     """Filter unavailable paths from DB and delete them.
# 
#     Args:
#         conn: sqlite3.Connection object.
#     """
#     query = "SELECT path FROM MEDIA"
#     for path in executeQuery(conn, query):
#         if not pathExist(path[0]):
#             deleteFromDB(conn, path)

def cleanDB(conn: sqlite3.Connection) -> None:
    """Filter and Delete:
    - Unavailable paths from DB 
    - Trash paths older than 30 days

    Args:
        conn: sqlite3.Connection object.
    """
    query = "SELECT path FROM MEDIA"
    paths = []
    for path in executeQuery(conn, query).fetchall():
        if not pathExist(path[0]):
            paths.append(path[0])

    query = """
    SELECT path FROM MEDIA 
    WHERE hidden = -1 
    AND modifiedTime <= DATE('now', '-30 days')
    """
    for path in executeQuery(conn, query).fetchall():
        paths.append(path[0])
    
    if paths:
        print(paths)
        deleteFromDB(conn, paths)

def updateMediaPath(conn, file, fileHash):
    """Updates the path of a media file in the database.

    Args:
        conn: sqlite3.Connection object.
        file: The path to the media file.
        fileHash: The hash value of the media.

    Returns:
        True if the path was updated, False otherwise.
    """
    if executeQuery(conn, "UPDATE MEDIA SET path = ? WHERE hash = ?", [file, fileHash]).rowcount == 0:
        return False
    return True

def insertMedia(conn: sqlite3.Connection, fileHash: str, file: str, directory: str, fileType: str) -> Tuple[int, str, str]:
    """Populates the MEDIA table with the given file information.

    Args:
        conn: sqlite3.Connection object.
        file: The path to the media file.
        fileType: The type of the media file.

    Returns:
        A tuple of mediaID, file, and fileType.

    Note:
        No need to check if mediaID exist in Junction Table.
        updateMediaPath() won't allow older mediaIDs.
    """
    return [executeQuery(conn, "INSERT INTO MEDIA(hash, path, directory, fileType, hidden) VALUES(?, ?, ?, ?, 0)", [fileHash, file, directory, fileType]).lastrowid, file, fileType]

def insertClassRelation(conn: sqlite3.Connection, mediaClass: List[str], mediaID) -> None:
    """Populates the JUNCTION table with the given class information.

    Args:
        conn: sqlite3.Connection object.
        mediaClass: A list of class names.
        mediaID: The ID of the media file.
    """
    for className in mediaClass:
        try:
            classID = executeQuery(conn, "INSERT INTO CLASS(class) VALUES(?)", [className]).lastrowid
        except sqlite3.IntegrityError:
            classID = executeQuery(conn, "SELECT classID FROM CLASS WHERE class = ?", [className]).fetchall()[0][0]
        
        executeQuery(conn, "INSERT OR IGNORE INTO JUNCTION(mediaID, classID) VALUES(?, ?)", [mediaID, classID])

def moveToTrash(conn: sqlite3.Connection, paths: List[str]) -> None:
    """Move images to trash by setting the hidden column to -1.

    Args:
        conn: sqlite3.Connection object.
        paths: A list of paths to move to trash.
    """
    query = f"""
        UPDATE MEDIA 
        SET hidden = -1,
        modifiedTime = CURRENT_TIMESTAMP
        WHERE path IN ({', '.join('?' * len(paths))})
    """
    executeQuery(conn, query, paths)