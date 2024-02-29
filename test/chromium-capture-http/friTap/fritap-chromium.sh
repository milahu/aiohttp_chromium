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

# original
#exec "/nix/store/nsx8iznrwqwb4mwy3l9n4alvcd381z5k-ungoogled-chromium-unwrapped-120.0.6099.224/libexec/chromium/chromium"  ${NIXOS_OZONE_WL:+${WAYLAND_DISPLAY:+--ozone-platform-hint=auto --enable-features=WaylandWindowDecorations}}  "$@" 

# no: PermissionError: [Errno 1] Operation not permitted
# _socket.socket.__init__(self, family, type, proto, fileno)
#--full_capture \

#--debugoutput \

#exec /nix/store/jc5v1851y1saxsbcwpllik1j47ih88b5-fritap-1.1.0/bin/friTap \

set -x

echo "starting chromium"
#chromium --user-data-dir=$PWD/chromium-user-data --disable-seccomp-sandbox --single-process &
chromium --user-data-dir=$PWD/chromium-user-data --disable-seccomp-sandbox --single-process --no-sandbox &
chromium_pid=$!
echo "chromium_pid $chromium_pid"

echo "waiting for chromium to start"
sleep 5

# no. grepping "ps" for "user-data-dir" is unstable
if false; then
  # get pid of main chromium process
  # can be different than chromium_pid (rarely? never?)
  chromium_pid_2=$(ps -AF | grep user-data-dir=$PWD/chromium-user-data | head -n1 | awk '{ print $2 }')
  if [[ "$chromium_pid" != "$chromium_pid_2" ]]; then
    echo "chromium_pid changed from $chromium_pid to $chromium_pid_2"
    $chromium_pid_2
  fi
fi

echo "starting fritap"
#python $PWD/friTap.py \
friTap \
--pcap $PWD/frida-tap.pcap \
$chromium_pid &
fritap_pid=$!
echo "fritap_pid $fritap_pid"

echo "waiting for fritap"
sleep 10

url="https://httpbin.org/get"
echo "opening url $url"
chromium --user-data-dir=$PWD/chromium-user-data "$url"
echo "waiting for chromium"
sleep 5

echo "killing chromium $chromium_pid"
kill $chromium_pid

echo "killing fritap"
kill $fritap_pid

exit

# no. grepping "ps" for "user-data-dir" is unstable
if false; then
  if [[ "$chromium_pid" != "$chromium_pid_2" ]]; then
    echo "killing chromium $chromium_pid_2"
    kill $chromium_pid_2
  fi
fi

exit

set -x
exec python $PWD/friTap.py \
--spawn \
--pcap $PWD/frida-tap.pcap \
"/nix/store/nsx8iznrwqwb4mwy3l9n4alvcd381z5k-ungoogled-chromium-unwrapped-120.0.6099.224/libexec/chromium/chromium $*"

#chromium --disable-seccomp-sandbox --single-process --user-data-dir=$PWD/chromium-user-data

if false; then
	# dump env
	echo PATH $PATH
	echo XDG_DATA_DIRS $XDG_DATA_DIRS
	echo LD_PRELOAD $LD_PRELOAD
	echo LD_LIBRARY_PATH $LD_LIBRARY_PATH
	echo CHROME_WRAPPER $CHROME_WRAPPER
	exit
fi

#exec gdb -tui -ex=r --args \
#exec gdb -ex=r --args \
#exec gdb -x=gdb.py --args \
exec /nix/store/mksx9gbwcdbks2py01ji0xgnxxhyzwdf-ddd-3.3.12/bin/ddd --args \
"/nix/store/nsx8iznrwqwb4mwy3l9n4alvcd381z5k-ungoogled-chromium-unwrapped-120.0.6099.224/libexec/chromium/chromium" \
--disable-seccomp-sandbox \
--single-process \
--user-data-dir=$PWD/chromium-user-data \
${NIXOS_OZONE_WL:+${WAYLAND_DISPLAY:+--ozone-platform-hint=auto --enable-features=WaylandWindowDecorations}}  "$@"
