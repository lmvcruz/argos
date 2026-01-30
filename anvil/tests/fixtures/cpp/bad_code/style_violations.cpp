/**
 * C++ file with style violations.
 *
 * This fixture violates Google C++ Style Guide conventions.
 */

#include <iostream>
#include <string>
// Missing blank line before includes
#include <vector>

// Global variable (should be avoided)
int globalVariable = 42;

// Function name should be lowercase with underscores
void BadFunctionName(int X,int y) {  // No spaces after commas
    int z=X+y;  // No spaces around operators
    std::cout<<z<<std::endl;  // No spaces around <<
}

// Class name is okay, but members are not
class GoodClassName {
public:  // Should be "public:" with one space indent
    // Member variable without trailing underscore (Google style)
    int memberVar;
    std::string name;

    // Constructor with poor formatting
    GoodClassName(int x,std::string n):memberVar(x),name(n){}

    // Very long line that exceeds 80 characters and should be wrapped but is not wrapped properly
    void VeryLongMethodNameThatExceedsRecommendedLength(int param1, int param2, int param3, int param4) {
        std::cout << param1 << param2 << param3 << param4 << std::endl;
    }

private:
    void helper( int x , int y ) {  // Extra spaces in parameters
        return;
    }
};

// Multiple statements on one line
int main() { int x = 1; int y = 2; int z = x + y; return 0; }
