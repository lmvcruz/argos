#include "greeter.h"
#include <sstream>

std::string Greeter::greet(const std::string& name) {
    // Simulate some work
    std::stringstream ss;
    for (int i = 0; i < 10000; ++i) {
        ss << "Hello, " << name << "! ";
    }
    return ss.str();
}
