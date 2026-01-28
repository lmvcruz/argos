#ifndef TEMPLATE_UTILS_H
#define TEMPLATE_UTILS_H

template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

template<typename T>
T min(T a, T b) {
    return (a < b) ? a : b;
}

#endif // TEMPLATE_UTILS_H
