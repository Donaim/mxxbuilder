My simple builder for c++

# Usage
    mxxbuild.py targetpath [++out [OUT]] 
                [++compile] [++no-compile] [++link] [++no-link] 
                [++stdafx] [++no-stdafx]  
                [++clean] [++autorun]  
                [++copts COPTS [COPTS ...]] [++lopts LOPTS [LOPTS ...]]
                [++exclude EXCLUDE [EXCLUDE ...]] 

Where  
`targetpath` is source files directory OR just one file. Usually `/src`.  
`++copts`, `++lopts` are compiler- and respectively linker- options.  
`++exclude` will ignore chosen files during linking/compilation. Useful for tests or solution with multiple `main` entries.  
`++out` specifies `-o` (output file) option.  
`++clean` does usual clean up in `/build` directory.  
`++autorun` runs `OUT` after linking, or just runs if it exists.  
`++compile`, `++no-compile`, `++link` and `++no-link` are self-descriptive. Default values are true.  

You need to use `++` instead of `--` because argparse treats `-` as its own option, therefore it's problematic to pass `copts`, `lopts` to g++.

# Internal procedure
- recieve `/targetpath` path
- find `/build` directory at `targetpath/../build`. create if doesn't exist
- init output files from `/build`, and source files from `/targetpath`
- compare modification time of source files and output files with same name
- if output file is older, recompile it
- link everything in `/build`

Note that mxxbuild does not track for changes in .h files. You have to recompile it youself whether such change has happend.  
Exception is "stdafx.h" which is being checked for updates.  

# To do
- [X] Timings and other statistics
- [X] Option parsing
- [X] Auto-run option
- [X] Send-forward options for linker and compiler

