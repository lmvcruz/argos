#include <iostream>

int main() {
#ifdef DEBUG_BUILD
    std::cout << "Running in DEBUG mode" << std::endl;
#elif defined(RELEASE_BUILD)
    std::cout << "Running in RELEASE mode" << std::endl;
#else
    std::cout << "Build type not specified" << std::endl;
#endif
    return 0;
}
