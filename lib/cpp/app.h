// Misc application level helpers
// Author: Dustin Fast, 2020

#include <cstdlib>
#include <cstdio>
#include <iostream>
#include <map>

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

// Maps numpad keycodess to their non-numpad keycode equivelant based on
// numlock status.
static void map_numpad_keys(unsigned int *keycode, bool numlock_on) {
    if (numlock_on) {
        switch(*keycode) {
            case 90: *keycode = 19; break;  // 0
            case 87: *keycode = 10; break;  // 1
            case 88: *keycode = 11; break;  // 2
            case 89: *keycode = 12; break;  // 3 
            case 83: *keycode = 13; break;  // 4 
            case 84: *keycode = 14; break;  // 5 
            case 85: *keycode = 15; break;  // 6 
            case 79: *keycode = 16; break;  // 7 
            case 80: *keycode = 17; break;  // 8 
            case 81: *keycode = 18; break;  // 9 
            case 91: *keycode = 60; break;  // .
            default:
                break; 
        }
    } else {
        switch(*keycode) {
            case 79: *keycode = 110; break;  // Home
            case 87: *keycode = 115; break;  // End
            case 81: *keycode = 112; break;  // PgUp
            case 89: *keycode = 117; break;  // PgDwn
            case 83: *keycode = 113; break;  // l_arrow
            case 85: *keycode = 114; break;  // r_arrow
            case 80: *keycode = 111; break;  // u_arrow
            case 88: *keycode = 116; break;  // d_arrow
            case 90: *keycode = 118; break;  // Ins
            case 91: *keycode = 119; break;  // Del
            default:
                break; 
        }
    }
} 