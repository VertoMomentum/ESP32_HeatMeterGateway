#pragma once

#include <cstdint>
#include <chrono>

inline int64_t g_mockTimeUs = 1000000LL;
inline bool g_useMockTime = false;

inline int64_t esp_timer_get_time(void)
{
    if (g_useMockTime)
    {
        return g_mockTimeUs;
    }
    using namespace std::chrono;
    return duration_cast<microseconds>(steady_clock::now().time_since_epoch()).count();
}
