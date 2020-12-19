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
#include <yaml-cpp/yaml.h>

using namespace std;


#define CONFIG_FILE_PATH "/opt/app/src/config.yaml"


// Load the application's config from file (Usage ex: APP_CFG[s].as<string>())
// TODO: File load exception handling
YAML::Node APP_CFG = YAML::LoadFile(CONFIG_FILE_PATH);


// Prints the given string to stdout, formatted as an info str.
void info(const char *s) {
    cout << APP_CFG["ANSII_ESC_OK"].as<string>();
    cout << "INFO: " << APP_CFG["ANSII_ESC_ENDCOLOR"].as<string>() << s ;
    // printf("%sINFO:%s %s", ANSII_ESC_OK, ANSII_ESC_ENDCOLOR, s);
}

// Prints the given string to stdout, formatted as a warning.
void warn(const char *s) {
    cout << APP_CFG["ANSII_ESC_WARNING"].as<string>();
    cout << "WARN: " << APP_CFG["ANSII_ESC_ENDCOLOR"].as<string>() << s ;
}

// Prints the given string to stdout, formatted as an error.
void error(const char *s) {
    cout << APP_CFG["ANSII_ESC_ERROR"].as<string>();
    cout << "ERROR: " << APP_CFG["ANSII_ESC_ENDCOLOR"].as<string>() << s ;
}

// Prints the given string to stdout in bold.
void bold(const char *s) {
    cout << APP_CFG["ANSII_ESC_BOLD"].as<string>();
    cout << s << APP_CFG["ANSII_ESC_ENDCOLOR"].as<string>();
}


#endif // Top-level include guard
