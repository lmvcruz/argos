cmake_minimum_required(VERSION 3.10)
project(WithSubdirectories VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add subdirectory with library
add_subdirectory(lib)

# Add subdirectory with executable
add_subdirectory(app)
