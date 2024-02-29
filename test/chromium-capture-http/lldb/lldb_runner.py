#!/usr/bin/env python3

"""
--no-sandbox
in run.sh

fix: chromium does not start in lldb debugger sandbox::SetuidSandboxHost::GetSandboxBinaryPath signal SIGILL: illegal instruction operand

thread #1: tid = 121985, 0x000055555f506a1a chromium`sandbox::SetuidSandboxHost::GetSandboxBinaryPath() + 538, name = 'chromium', stop reason = signal SIGTRAP frame #0: 0x000055555f506a1a chromium`sandbox::SetuidSandboxHost::GetSandboxBinaryPath() + 538
thread #2: tid = 121989, 0x00007ffff6f4385f libc.so.6`__poll + 79, name = 'sandbox_ipc_thr' frame #0: 0x00007ffff6f4385f libc.so.6`__poll + 79

thread #1: tid = 121985, 0x000055555f506a1a chromium`sandbox::SetuidSandboxHost::GetSandboxBinaryPath() + 538, name = 'chromium', stop reason = signal SIGILL: illegal instruction operand frame #0: 0x000055555f506a1a chromium`sandbox::SetuidSandboxHost::GetSandboxBinaryPath() + 538
thread #2: tid = 121989, 0x00007ffff6f4385f libc.so.6`__poll + 79, name = 'sandbox_ipc_thr' frame #0: 0x00007ffff6f4385f libc.so.6`__poll + 79

https://issues.chromium.org/issues/41198011
"""

"""
still with "chromium --no-sandbox"
lldb hangs

https://github.com/llvm/llvm-project/issues/54761

lldb crash parsing Google Chrome types

The packages look mildly broken, as the python files are scattered between site and dist directories, I had to fix that in my Dockerfile:

cp -r /usr/lib/llvm-14/lib/python3.9/site-packages/lldb/* \
    /usr/lib/python3/dist-packages/lldb



no "dist-packages" in
/nix/store/47n788z8npj0mysyr853p1rs28lslzj4-lldb-16.0.6-lib/lib/python3.11

chromium is built with llvm 17

nixpkgs/pkgs/applications/networking/browsers/chromium/default.nix

  llvmPackages_attrName = "llvmPackages_17";
  stdenv = pkgs.${llvmPackages_attrName}.stdenv;

$ lldb --version
lldb version 16.0.6

"""

# https://stackoverflow.com/questions/33412504/lldb-python-c-bindings-async-step-instructions

# https://github.com/llvm/llvm-project/blob/main/lldb/examples/python/process_events.py

# https://github.com/qt-creator/qt-creator/blob/1af555ad09be169bebc7525e4bb7e10ad4de271d/share/qtcreator/debugger/lldbbridge.py#L71

import time
import sys
#sys.path.append("/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python")
import lldb
import os
import asyncio

class Options:
    pass

options = Options()
options.show_threads = True
options.stop_on_error = True

def print_threads(process, options):
    if options.show_threads:
        for thread in process:
            print("%s %s" % (thread, thread.GetFrameAtIndex(0)))


def run_commands(command_interpreter, commands):
    return_obj = lldb.SBCommandReturnObject()
    for command in commands:
        command_interpreter.HandleCommand(command, return_obj)
        if return_obj.Succeeded():
            print(return_obj.GetOutput())
        else:
            print(return_obj)
            if options.stop_on_error:
                break

