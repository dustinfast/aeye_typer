/////////////////////////////////////////////////////////////////////////////
// Misc application level helpers
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

#ifndef APP_H
#define APP_H

#include <stdio.h>
#include <iostream>
#include <map>

#include <yaml-cpp/yaml.h>

using namespace std;


#define ANSII_ESC_BOLD "\033[1m"
#define ANSII_ESC_OK "\033[92m"
#define ANSII_ESC_WARNING "\033[38;5;214m"
#define ANSII_ESC_ERROR "\033[91m"
#define ANSII_ESC_ENDCOLOR "\033[0m"

#define CONFIG_FILE_PATH "/opt/app/src/config.yaml"

// Returns the application's config elements as a map.
map<string, string> app_config() {
    YAML::Node config = YAML::LoadFile(CONFIG_FILE_PATH);
    map<string, string> config_map;

    for(YAML::const_iterator it=config.begin();it!=config.end();++it) 
        config_map[it->first.as<string>()] = it->second.as<string>();

    return config_map;
}

// Prints the given string to stdout, formatted as an info str.
void info(const char *s) {
    printf("%sINFO:%s %s", ANSII_ESC_OK, ANSII_ESC_ENDCOLOR, s);
}

// Prints the given string to stdout, formatted as a warning.
void warn(const char *s) {
    printf("%sWARN:%s %s", ANSII_ESC_WARNING, ANSII_ESC_ENDCOLOR, s);
}

// Prints the given string to stdout, formatted as an error.
void error(const char *s) {
    printf("%sERROR:%s %s", ANSII_ESC_ERROR, ANSII_ESC_ENDCOLOR, s);
}

// Prints the given string to stdout in bold.
void bold(const char *s) {
    printf("%s%s%s", ANSII_ESC_BOLD, s, ANSII_ESC_ENDCOLOR);
}


#endif // Top-level include guard
