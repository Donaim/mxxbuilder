
#ifndef __SOME_STDAFX_H
#define __SOME_STDAFX_H

    #ifdef __WIN_32__
    #include <windows.h>
    #include <io.h>
    #endif
    #ifdef __unix__
    #include <fcntl.h>
    #endif

#endif