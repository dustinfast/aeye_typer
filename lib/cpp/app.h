// Misc application level helpers
// Author: Dustin Fast, 2020

#include <cstdlib>
#include <cstdio>
#include <iostream>

#include <sqlite3.h>

#include "yaml-cpp/yaml.h"

using namespace std;


#define CONFIG_FILE_PATH "/opt/app/src/_config.yaml"


// Returns the application's config elements as a map.
// ASSUMES: No nested elements exist in the config file.
static map<string, string> get_app_config() {
    YAML::Node config = YAML::LoadFile(CONFIG_FILE_PATH);
    map<string, string> config_map;

    for(YAML::const_iterator it=config.begin();it!=config.end();++it) 
        config_map[it->first.as<string>()] = it->second.as<string>();
    
    return config_map;
}


// Opens the specified sqlite db and returns a ptr to it.
sqlite3* get_sqlite_db(const char *path) {
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
