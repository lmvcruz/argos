#include <iostream>
#include "greeter.h"

int main() {
    Greeter greeter;
    std::cout << greeter.greet("Forge") << std::endl;
    return 0;
}
