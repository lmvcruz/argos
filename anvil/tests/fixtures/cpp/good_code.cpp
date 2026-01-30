/**
 * Good C++ code sample.
 *
 * This file demonstrates well-formatted, standards-compliant C++ code
 * that should pass all validators.
 */

#include <iostream>
#include <string>
#include <vector>

namespace example {

/**
 * Calculate the sum of numbers in a vector.
 *
 * @param numbers Vector of integers to sum
 * @return Sum of all numbers
 */
int calculate_sum(const std::vector<int>& numbers) {
    int sum = 0;
    for (int num : numbers) {
        sum += num;
    }
    return sum;
}

/**
 * DataProcessor class for processing data with configurable options.
 */
class DataProcessor {
 public:
    /**
     * Constructor.
     *
     * @param name Name of the processor
     * @param debug Enable debug output
     */
    DataProcessor(const std::string& name, bool debug = false)
        : name_(name), debug_(debug) {}

    /**
     * Add an item to the data list.
     *
     * @param item Item to add
     */
    void add_data(const std::string& item) {
        data_.push_back(item);
        if (debug_) {
            std::cout << "Added item: " << item << std::endl;
        }
    }

    /**
     * Get the number of items.
     *
     * @return Number of items in the data list
     */
    size_t get_count() const {
        return data_.size();
    }

 private:
    std::string name_;
    bool debug_;
    std::vector<std::string> data_;
};

}  // namespace example

int main() {
    example::DataProcessor processor("example", true);
    processor.add_data("item1");
    processor.add_data("item2");
    std::cout << "Total items: " << processor.get_count() << std::endl;
    return 0;
}
