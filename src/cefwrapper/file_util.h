//
// Created by maxim on 19.10.2022.
//

#ifndef CEF_WRAPPER_FILE_UTIL_H
#define CEF_WRAPPER_FILE_UTIL_H
#include <filesystem>
#include <fstream>

/**
 * Returns an std::string which represents the raw bytes of the file.
 *
 * @param path The path to the file.
 * @return The content of the file as it resides on the disk - byte by byte.
 */
[[nodiscard]] static std::string
file_contents_binary(const std::filesystem::path &path) {
  // Sanity check
  if (!std::filesystem::is_regular_file(path))
    return {};

  // Open the file
  // Note that we have to use binary mode as we want to return a string
  // representing matching the bytes of the file on the file system.
  std::ifstream file(path, std::ios::in | std::ios::binary);
  if (!file.is_open())
    return {};

  // Read contents
  std::string content{std::istreambuf_iterator<char>(file),
                      std::istreambuf_iterator<char>()};

  // Close the file
  file.close();

  return content;
}
#endif // CEF_WRAPPER_FILE_UTIL_H
