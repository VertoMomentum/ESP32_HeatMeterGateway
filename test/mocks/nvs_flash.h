#pragma once

#include "esp_err.h"

inline esp_err_t g_mockNvsInitFirstResult = ESP_OK;
inline int g_mockNvsEraseCount = 0;

inline esp_err_t nvs_flash_init(void)
{
    if (g_mockNvsInitFirstResult != ESP_OK)
    {
        esp_err_t res = g_mockNvsInitFirstResult;
        g_mockNvsInitFirstResult = ESP_OK;
        return res;
    }
    return ESP_OK;
}

inline esp_err_t nvs_flash_erase(void)
{
    g_mockNvsEraseCount++;
    return ESP_OK;
}
