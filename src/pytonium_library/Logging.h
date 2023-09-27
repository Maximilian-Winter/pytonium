//
// Created by maxim on 27.09.2023.
//

#ifndef PYTONIUM_LOGGING_H
#define PYTONIUM_LOGGING_H

#include <iostream>
#include <fstream>
#include <string>

class Logging {
public:
    // Constructor
    Logging(std::string path) : log_file_path(std::move(path)) {
        // Open the file in append mode
        log_stream.open(log_file_path, std::ios::app);
        if (!log_stream.is_open()) {
            std::cerr << "Failed to open log file: " << log_file_path << std::endl;
        }
    }

    // Destructor
    ~Logging() {
        if (log_stream.is_open()) {
            log_stream.close();
        }
    }

    // Append a log message to the file
    void appendLog(const std::string &message) {
        if (log_stream.is_open()) {
            log_stream << message << std::endl;
        } else {
            std::cerr << "Log stream is not open. Could not log message." << std::endl;
        }
    }

private:
    std::string log_file_path;
    std::ofstream log_stream;
};
#endif //PYTONIUM_LOGGING_H
