#include <iostream>
#include "string_utils.h"

int main() {
    std::string text = "Hello World";
    std::cout << "Original: " << text << std::endl;
    std::cout << "Upper: " << to_upper(text) << std::endl;
    std::cout << "Lower: " << to_lower(text) << std::endl;
    return 0;
}
