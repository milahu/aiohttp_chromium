Dump of assembler code for function BIO_read: ; int BIO_read(BIO *bio, void *buf, int len)
   0x000055555d496940 <+0>:     push   rbp ; BIO *bio
   0x000055555d496941 <+1>:     mov    rbp,rsp
   0x000055555d496944 <+4>:     push   rbx ; void *buf
   0x000055555d496945 <+5>:     push   rax ; int len

   0x000055555d496946 <+6>:     test   rdi,rdi ; bio == NULL
   0x000055555d496949 <+9>:     je     0x55555d496991 <BIO_read+81> ; OPENSSL_PUT_ERROR(BIO, BIO_R_UNSUPPORTED_METHOD); return -2;

   0x000055555d49694b <+11>:    mov    rbx,rdi
   0x000055555d49694e <+14>:    mov    rax,QWORD PTR [rdi]
   0x000055555d496951 <+17>:    test   rax,rax ; bio->method == NULL
   0x000055555d496954 <+20>:    je     0x55555d496991 <BIO_read+81> ; OPENSSL_PUT_ERROR(BIO, BIO_R_UNSUPPORTED_METHOD); return -2;

   0x000055555d496956 <+22>:    mov    rax,QWORD PTR [rax+0x18]
   0x000055555d49695a <+26>:    test   rax,rax ; bio->method->bread == NULL
   0x000055555d49695d <+29>:    je     0x55555d496991 <BIO_read+81> ; OPENSSL_PUT_ERROR(BIO, BIO_R_UNSUPPORTED_METHOD); return -2;

   0x000055555d49695f <+31>:    cmp    DWORD PTR [rbx+0x8],0x0
   0x000055555d496963 <+35>:    je     0x55555d4969bb <BIO_read+123> ; OPENSSL_PUT_ERROR(BIO, BIO_R_UNINITIALIZED); return -2;

   0x000055555d496965 <+37>:    test   edx,edx ; len <= 0
   0x000055555d496967 <+39>:    jle    0x55555d4969d6 <BIO_read+150> ; return 0

; ???
   0x000055555d496969 <+41>:    lea    rcx,[rip+0xfffffffffa9e14c0]        # 0x555557e77e30 <__typeid__ZTSFiP6bio_stPciE_global_addr>

      => 0x0000555557e77e30 <+0>:     jmp    0x55555d99c630 <_ZN3net16SocketBIOAdapter14BIOReadWrapperEP6bio_stPci.cfi>

   0x000055555d496970 <+48>:    mov    rdi,rax
   0x000055555d496973 <+51>:    sub    rdi,rcx
   0x000055555d496976 <+54>:    ror    rdi,0x3
   0x000055555d49697a <+58>:    cmp    rdi,0x4 ; ret > 0 (?)
   0x000055555d49697e <+62>:    ja     0x55555d4969da <BIO_read+154> ; ??? throw error?

   0x000055555d496980 <+64>:    mov    rdi,rbx
   ; rdi == 58652142079206
   ; rbx == 58652142418392
   0x000055555d496983 <+67>:    call   rax ; int ret = bio->method->bread(bio, buf, len);

      rbp == bio
      rbx == buf
      rax == len

      eax == ret

      print $eax
      5

      (gdb) print (char[5]) *($rbx)
      $12 = "H\027H\001X"

      (gdb) print (char[$eax]) *($rbx)
      syntax error in expression

      print $eax
      62

      print (char[62]) *($rbx)
      $16 = "H\027H\001X5\000\000\001\000\000\000\001", '\000' <repeats 15 times>, "\003\000\000\0000\0205\001X5\000\000\000\000\000\000\000\000\000\000\240\026\000\000\000\000\000\000\262\a\000\000\000"

      x/62bc $rbx
      0x3558041d39d8: 72 'H'  23 '\027'       72 'H'  1 '\001'        88 'X'  53 '5'  0 '\000'        0 '\000'
      0x3558041d39e0: 1 '\001'        0 '\000'        0 '\000'        0 '\000'        1 '\001'        0 '\000'        0 '\000'        0 '\000'
      0x3558041d39e8: 0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'
      0x3558041d39f0: 0 '\000'        0 '\000'        0 '\000'        0 '\000'        3 '\003'        0 '\000'        0 '\000'        0 '\000'
      0x3558041d39f8: 48 '0'  16 '\020'       53 '5'  1 '\001'        88 'X'  53 '5'  0 '\000'        0 '\000'
      0x3558041d3a00: 0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'
      0x3558041d3a08: -96 '\240'      22 '\026'       0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'        0 '\000'
      0x3558041d3a10: -78 '\262'      7 '\a'  0 '\000'        0 '\000'        0 '\000'        0 '\000'

      print *($rbx)@62
      $15 = {21501768, 13656, 1, 1, 0, 0, 0, 3, 20254768, 13656, 0, 0, 5792, 0, 1970, 0, -269488145, 0, 1479868416, 808393988, 0, 0, 67661856, 13656, 0, 0, 69776488, 13656, 1, 13656, 71599232, 13656, 71599232, 13656, 71599256, 13656, 0, 1, 0 <repeats 18 times>, 2147483647, 1, 1690319384, 21845, 0, 0}



   0x000055555d496985 <+69>:    test   eax,eax ; ret > 0
   0x000055555d496987 <+71>:    jle    0x55555d4969b4 <BIO_read+116> ; if (ret <= 0) -> return

; else: (ret > 0)
   0x000055555d496989 <+73>:    mov    ecx,eax
   0x000055555d49698b <+75>:    add    QWORD PTR [rbx+0x30],rcx ; bio->num_read += ret;
   0x000055555d49698f <+79>:    jmp    0x55555d4969b4 <BIO_read+116> ; -> return

   0x000055555d496991 <+81>:    lea    rcx,[rip+0xfffffffff97472ea]        # 0x555556bddc82 <.src.llvm.2087529851984499442>
   0x000055555d496998 <+88>:    mov    edi,0x11
   0x000055555d49699d <+93>:    xor    esi,esi
   0x000055555d49699f <+95>:    mov    edx,0x73
   0x000055555d4969a4 <+100>:   mov    r8d,0x7c
   0x000055555d4969aa <+106>:   call   0x55555d4aa000 <ERR_put_error>
   0x000055555d4969af <+111>:   mov    eax,0xfffffffe ; return code -2 (?)

   0x000055555d4969b4 <+116>:   add    rsp,0x8
   0x000055555d4969b8 <+120>:   pop    rbx
   0x000055555d4969b9 <+121>:   pop    rbp
   0x000055555d4969ba <+122>:   ret ; return

   0x000055555d4969bb <+123>:   lea    rcx,[rip+0xfffffffff97472c0]        # 0x555556bddc82 <.src.llvm.2087529851984499442>
   0x000055555d4969c2 <+130>:   mov    edi,0x11
   0x000055555d4969c7 <+135>:   xor    esi,esi
   0x000055555d4969c9 <+137>:   mov    edx,0x72
   0x000055555d4969ce <+142>:   mov    r8d,0x80
   0x000055555d4969d4 <+148>:   jmp    0x55555d4969aa <BIO_read+106>

; throw error?
   0x000055555d4969d6 <+150>:   xor    eax,eax
   0x000055555d4969d8 <+152>:   jmp    0x55555d4969b4 <BIO_read+116>
   0x000055555d4969da <+154>:   ud1    eax,DWORD PTR [eax+0x2]
