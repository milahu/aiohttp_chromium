#!/usr/bin/env python3

# TODO remove?
# dont ask: Make breakpoint pending on future shared library load?
gdb.execute("set breakpoint pending on")

gdb.execute("break BIO_read")
#gdb.execute("break BIO_write") # TODO
gdb.execute("")
gdb.execute("")
gdb.execute("")



# https://stackoverflow.com/questions/17893554
# how-to-print-the-current-line-of-source-at-breakpoint-in-gdb-and-nothing-else

# example: these breakpoints do stop - but cannot change their 
# stop method (which contains the "commands" for breakpoint in python)
#ax = gdb.Breakpoint("doSomething")
#print("hello", ax)
#print(dir(ax))
#print(ax.expression, ax.condition, ax.commands) # not writable!
#bx = gdb.Breakpoint("myprog.c:63")

# anything more than that - need to subclass:


class BIO_read_result(gdb.Breakpoint):
    """
        rbp == bio
        rbx == buf
        rax == len

        eax == ret

        print $eax
        5

        (gdb) print (char[5]) *($rbx)
        $12 = "H\027H\001X"
    """
    def stop(self):
        ret = gdb.execute("print $eax", to_string=True)
        buf = gdb.execute(f"print print (char[{ret}]) *($rbx)", to_string=True)
        print(buf)
        gdb.execute("continue")
        return True



class BIO_read(gdb.Breakpoint):
    done = False
    def stop(self):
        return True
        return False # continue inferior
        if self.done:
            return False # continue inferior
        asm = gdb.execute("disassemble", to_string=True)
        # parse
        addr, instr = None, None
        for line in asm.split("\n"):
            # FIXME Python Exception <class 'ValueError'>: not enough values to unpack (expected 2, got 1)
            line_parts = line.split("\t")
            if len(line_parts) != 2:
                continue
            addr, instr = line.split("\t")
            if instr == "mov    ecx,eax":
                print("line", repr(line))
                break
            if instr == "add    QWORD PTR [rbx+0x30],rcx":
                print("line", repr(line))
                break
            # unstable instr: "jmp    0x55555d4969b4 <BIO_read+116>"

        if addr == None:
            raise Exception("not found the result instructions of BIO_read")

        # addr: "   0x000055555d496989 <+73>:"
        addr = "*" + addr.split("<")[0].strip()
        # addr: "*0x000055555d496989"

        """
        self.delete()
        print("deleting all breakpoints")
        gdb.execute("delete breakpoints")
        """

        """
        print(f"adding breakpoint BIO_read_result at {addr}")
        BIO_read_result(addr)
        """

        self.done = True

        # Python Exception <class 'gdb.error'>: Cannot execute this command while the selected thread is running.
        #gdb.execute("continue")

        return True
        return False # continue inferior

# FIXME
"""
adding breakpoint BIO_read_result at *0x000055555d496989
Breakpoint 3 at 0x55555d496989
[Switching to Thread 0x7fffd61136c0 (LWP 683605)]

Thread 28 "NetworkService" hit Breakpoint 1, 0x000055555d496944 in BIO_read ()
"""

"""
TODO find one of these

line '   0x000055555d496989 <+73>:\tmov    ecx,eax'
line '   0x000055555d49698b <+75>:\tadd    QWORD PTR [rbx+0x30],rcx'
line '   0x000055555d49698f <+79>:\tjmp    0x55555d4969b4 <BIO_read+116>'

"""

#BIO_read("BIO_read")

# https://stackoverflow.com/questions/10748501/what-are-the-best-ways-to-automate-a-gdb-debugging-session
# must specify cmdline arg for "run" when running in batch mode
gdb.execute("run")
#gdb.execute("run --user-data-dir=/home/user/src/milahu/opensubtitles-scraper/aiohttp_chromium/test/chromium-capture-http/user-data --disable-seccomp-sandbox --single-process https://httpbin.dev/drip?code=200&numbytes=5&duration=5")




class MyBreakpoint(gdb.Breakpoint):
  #def __init__(self, spec, command=""):
  #  super(MyBreakpoint, self).__init__(spec, gdb.BP_BREAKPOINT,
  #  self.command = command # not used

  def stop(self):
    # gdb.write - like print
    # gdb.decode_line() - like gdb.find_pc_line(pc)

    current_line = gdb.decode_line()
    symtline = current_line[1][0]
    #print(current_line, symtline.is_valid(), symtline.line , symtline.pc , symtline.symtab )

    sysy = symtline.symtab
    #print(sysy.filename, sysy.fullname(), sysy.is_valid() )

    sysyo = sysy.objfile
    #print(sysyo.filename, sysyo.is_valid(), sysyo.pretty_printers)
    ###print(gdb.solib_name()) # this breaks stuff??!

    sourcefilename = sysy.filename
    sourcefullpath = sysy.fullname()
    sourcelinenum = symtline.line   # somehow, it may be offset by 1, from what "list *$pc says"

    listingline = gdb.execute("list *$pc,+0", to_string=True)
    #print( "BREAK at %s:%d -- %s" % (sourcefilename, sourcelinenum, listingline) )

    llsplit = listingline.split("\n")
    listpreamble, gdbsourceline = llsplit[:2]
    addr, noneed, noneed, funcname, fileloc = listpreamble.split(" ")[:5]
    #linenum, sourceline = gdbsourceline.split("\t")[:2] # not using these - put gdb line verbatim

    outline = "[% 4s] %s % 16s:%s" % (sourcelinenum, addr, sourcefilename[-16:], gdbsourceline)
    print(outline)
    return False # continue (do not stop inferior)

#ax = MyBreakpoint("doSomething")
#bx = MyBreakpoint("myprog.c:63")

# also: python print( gdb.execute("list *$pc,+0", False, True).splitlines()[1] ) – 
