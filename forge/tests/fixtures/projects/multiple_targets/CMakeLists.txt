cmake_minimum_required(VERSION 3.10)
project(MultipleTargets VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Create a library
add_library(math_lib STATIC math_utils.cpp)

# Create first executable
add_executable(app1 app1.cpp)
target_link_libraries(app1 PRIVATE math_lib)

# Create second executable
add_executable(app2 app2.cpp)
target_link_libraries(app2 PRIVATE math_lib)
