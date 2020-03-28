// Misc application level helpers
// Author: Dustin Fast, 2020

#include <iostream>

#include "yaml-cpp/yaml.h"

using namespace std;


#define CONFIG_FILE_PATH "/opt/app/src/_config.yaml"


// Returns the application's config elements as a map.
// ASSUMES: Config file is not multi-tiered.
map<string, string> get_app_config() {
    YAML::Node config = YAML::LoadFile(CONFIG_FILE_PATH);
    map<string, string> config_map;

    for(YAML::const_iterator it=config.begin();it!=config.end();++it) 
        config_map[it->first.as<string>()] = it->second.as<string>();
    
    return config_map;
}