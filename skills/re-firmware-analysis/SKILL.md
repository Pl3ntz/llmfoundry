---
name: re-firmware-analysis
description: Reverse engineering firmware, extract filesystems, locate kernel, U-Boot, and update logic from firmware images with binwalk and manual analysis. Use when analyzing router, IoT, or embedded device firmware.
---

# Firmware Analysis

Extract and analyze firmware images from embedded devices (routers, IoT, cameras,
controllers). The goal is finding the filesystem, kernel, config, and update logic.

## 1. Identify the image

```bash
file firmware.bin
binwalk firmware.bin            # scan for signatures
binwalk -e firmware.bin         # extract everything
```

Signals: GZip/LZMA at known offsets, SquashFS, JFFS2, CramFS, TRX (broadcom), custom
headers. `binwalk` output is the evidence.

## 2. Extract the filesystem

```bash
binwalk -e firmware.bin          # auto-extract
# or manually, from the binwalk offset
dd if=firmware.bin of=fs.squashfs bs=1 skip=<offset>
unsquashfs fs.squashfs          # squashfs
# jffs2: use jefferson (jffs2 extractor)
# or mount read-only when possible
```

- SquashFS is the most common embedded read-only fs. `unsquashfs` extracts it.
- JFFS2 needs a special tool (`jefferson`).
- If the fs is encrypted, report it as encrypted with the evidence, don't guess content.

## 3. Find the kernel and bootloader

```bash
binwalk firmware.bin | grep -iE "kernel|uimage|gzip|lzma|uboot"
# U-Boot: strings in the header often show "U-Boot 2024" and the load address
strings firmware.bin | grep -i "uboot"
```

- U-Boot header: magic `\x27\x05\x19\x56`, load address, entry point, image name.
- Kernel is usually gzip/lzma compressed, identifiable by the compression signature.

## 4. Analyze the filesystem contents

Once extracted, look at:
- `/etc/passwd`, `/etc/shadow` → default credentials, users (a finding if default root)
- `/etc/init.d/`, `/etc/rc.d/` → startup, services, persistence
- `/www`, web server files → web interface logic, LFI/RCE surface
- `dropbear`/`sshd` keys, `/etc/config/` (OpenWrt uci), firmware update scripts
- binaries of interest → hand to the other RE skills

## 5. Update logic (how it updates)

- Find the update script (often `/sbin/sysupgrade`, `/bin/upgrade`).
- How does it validate images? Signature check? Plain overwrite?
- A missing signature check on update images is a vulnerability (unauthenticated
  firmware flash).

## Output contract

```
### FIRMWARE
- device / vendor (if known): [from header or strings]
- image format: [trx/squashfs/gzip + offsets]
- filesystem: [squashfs, extracted at <path>]

### CONTENTS OF INTEREST
- [default creds, config, services, update logic, keys]

### SECURITY NOTES
- [missing update signature, default creds, exposed services]

### NEXT STEP
- [reverse a specific binary / test update validation]
```

## Anti-delirium

- Everything comes from binwalk output or files actually extracted.
- "Encrypted filesystem" only if the scan shows no recognizable fs and you attempted
  extraction. Say what you tried.
- Default credentials are a finding only if you read the actual /etc/passwd/shadow.
- Never claim a vulnerability (missing update signature) without reading the update code.
