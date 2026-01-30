/**
 * Good C++ header file.
 *
 * This header demonstrates proper header guard usage and documentation.
 */

#pragma once

#include <string>
#include <vector>

namespace example {

/**
 * Calculator class for basic arithmetic operations.
 */
class Calculator {
 public:
    /**
     * Constructor.
     */
    Calculator() = default;

    /**
     * Destructor.
     */
    ~Calculator() = default;

    /**
     * Add two numbers.
     *
     * @param a First number
     * @param b Second number
     * @return Sum of a and b
     */
    int add(int a, int b) const;

    /**
     * Subtract two numbers.
     *
     * @param a First number
     * @param b Second number
     * @return Difference of a and b
     */
    int subtract(int a, int b) const;

    /**
     * Multiply two numbers.
     *
     * @param a First number
     * @param b Second number
     * @return Product of a and b
     */
    int multiply(int a, int b) const;

 private:
    // No state needed for this simple calculator
};

}  // namespace example
