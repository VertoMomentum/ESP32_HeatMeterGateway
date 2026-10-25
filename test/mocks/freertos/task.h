#pragma once

#include "FreeRTOS.h"

struct MockTaskExitException
{
};

inline void (*g_lastCreatedTaskFn)(void *) = nullptr;
inline void *g_lastCreatedTaskParam = nullptr;
inline int g_mockTaskDelayRemaining = -1;
inline void (*g_onTaskDelayCallback)(void) = nullptr;

inline void vTaskDelay(TickType_t ticks)
{
    (void)ticks;
    if (g_onTaskDelayCallback != nullptr)
    {
        g_onTaskDelayCallback();
    }
    if (g_mockTaskDelayRemaining >= 0)
    {
        if (g_mockTaskDelayRemaining == 0)
        {
            throw MockTaskExitException();
        }
        g_mockTaskDelayRemaining--;
    }
}

inline BaseType_t xTaskCreate(void (*taskFunction)(void *), const char *name, uint32_t stackDepth, void *params, int priority, TaskHandle_t *handle)
{
    (void)name;
    (void)stackDepth;
    (void)priority;
    g_lastCreatedTaskFn = taskFunction;
    g_lastCreatedTaskParam = params;
    if (handle != nullptr)
    {
        *handle = (TaskHandle_t)1;
    }
    return pdTRUE;
}

inline void vTaskDelete(TaskHandle_t handle)
{
    (void)handle;
}