async def main():

    debugger = lldb.SBDebugger.Create()

    debugger.SetAsync(True)

    command_interpreter = debugger.GetCommandInterpreter()

    # fix: error: unable to locate lldb-server
    # lldb is looking in the wrong $PATH = support exe dir
    # https://github.com/NixOS/nixpkgs/pull/119945
    # -> set LLDB_DEBUGSERVER_PATH to absolute path of lldb-server
    # get absolute path of lldb-server
    # TODO shorter?
    lldb_server_exe = next(filter(lambda p: os.path.exists(p), map(lambda p: p + "/lldb-server", os.get_exec_path())))
    os.environ["LLDB_DEBUGSERVER_PATH"] = lldb_server_exe
    # https://bugs.launchpad.net/ubuntu/+source/llvm-toolchain-10/+bug/1894159
    # $ ./run.sh 2>&1 | grep "support exe dir"
    # 1707908435.624865294 python3          support exe dir -> `/nix/store/asiphbpiy2gmidfm3xbwcikayhs66289-python3-3.11.7/bin/`
    #debugger.EnableLog("lldb", ['all'])

    exe = sys.argv[1]
    print("exe", repr(exe))

    args = sys.argv[2:]
    print("args", repr(args))

    target = debugger.CreateTargetWithFileAndArch(exe, lldb.LLDB_ARCH_DEFAULT)

    if not target:
        print("no target")
        return

    """
    #main_bp = target.BreakpointCreateByName("main", target.GetExecutable().GetFilename())
    main_bp = target.BreakpointCreateByName("main")
    print(main_bp)
    """

    # TODO find this address in BIO_read
    #    0x000055555d496989 <+73>:    mov    ecx,eax
    #    0x000055555d49698b <+75>:    add    QWORD PTR [rbx+0x30],rcx ; bio->num_read += ret;
    bp = target.BreakpointCreateByAddress(0x55555d496989)

    """
    #break BIO_read
    break *0x000055555d496989
    commands 1
      # no...
      #printf "buf %d %s\n", $eax, *($rbx)@$eax
      # print buf size
      printf "buf size=%d\n", $eax
      # print buf content
      # no. this stops on null bytes
      #printf "buf str=%s\n", *($rbx)@$eax
    """

    launch_info = lldb.SBLaunchInfo(args)
    launch_info.SetExecutableFile(lldb.SBFileSpec(exe), True)
    #launchInfo.SetWorkingDirectory(self.workingDirectory_)
    #launchInfo.SetEnvironmentEntries(self.environment_, False)

    error = lldb.SBError()
    process = target.Launch(launch_info, error)

    #print("waiting for launch"); await asyncio.sleep(5)

    # Make sure the launch went ok
    if not process or process.GetProcessID() == lldb.LLDB_INVALID_PROCESS_ID:
        print("no process")
        if error:
            print(error)
        else:
            print("error: launch failed")
        return

    pid = process.GetProcessID()
    print("Process is %i" % (pid))

    """
    if attach_info:
        # continue process if we attached as we won't get an
        # initial event
        process.Continue()
    """

    ################

    listener = debugger.GetListener()
    # sign up for process state change events
    stop_idx = 0
    done = False

    while not done:

        event = lldb.SBEvent()

        #print("listener.WaitForEvent")
        # wrap listener.WaitForEvent with asyncio
        # https://stackoverflow.com/questions/43241221/how-can-i-wrap-a-synchronous-function-in-an-async-coroutine
        #if not listener.WaitForEvent(options.event_timeout, event):
        event_timeout = lldb.UINT32_MAX
        loop = asyncio.get_event_loop()
        # None == ThreadPoolExecutor
        wait_result = await loop.run_in_executor(None, listener.WaitForEvent, event_timeout, event)
        # asyncio.coroutine was removed
        #wait_result = await asyncio.coroutine(listener.WaitForEvent)(event_timeout, event)

        if not wait_result:

            # timeout waiting for an event
            print(
                "no process event for %u seconds, killing the process..."
                % (event_timeout)
            )
            done = True
            break

        if not lldb.SBProcess.EventIsProcessEvent(event):
            print("ignoring event = %s" % (event))
            continue

        """
        # event = <lldb.SBEvent; proxy of <Swig Object of type 'lldb::SBEvent *' at 0x7f88672104b0> >
        print("event = %s" % (event))
        #print("event dir", dir(event))
        print("event GetBroadcaster", repr(event.GetBroadcaster()))
        print("event GetBroadcasterClass", repr(event.GetBroadcasterClass()))
        #print("event GetCStringFromEvent", repr(event.GetCStringFromEvent(event)))
        print("event GetDataFlavor", repr(event.GetDataFlavor()))
        #print("event GetDescription", repr(event.GetDescription(description)))
        print("event GetType", repr(event.GetType()))
        print("event IsValid", repr(event.IsValid()))
        """

        """
        event GetBroadcaster <lldb.SBBroadcaster; proxy of <Swig Object of type 'lldb::SBBroadcaster *' at 0x7feae4015050> >
        event GetBroadcasterClass 'lldb.process'
        event GetDataFlavor 'Process::ProcessEventData'
        event GetType 1
        event IsValid True
        """

        print("event", event.GetType(), event.GetDataFlavor())

        state = lldb.SBProcess.GetStateFromEvent(event)
        if state == lldb.eStateInvalid:
            # Not a state event
            print("process event = %s" % (event))
        else:
            print(
                "process state changed event: %s"
                % (lldb.SBDebugger.StateAsCString(state))
            )
            if state == lldb.eStateStopped:
                if stop_idx == 0:
                    if launch_info:
                        print("process %u launched" % (pid))
                        run_commands(
                            command_interpreter, ["breakpoint list"]
                        )
                    else:
                        print("attached to process %u" % (pid))
                        for m in target.modules:
                            print(m)
                        """
                        if options.breakpoints:
                            for bp in options.breakpoints:
                                debugger.HandleCommand(
                                    "_regexp-break %s" % (bp)
                                )
                            run_commands(
                                command_interpreter,
                                ["breakpoint list"],
                            )
                        """
                    """
                    run_commands(
                        command_interpreter, options.launch_commands
                    )
                    """
                else:
                    #if options.verbose:
                    if True:
                        print("process %u stopped" % (pid))
                    """
                    run_commands(
                        command_interpreter, options.stop_commands
                    )
                    """
                stop_idx += 1
                print_threads(process, options)
                print("continuing process %u" % (pid))
                process.Continue()
            elif state == lldb.eStateExited:
                exit_desc = process.GetExitDescription()
                if exit_desc:
                    print(
                        "process %u exited with status %u: %s"
                        % (pid, process.GetExitStatus(), exit_desc)
                    )
                else:
                    print(
                        "process %u exited with status %u"
                        % (pid, process.GetExitStatus())
                    )
                """
                run_commands(
                    command_interpreter, options.exit_commands
                )
                """
                done = True
            elif state == lldb.eStateCrashed:
                print("process %u crashed" % (pid))
                print_threads(process, options)
                """
                run_commands(
                    command_interpreter, options.crash_commands
                )
                """
                done = True
            elif state == lldb.eStateDetached:
                print("process %u detached" % (pid))
                done = True
            elif state == lldb.eStateRunning:
                # process is running, don't say anything,
                # we will always get one of these after
                # resuming
                #if options.verbose:
                if True:
                    print("process %u resumed" % (pid))
            elif state == lldb.eStateUnloaded:
                print(
                    "process %u unloaded, this shouldn't happen"
                    % (pid)
                )
                done = True
            elif state == lldb.eStateConnected:
                print("process connected")
            elif state == lldb.eStateAttaching:
                print("process attaching")
            elif state == lldb.eStateLaunching:
                print("process launching")

    # end of: while not done

    """
    # Now that we are done dump the stdout and stderr
    process_stdout = process.GetSTDOUT(1024)
    if process_stdout:
        print("Process STDOUT:\n%s" % (process_stdout))
        while process_stdout:
            process_stdout = process.GetSTDOUT(1024)
            print(process_stdout)

    process_stderr = process.GetSTDERR(1024)
    if process_stderr:
        print("Process STDERR:\n%s" % (process_stderr))
        while process_stderr:
            process_stderr = process.GetSTDERR(1024)
            print(process_stderr)
    """

    process.Kill()  # kill the process

    lldb.SBDebugger.Terminate()

    return

    ##############

    # Print some simple process info
    state = process.GetState()
    print('process state')
    print(state)
    thread = process.GetThreadAtIndex(0)
    frame = thread.GetFrameAtIndex(0)
    print('stop loc')
    print(hex(frame.pc))
    print('thread stop reason')
    print(thread.stop_reason)

    print('stepping')
    thread.StepInstruction(False)

    time.sleep(1)

    print('process state')
    print(process.GetState())

    print('thread stop reason')
    print(thread.stop_reason)
    frame = thread.GetFrameAtIndex(0)
    print('stop loc')
    print(hex(frame.pc))  # invalid output?

asyncio.run(main())
