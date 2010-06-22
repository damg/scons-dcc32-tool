# Author: Dmitri Bachtin

# dcc32.py - A very simple Delphi tool for building dpr projects with
# SCons.

# Copyright (c) 2010, COM plan + service GmbH
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:

#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.

#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.

#    * Neither the name of the <ORGANIZATION> nor the names of its
#      contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from SCons.Script import *
from SCons.Scanner import Scanner
from SCons.Builder import Builder
import os.path
import re

def exists(env):
    return WhereIs(env["DCC"])

def is_library_project(content):
    return re.search(r"\s*library\s+[^;]+\s*;", content) != None

def is_program_project(content):
    return re.search(r"\s*program\s+[^;]+\s*;", content) != None

def cfg_output_directory(cfg_filename):
    f = open(cfg_filename, "r")
    try:
        for line in f:
            if line.startswith("-E"):
                return line.strip()[3:len(line)-2]
    finally:
        f.close()
    return None

def dccflags_output_directory(flags):
    for line in flags:
        if line.startswith("-E"):
            return line[3:len(line)-1]
    return None

def print_dccflags(env):
    print env["DCCFLAGS"]

def dcc32_emitter(target, source, env):
    assert(len(target) == 1)
    assert(len(source) == 1)
    
    dpr = source[0]
    if is_library_project(dpr.get_contents()):
        tfile = "%s.dll" % str(target[0])
    elif is_program_project(dpr.get_contents()):
        tfile = "%s.exe" % str(target[0])
    else:
        raise RuntimeError("Unknown delphi project type")

    outdir=dccflags_output_directory(env["DCCFLAGS"])

    if not outdir:
        cfg_filename = "%s.cfg" % str(target[0])
        outdir=cfg_output_directory(cfg_filename)
    if not outdir:
        outdir="."

    if outdir.startswith("#"):
        outdir = "%s/%s" % (env.GetLaunchDir(), outdir[1:])
    tfile = os.path.join(outdir, tfile)

    target.append(tfile)

    return (target, source)

def generate(env):
    
    def _dccflags_unitpath_expander(dccopts):
        def expand_path(opt):
            if opt.startswith("-E"):
                outdir = opt[3:len(opt)-1]
                if outdir.startswith("#"):
                    outdir = "%s/%s" % (env.GetLaunchDir(), outdir[1:])
                return "-E\"%s\"" % outdir
            else:
                return opt
                
        return [ expand_path(e) for e in dccopts ]

    env["DCC"] = "dcc32"
    env["DCCFLAGS"] = []
    env["_dccflags_unitpath_expander"] = _dccflags_unitpath_expander
    env["_DCCFLAGS"] = "${_dccflags_unitpath_expander(DCCFLAGS)}"

    dcc32_compiler = Builder(
        action = "$DCC $_DCCFLAGS ${SOURCES.file}",
        src_suffix = ".dpr",
        emitter = dcc32_emitter,
        chdir=1
        )

    env.Append(BUILDERS = { "DelphiProject" : dcc32_compiler } )
