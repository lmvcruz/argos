add_library(string_lib STATIC string_utils.cpp)
target_include_directories(string_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
