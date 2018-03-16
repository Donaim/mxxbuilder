My simple builder for c++

# Usage
    mxxbuild.py [++copts COPTS [COPTS ...]]
                [++lopts LOPTS [LOPTS ...]]
                [++exclude EXCLUDE [EXCLUDE ...]]
                [++compile] [++no-compile]
                [++link] [++no-link] 
                [++autorun] [++clean]
                targetdir

Where `++copts` is compiler-options, and respectively `++lopts` is linker options.  
`targetdir` is source files directory.  
You need to use `++` to provide optional arguments for compiler or linker it's because argparse recognizes `-` as its own option.

For now, target project has to have following structure:  

    | project root
    |---|- build/
        |- src/
        |- ...

Where, obviously, /build is the output directory which cxxbuilder is going to be using for .exe file and .o files. And /src is `targetdir` which contains all source .cpp files that are used during compilation.   


# To do
- [X] Timings and other statistics
- [X] Option parsing
- [X] Auto-run option
- [X] Send-forward options for linker and compiler

