#pragma once

#include "esp_err.h"
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>
#include <map>

typedef uint32_t nvs_handle_t;

typedef enum
{
    NVS_READONLY,
    NVS_READWRITE
} nvs_open_mode_t;

inline std::map<std::string, std::string> g_mockNvsStrings;
inline std::map<std::string, uint16_t> g_mockNvsU16;
inline std::map<std::string, uint32_t> g_mockNvsU32;
inline std::map<std::string, uint8_t> g_mockNvsU8;
inline esp_err_t g_mockNvsOpenResult = ESP_OK;
inline esp_err_t g_mockNvsCommitResult = ESP_OK;

inline void resetMockNvs()
{
    g_mockNvsStrings.clear();
    g_mockNvsU16.clear();
    g_mockNvsU32.clear();
    g_mockNvsU8.clear();
    g_mockNvsOpenResult = ESP_OK;
    g_mockNvsCommitResult = ESP_OK;
}

inline esp_err_t nvs_open(const char *name, nvs_open_mode_t openMode, nvs_handle_t *outHandle)
{
    (void)name;
    (void)openMode;
    if (g_mockNvsOpenResult != ESP_OK)
    {
        return g_mockNvsOpenResult;
    }
    if (outHandle != nullptr)
    {
        *outHandle = 1;
    }
    return ESP_OK;
}

inline void nvs_close(nvs_handle_t handle)
{
    (void)handle;
}

inline esp_err_t nvs_get_str(nvs_handle_t handle, const char *key, char *outValue, size_t *length)
{
    (void)handle;
    if (key == nullptr || length == nullptr)
    {
        return ESP_FAIL;
    }
    auto it = g_mockNvsStrings.find(key);
    if (it == g_mockNvsStrings.end())
    {
        return ESP_FAIL;
    }
    size_t required = it->second.size() + 1;
    if (outValue == nullptr)
    {
        *length = required;
        return ESP_OK;
    }
    if (*length < required)
    {
        return ESP_FAIL;
    }
    std::memcpy(outValue, it->second.c_str(), required);
    *length = required;
    return ESP_OK;
}

inline esp_err_t nvs_get_u16(nvs_handle_t handle, const char *key, uint16_t *outValue)
{
    (void)handle;
    if (key == nullptr || outValue == nullptr)
    {
        return ESP_FAIL;
    }
    auto it = g_mockNvsU16.find(key);
    if (it == g_mockNvsU16.end())
    {
        return ESP_FAIL;
    }
    *outValue = it->second;
    return ESP_OK;
}

inline esp_err_t nvs_get_u32(nvs_handle_t handle, const char *key, uint32_t *outValue)
{
    (void)handle;
    if (key == nullptr || outValue == nullptr)
    {
        return ESP_FAIL;
    }
    auto it = g_mockNvsU32.find(key);
    if (it == g_mockNvsU32.end())
    {
        return ESP_FAIL;
    }
    *outValue = it->second;
    return ESP_OK;
}

inline esp_err_t nvs_get_u8(nvs_handle_t handle, const char *key, uint8_t *outValue)
{
    (void)handle;
    if (key == nullptr || outValue == nullptr)
    {
        return ESP_FAIL;
    }
    auto it = g_mockNvsU8.find(key);
    if (it == g_mockNvsU8.end())
    {
        return ESP_FAIL;
    }
    *outValue = it->second;
    return ESP_OK;
}

inline esp_err_t nvs_set_str(nvs_handle_t handle, const char *key, const char *value)
{
    (void)handle;
    if (key != nullptr && value != nullptr)
    {
        g_mockNvsStrings[key] = value;
    }
    return ESP_OK;
}

inline esp_err_t nvs_set_u16(nvs_handle_t handle, const char *key, uint16_t value)
{
    (void)handle;
    if (key != nullptr)
    {
        g_mockNvsU16[key] = value;
    }
    return ESP_OK;
}

inline esp_err_t nvs_set_u32(nvs_handle_t handle, const char *key, uint32_t value)
{
    (void)handle;
    if (key != nullptr)
    {
        g_mockNvsU32[key] = value;
    }
    return ESP_OK;
}

inline esp_err_t nvs_set_u8(nvs_handle_t handle, const char *key, uint8_t value)
{
    (void)handle;
    if (key != nullptr)
    {
        g_mockNvsU8[key] = value;
    }
    return ESP_OK;
}

inline esp_err_t nvs_commit(nvs_handle_t handle)
{
    (void)handle;
    return g_mockNvsCommitResult;
}
