#!/usr/bin/env python3

import os
import subprocess
import sys
import re
import argparse

def skip_until_crash(file):
    while True:
        line = file.readline()
        if not line:
            return
        if 'E/CRASH' in line:
            return
        if 'beginning of crash' in line:
            return

def find_lib(lib_name):
    dirs = [ ARCH, '', f'{ANDROID_SYMBOL_PATH}/{ARCH}' ]
    exts = [ '.sym.so', '.so' ]
    for ext in exts:
        for dir in dirs:
            if dir:
                candidate = f'{dir}/lib{lib_name}{ext}'
            else:
                candidate = f'lib{lib_name}{ext}'
            if os.path.isfile(candidate):
                return candidate
    return None

def symbolize_line(line):
    print (line)
    m = compile.match(line)
    if m:
        no = m.group('no')
        lib = m.group('lib')
        addr = m.group('addr')
        print(f'{stack_color}{no} lib{lib}.so:{addr}')
        if lib and addr:
            symPath = find_lib(lib)
            if symPath:
                os.system(f'{ADDR2LINE} -a -p -f -C -e {symPath} {addr} | head -n 1')
                return True
    return False

def symbolize(file):
    parse=False
    while True:
        line = file.readline().strip()
        print (line)
        if not line:
            return
        if symbolize_line(line):
            parse = True
        else:
            if parse:
                return
            else:
                # print contents before pc appears
                print(line)

def input_from_stdin(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            symbolize_line(output.strip())
    rc = process.poll()
    return rc

def set_unity_ver(ver):
    global UNITY
    UNITY=f'/Applications/Unity/Hub/Editor/{ver}'
    print (f'Unity={UNITY}')

def extract_info(file):
    while True:
        line = file.readline().strip()
        if not line:
            return
        p = re.compile(r".*E\/CRASH\s+.+Version '(?P<version>[0-9\.f]+) .+CPU '(?P<cpu>[^']+)'")
        m = p.match(line)
        if m:
            set_unity_ver(m.group('version'))
            return
        
def set_ndk():
    global NDK, NDK_TOOLCHAIN, ARCH, ADDR2LINE, ANDROID_SYMBOL_PATH
    if args.ndk:
        NDK=os.environ.get('NDK', None)
    else:
        NDK=f'{UNITY}/PlaybackEngines/AndroidPlayer/NDK'

    NDK_TOOLCHAIN=f'{NDK}/toolchains'

    #if args.arch == 32:
    #    ARCH='armeabi-v7a'
    #    ADDR2LINE=f'{NDK_TOOLCHAIN}/arm-linux-androideabi-4.9/prebuilt/darwin-x86_64/bin/arm-linux-androideabi-addr2line'
    #    ANDROID_SYMBOL_PATH=f'{UNITY}/PlaybackEngines/AndroidPlayer/Variations/il2cpp/Release/Symbols'
    #else:
    ARCH='arm64-v8a'
    #ADDR2LINE=f'{NDK_TOOLCHAIN}/aarch64-linux-android-4.9/prebuilt/darwin-x86_64/bin/aarch64-linux-android-addr2line'
    ADDR2LINE=f'{NDK_TOOLCHAIN}/llvm/prebuilt/darwin-x86_64/bin/llvm-addr2line'
    ANDROID_SYMBOL_PATH=f'{UNITY}/PlaybackEngines/AndroidPlayer/Variations/il2cpp/Release/Symbols'
    print (f'ADDR2LINE={ADDR2LINE}')


stack_color='\033[93m'
compile = re.compile(r'.+(?P<no>#[0-9]+) pc (?P<addr>\w+)\s+.+lib(?P<lib>[\w]+)\.so')
parser = argparse.ArgumentParser(description='Symbolicate crash logs from android logcat')
parser.add_argument('logfile')#, nargs='?')
parser.add_argument('--unityVer', help='unity version such as "2021.1.0f1"')
parser.add_argument('--ndk', help='ndk path')
parser.add_argument('--symboldir', help="directory path containing '[armeabi-v7a or arm64-v8a]/lib[...].sym.so'")
#parser.add_argument('--arch', default=64, choices=['32', '64'])
args = parser.parse_args()

if args.unityVer:
    set_unity_ver(args.unityVer)
else:
    UNITY=os.environ.get('UNITY', None)

LOGFILE=args.logfile
if args.symboldir:
    ANDROID_SYMBOL_PATH=args.symboldir
    
if LOGFILE and os.path.isfile(LOGFILE):
    with open(LOGFILE, 'r') as file:
        #skip_until_crash(file)
        set_ndk()
        symbolize(file)
# else:
#     print(f'Input from adb logcat')
#     input_from_stdin('adb logcat')

