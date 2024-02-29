#! /nix/store/9vafkkic27k7m4934fpawl6yip3a6k4h-bash-5.2-p21/bin/bash -e

if [ -x "/run/wrappers/bin/__chromium-suid-sandbox" ]
then
  export CHROME_DEVEL_SANDBOX="/run/wrappers/bin/__chromium-suid-sandbox"
else
  export CHROME_DEVEL_SANDBOX="/nix/store/xhla7mrv6fj5zcpzxrhmrpvdq3wpgvqb-ungoogled-chromium-120.0.6099.224-sandbox/bin/__chromium-suid-sandbox"
fi

# Make generated desktop shortcuts have a valid executable name.
export CHROME_WRAPPER='chromium'

# To avoid loading .so files from cwd, LD_LIBRARY_PATH here must not
# contain an empty section before or after a colon.
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH${LD_LIBRARY_PATH:+:}/nix/store/2p2di92jwcwf3fsav8zdngfn9hmdvinb-libva-2.20.0/lib:/nix/store/gdghqnck4i6jrp8bsy722903qxi89drg-pipewire-1.0.0/lib:/nix/store/8ggx8dnicpljzjcfijk8swy4l0fa2j01-wayland-1.22.0/lib:/nix/store/8yicinmsnqmlkgvmzh468bi0bsap0fix-gtk+3-3.24.39/lib:/nix/store/baqf0lfi9ip4zjhqv0w3b8mx97pz5kj4-gtk4-4.12.4/lib:/nix/store/ynac0qi3qnpb35p72may7vb3697bapad-libkrb5-1.21.2/lib"

# libredirect causes chromium to deadlock on startup
export LD_PRELOAD="$(echo -n "$LD_PRELOAD" | /nix/store/khndnv11g1rmzhzymm1s5dw7l2ld45bc-coreutils-9.4/bin/tr ':' '\n' | /nix/store/mmsb0ivm355r4l3yjbpaiirkf673n66v-gnugrep-3.11/bin/grep -v /lib/libredirect\\.so$ | /nix/store/khndnv11g1rmzhzymm1s5dw7l2ld45bc-coreutils-9.4/bin/tr '\n' ':')"

export XDG_DATA_DIRS=/nix/store/ghll7l90b4q1y9g9qiahxfkx840iwvdf-cups-2.4.7/share:/nix/store/8yicinmsnqmlkgvmzh468bi0bsap0fix-gtk+3-3.24.39/share:/nix/store/baqf0lfi9ip4zjhqv0w3b8mx97pz5kj4-gtk4-4.12.4/share:/nix/store/wvvrbl6p1s6lalc1vwii4jbz08gazdf3-adwaita-icon-theme-45.0/share:/nix/store/k4mksszws2ff3y6d7l19cvs56c1nh4nj-hicolor-icon-theme-0.17/share:/nix/store/gfp30ph6l28vz62ggcl7j2b5sp22j1hy-gsettings-desktop-schemas-45.0/share/gsettings-schemas/gsettings-desktop-schemas-45.0:/nix/store/8yicinmsnqmlkgvmzh468bi0bsap0fix-gtk+3-3.24.39/share/gsettings-schemas/gtk+3-3.24.39:/nix/store/baqf0lfi9ip4zjhqv0w3b8mx97pz5kj4-gtk4-4.12.4/share/gsettings-schemas/gtk4-4.12.4${XDG_DATA_DIRS:+:}$XDG_DATA_DIRS

# Mainly for xdg-open but also other xdg-* tools (this is only a fallback; $PATH is suffixed so that other implementations can be used):
export PATH="$PATH${PATH:+:}/nix/store/51jay5z2f95972gyidah3zc4wpzsn957-xdg-utils-unstable-2022-11-06/bin"

#exec gdb -x gdbinit.txt --args \
#exec r2 -d \
#exec python
#exec gdb --batch -x gdb_chromium.py --args \
#exec gdb --batch -x gdb_chromium.py --args \
#exec gdb --command=gdb_chromium.gdb --args \
#exec gdb --batch --command=gdb_chromium.gdb --args \


#--batch --source lldbinit.txt \

exec ./lldb_runner.py "/nix/store/nsx8iznrwqwb4mwy3l9n4alvcd381z5k-ungoogled-chromium-unwrapped-120.0.6099.224/libexec/chromium/chromium"  ${NIXOS_OZONE_WL:+${WAYLAND_DISPLAY:+--ozone-platform-hint=auto --enable-features=WaylandWindowDecorations}}  "$@"

exec /nix/store/vpqd2k73ya6fxkwmy6bznc0xbiah2nq6-lldb-16.0.6/bin/lldb \
--repl --source-before-file lldbinit.txt \
-- \
"/nix/store/nsx8iznrwqwb4mwy3l9n4alvcd381z5k-ungoogled-chromium-unwrapped-120.0.6099.224/libexec/chromium/chromium"  ${NIXOS_OZONE_WL:+${WAYLAND_DISPLAY:+--ozone-platform-hint=auto --enable-features=WaylandWindowDecorations}}  "$@" 

exec "/nix/store/nsx8iznrwqwb4mwy3l9n4alvcd381z5k-ungoogled-chromium-unwrapped-120.0.6099.224/libexec/chromium/chromium"  ${NIXOS_OZONE_WL:+${WAYLAND_DISPLAY:+--ozone-platform-hint=auto --enable-features=WaylandWindowDecorations}}  "$@" 
