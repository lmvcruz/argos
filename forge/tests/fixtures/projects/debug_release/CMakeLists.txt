cmake_minimum_required(VERSION 3.10)
project(DebugRelease VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set default build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Print build type so Forge can detect it
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

add_executable(build_type_app main.cpp)

# Add compile definitions based on build type
target_compile_definitions(build_type_app PRIVATE
    $<$<CONFIG:Debug>:DEBUG_BUILD>
    $<$<CONFIG:Release>:RELEASE_BUILD>
)
