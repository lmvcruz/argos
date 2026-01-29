#include <iostream>
#include <chrono>
#include "greeter.h"

int main() {
    Greeter greeter;

    auto start = std::chrono::high_resolution_clock::now();
    std::string result = greeter.greet("Forge");
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "Greeting took: " << duration.count() << "ms" << std::endl;

    return 0;
}
