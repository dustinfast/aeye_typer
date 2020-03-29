// Misc sqlite helpers
// Author: Dustin Fast, 2020

#include <cstdlib>
#include <cstdio>
#include <iostream>
#include <vector>

#include <sqlite3.h>


using namespace std;


// Opens the specified sqlite db and returns a ptr to it.
static sqlite3* sqlite_get_db(const char *path) {
    sqlite3 *db;
    char *zErrMsg = 0;

    if(sqlite3_open(path, &db)) {
        fprintf(stderr, "ERROR: Failed to open db %s\n", sqlite3_errmsg(db));
        return(0);
    }
    else {
        return db;
    }
}


// Executes the given sql query in the context of the specified DB.
int sqlite_exec(sqlite3 *db, const char *sql_query) {
    char *zErrMsg = 0;

    int rc = sqlite3_exec(db, sql_query, NULL, 0, &zErrMsg);
   
    if(rc != SQLITE_OK) {
        fprintf(stderr, "SQL error on query: %s\n", sql_query);
        fprintf(stderr, " -- %s\n", zErrMsg);
        sqlite3_free(zErrMsg);
        return 0;
    }

    return 1;
}
// Creates a table having the given cols in the given sqlite database.
// If exists_ok is true, the table is dropped if it exists before creation.
// Each element in columns is that cols definition, ex: "NAME TYPE NOT NULL"
int sqlite_create_table(sqlite3 *db, string name, vector<string> columns, bool exists_ok=false) {
    int i = 0;
    string str_query;
    
    // Attempt to drop existing table iff specified
    if (exists_ok)
        str_query = "DROP TABLE IF EXISTS " + name;
        if (!sqlite_exec(db, str_query.c_str()))
            return 0;
    
    // Build the sql query CREATE statement
    str_query = "CREATE TABLE "  + name + "(";

    for (i = 0; i < columns.size(); i++) {
        str_query += columns[i];
        
        if (i < (columns.size() - 1))
            str_query += ",";
    }

    str_query += ");";

    // Create the table
    return sqlite_exec(db, str_query.c_str());
}


void sqlite_create_logtables(sqlite3 *db, bool drop_existing=false) {
    string tbl_name;
    vector<string> tbl_cols;

    // Create Keyboard events table
    tbl_name = "KeyboardEvents";
    tbl_cols.clear();

    tbl_cols.push_back("pkey INT PRIMARY KEY NOT NULL");
    tbl_cols.push_back("event_code INT NOT NULL");
    tbl_cols.push_back("key_id INT NOT NULL");
    tbl_cols.push_back("date_time DATETIME NOT NULL");

    sqlite_create_table(db, tbl_name, tbl_cols, drop_existing);

    // Create Mouse events table
    tbl_name = "MouseBtnEvents";
    tbl_cols.clear();

    tbl_cols.push_back("pkey INT PRIMARY KEY NOT NULL");
    tbl_cols.push_back("event_code INT NOT NULL");
    tbl_cols.push_back("btn_id INT NOT NULL");
    tbl_cols.push_back("date_time DATETIME NOT NULL");

    sqlite_create_table(db, tbl_name, tbl_cols, drop_existing);
}