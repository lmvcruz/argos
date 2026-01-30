/**
 * C++ file with static analysis issues.
 *
 * This fixture contains potential bugs detectable by static analyzers.
 */

#include <iostream>
#include <string>
#include <vector>

// Potential null pointer dereference
void null_pointer_issue() {
    int* ptr = nullptr;
    *ptr = 42;  // Dereferencing null pointer
}

// Memory leak
void memory_leak() {
    int* data = new int[100];
    // Missing delete[] data;
}

// Uninitialized variable
int uninitialized_variable() {
    int result;  // Not initialized
    return result;  // Reading uninitialized value
}

// Array out of bounds
void array_bounds_issue() {
    int arr[10];
    arr[15] = 42;  // Out of bounds access
}

// Use after delete
void use_after_delete() {
    int* ptr = new int(42);
    delete ptr;
    *ptr = 100;  // Use after delete
}

// Double delete
void double_delete() {
    int* ptr = new int(42);
    delete ptr;
    delete ptr;  // Double delete
}

// Infinite loop
void infinite_loop() {
    while (true) {
        // No break condition
    }
}

// Division by zero
int division_by_zero(int x) {
    int divisor = 0;
    return x / divisor;  // Division by zero
}

// Unused variable
void unused_variable() {
    int unused = 42;
    std::cout << "Function called" << std::endl;
}

// Unreachable code
int unreachable_code(int x) {
    return x * 2;
    x += 1;  // Unreachable
}

int main() {
    return 0;
}
