/**
 * C++ file with syntax errors.
 *
 * This fixture is intentionally broken to test syntax error detection.
 */

#include <iostream>
#include <string>

// Missing semicolon after class definition
class BrokenClass {
 public:
    void method() {
        std::cout << "Test" << std::endl;
    }
}  // Missing semicolon here

// Mismatched braces
void broken_function() {
    if (true) {
        std::cout << "Missing closing brace" << std::endl;
    // Missing closing brace
}

// Invalid function declaration
int another_broken(int x, int y {
    return x + y;
}

// Unmatched template brackets
template<typename T
class BrokenTemplate {
    T value;
};

// Missing return type
broken_return() {
    return 42;
}

// Invalid main
int main( {
    std::cout << "Broken main" << std::endl
    return 0;
}
