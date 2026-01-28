cmake_minimum_required(VERSION 3.10)
project(HeaderOnlyLib VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Header-only library
add_library(header_lib INTERFACE)
target_include_directories(header_lib INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable using the header-only library
add_executable(example main.cpp)
target_link_libraries(example PRIVATE header_lib)
