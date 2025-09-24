#!/system/bin/sh

# === Custom Environment Variables ===
export LD_LIBRARY_PATH={{dir}}
export PROOT_TMP_DIR={{dir}}/tmp
export TERM=xterm-256color
PATH="/bin:/sbin:/usr/bin:/usr/sbin:/usr/games:/usr/local/bin:/usr/local/sbin:{{dir}}/bin:/system/bin:\$PATH"

# Main directory for Proot setup
PROOT_MAIN={{dir}}
ROOTFS_DIR=$PROOT_MAIN/{{distro}}
PROOT_BIN=$PROOT_MAIN/proot

ARGS="--kill-on-exit"
ARGS="$ARGS -w $PWD"

for data_dir in /data/app /data/dalvik-cache \
	/data/misc/apexdata/com.android.art/dalvik-cache; do
	if [ -e "$data_dir" ]; then
		ARGS="$ARGS -b ${data_dir}"
	fi
done
unset data_dir

for system_mnt in /apex /odm /product /system /system_ext /vendor \
	/linkerconfig/ld.config.txt \
	/linkerconfig/com.android.art/ld.config.txt \
	/plat_property_contexts /property_contexts; do

	if [ -e "$system_mnt" ]; then
		system_mnt=$(realpath "$system_mnt")
		ARGS="$ARGS -b ${system_mnt}"
	fi
done
unset system_mnt

if ls -1U /storage > /dev/null 2>&1; then
	ARGS="$ARGS -b /storage"
	ARGS="$ARGS -b /storage/emulated/0:/sdcard"
else
	if ls -1U /storage/self/primary/ > /dev/null 2>&1; then
		storage_path="/storage/self/primary"
	elif ls -1U /storage/emulated/0/ > /dev/null 2>&1; then
		storage_path="/storage/emulated/0"
	elif ls -1U /sdcard/ > /dev/null 2>&1; then
		storage_path="/sdcard"
	else
		storage_path=""
	fi

	if [ -n "$storage_path" ]; then
		ARGS="$ARGS -b ${storage_path}:/sdcard"
		ARGS="$ARGS -b ${storage_path}:/storage/emulated/0"
		ARGS="$ARGS -b ${storage_path}:/storage/self/primary"
	fi
fi
unset storage_path

ARGS="$ARGS --kernel-release=6.6.30-AndroSH"

ARGS="$ARGS -b /dev"
ARGS="$ARGS -b /dev/urandom:/dev/random"
ARGS="$ARGS -b /proc"
ARGS="$ARGS -b /proc/self/fd:/dev/fd"
ARGS="$ARGS -b /proc/self/fd/0:/dev/stdin"
ARGS="$ARGS -b /proc/self/fd/1:/dev/stdout"
ARGS="$ARGS -b /proc/self/fd/2:/dev/stderr"
ARGS="$ARGS -b $PROOT_MAIN"
ARGS="$ARGS -b /sys"

# Bind /tmp to /dev/shm
if [ ! -d "$ROOTFS_DIR/tmp" ]; then
	mkdir -p "$ROOTFS_DIR/tmp"
	chmod 1777 "$ROOTFS_DIR/tmp"
fi
ARGS="$ARGS -b $ROOTFS_DIR/tmp:/dev/shm"

ARGS="$ARGS -r $ROOTFS_DIR"
ARGS="$ARGS -0"
ARGS="$ARGS --link2symlink"
ARGS="$ARGS --sysvipc"
ARGS="$ARGS -L"

if [ ! -f $PROOT_MAIN/patched ]; then
    echo "export PATH=$PATH" >> $ROOTFS_DIR/etc/profile
    echo "nameserver 1.1.1.1" > $ROOTFS_DIR/etc/resolv.conf
    mkdir -p $PROOT_MAIN/tmp
    touch $PROOT_MAIN/patched
fi

$PROOT_BIN $ARGS sh -c "/bin/login -f root"