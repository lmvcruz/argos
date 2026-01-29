cmake_minimum_required(VERSION 3.15)
project(HelloForge VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Main executable
add_executable(hello src/main.cpp)

# Library
add_library(greeter src/greeter.cpp)
target_include_directories(greeter PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

# Link library to executable
target_link_libraries(hello PRIVATE greeter)
