#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR cmd, int show)
{
    wchar_t directory[32768];
    wchar_t python[32768];
    wchar_t command[32768];
    DWORD length = GetModuleFileNameW(NULL, directory, ARRAYSIZE(directory));
    if (!length || length == ARRAYSIZE(directory))
        goto failed;
    wchar_t *separator = wcsrchr(directory, L'\\');
    if (separator == NULL)
        goto failed;
    *separator = L'\0';

    if (swprintf(python, ARRAYSIZE(python), L"%ls\\runtime-spleeter\\python.exe", directory) < 0 ||
        swprintf(command, ARRAYSIZE(command),
                 L"\"%ls\" -I \"%ls\\app.py\" --desktop --port 0", python, directory) < 0)
        goto failed;

    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION child;
    startup.cb = sizeof(startup);
    if (!CreateProcessW(python, command, NULL, NULL, FALSE, CREATE_NO_WINDOW,
                        NULL, directory, &startup, &child))
        goto failed;
    CloseHandle(child.hThread);
    WaitForSingleObject(child.hProcess, INFINITE);
    DWORD exit_code;
    if (!GetExitCodeProcess(child.hProcess, &exit_code))
        exit_code = 1;
    CloseHandle(child.hProcess);
    return (int)exit_code;

failed:
    MessageBoxW(NULL, L"Blacktable could not find or start its Windows runtime. Reinstall Blacktable and try again.",
                L"Blacktable Studio by Brian", MB_OK | MB_ICONERROR | MB_SETFOREGROUND);
    return 1;
}
