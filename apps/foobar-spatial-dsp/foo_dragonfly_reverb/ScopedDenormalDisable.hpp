#pragma once
/* MSVC/SSE2 denormal suppression — replaces DPF's extra/ScopedDenormalDisable.hpp */
#ifdef _MSC_VER
#include <immintrin.h>
struct ScopedDenormalDisable {
    unsigned int _csr;
    ScopedDenormalDisable() : _csr(_mm_getcsr()) {
        _mm_setcsr(_csr | 0x8040u); /* DAZ | FTZ */
    }
    ~ScopedDenormalDisable() { _mm_setcsr(_csr); }
};
#else
struct ScopedDenormalDisable {
    ScopedDenormalDisable() {}
    ~ScopedDenormalDisable() {}
};
#endif
