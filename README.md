Tool for c++ projects build automatization  

# Example usage
`$ cd project-root`  
`$ mxxbuild.py /src`  
mxx will perform both compilation and linking. All build files are gonna be in `/project-root/build` and output file will be called `a.exe` 

`$ cd project-root`  
`$ mxxbuild.py /src ++clean ++autorun ++verbose 0 ++max-threads 16 ++out ~/o.exe ++build ~/tmp/project-root ++copts -Iinclude/`  
Clean ~/tmp/project-root directory, set verbosity level to 0, use 16 threads and headers in `/project-root/include` to compile source files from `/project-root/src`, link them with output in `~/o.exe` and run final executable.  

To see all options run `mxxbuild.py +h`   

# Internal procedure
- recieve `/targetpath` path
- create `/build` if doesn't exist
- init output files from `/build`, and source files from `/targetpath`
- compare modification time of source files and output files with same name
- if output file is older, recompile it
- link everything in `/build`

Note that mxxbuild does not track for changes in .h files. You have to recompile it youself whether such change has happend.  
Exception is "stdafx.h" which is being checked for updates.  

# Features
- compilation of changed files only
- async compilation
- support of "stdafx.h" precompiled header
- cross platform
- no install, just download and run
- no external dependencies, only g++ itself

# To do
- [X] Timings and other statistics
- [X] Option parsing
- [X] Auto-run option
- [X] Send-forward options for linker and compiler
- [X] max-threads option for compilation
