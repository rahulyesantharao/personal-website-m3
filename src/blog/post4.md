Recently, I dual-booted my computer (Razer Blade 14" 2017, Intel 7700HQ - GTX1060) with Arch Linux, and I wanted to document the process here to make it easier for any others who are planning on a similar process. Note that this is for a UEFI machine that already runs Windows 10 (although the instructions may easily translate to some other setups).

## Reading
Before beginning the dual boot process, I decided to first read about the boot process and Linux in general; although not strictly necessary, this reading was interesting and helped me understand all the steps involved in the dual boot process. I have listed some basic links I would recommend reading before, in order to get a clear understanding the boot process and related technologies.

 - [https://en.wikipedia.org/wiki/Booting](https://en.wikipedia.org/wiki/Booting)
 - [https://en.wikipedia.org/wiki/Firmware](https://en.wikipedia.org/wiki/Firmware)
 - [https://en.wikipedia.org/wiki/Disk_partitioning](https://en.wikipedia.org/wiki/Disk_partitioning)
 - [https://en.wikipedia.org/wiki/BIOS](https://en.wikipedia.org/wiki/BIOS)
 - [https://en.wikipedia.org/wiki/Master_boot_record](https://en.wikipedia.org/wiki/Master_boot_record)
 - [https://en.wikipedia.org/wiki/Unified_Extensible_Firmware_Interface](https://en.wikipedia.org/wiki/Unified_Extensible_Firmware_Interface)
 - [https://en.wikipedia.org/wiki/GUID_Partition_Table](https://en.wikipedia.org/wiki/GUID_Partition_Table)
 - [https://www.cs.tau.ac.il/telux/lin-club_files/linux-boot/slide0000.htm](https://www.cs.tau.ac.il/telux/lin-club_files/linux-boot/slide0000.htm)

## Windows Preparation
First, just to be safe, it is important to completely back up any important files you have saved on your computer. 

Then, open up *Disk Management* (open Command Prompt as Administrator and type in `diskmgmt.msc`) (see the figure below) and create space for the Linux installation. There should be at least 3 basic partitions: EFI System Partition, OEM, and Windows (the main partition that takes most of the space). In addition, there may be an extra recovery partition - beyond the first 3, you can choose whether or not to delete the extra partitions (consider the warranty and other aspects specific to your computer, I chose to leave my recovery partition). Choose the large Windows partition, right click it, and choose shrink - the amount by which you shrink is the amount of space you will have for your Linux installation. This new space will show up as unpartitioned space - this is what we want.

![Disk Management](https://rahulyesantharao.com/resources/img/diskmgmt.min.png "Disk Management Setup")

Now, we will prepare for the actual Linux boot process. First, [**turn off Windows Fast Startup**](https://www.tenforums.com/tutorials/4189-turn-off-fast-startup-windows-10-a.html). Then, hold down shift and press the restart button to open the troubleshooting menu. Choose Troubleshoot > Advanced Options > UEFI Firmware Settings. Then, on restart, the UEFI options will open. Disable Intel Fast Boot and Secure Boot (details [here](https://wiki.archlinux.org/index.php/Dual_boot_with_Windows#UEFI_Secure_Boot)).

## Installation Media
Download an Arch Linux ISO from the [Downloads Page](https://www.archlinux.org/download/) (verify the checksums, noting the [Master Signing Keys](https://www.archlinux.org/master-keys/)). Then, download [Rufus](https://rufus.akeo.ie/), a USB drive formatting utility (alternatively, you can use `dd` if you have a machine running Linux or MacOS). Get a USB drive that doesn't have any data you need (it will be wiped by the boot drive formatting process), and plug it in. Start up Rufus; it should automatically recognize the USB drive. After ascertaining that it has the correct drive, choose the Arch Linux ISO and start the format process (I also chose FAT32, the UEFI/GPT partition scheme, check device for bad blocks with 1 pass and unchecked quick format). Make sure to choose *DD Image* mode after choosing Start (see more [here](https://wiki.archlinux.org/index.php/USB_flash_installation_media#Using_Rufus)).

## Booting Into Linux
Plug in the USB (the computer will not recognize it because of the DD formatting). Restart Windows, and press the correct key to go into the Boot Menu (on the Razer Blade, smash F12). In the Boot Menu, choose your USB (will show up as something relating to EFI USB). In the Arch Linux boot screen that shows up next, choose the first default option, "Arch Linux archiso x86_64 UEFI USB". Now, we are entered into an Arch Linux shell running off the USB - it will recognize the laptop's internal hard drive as an attached device.

## Setting up for Install
### Connect to WiFi

    #!bash
    $ iw dev # Get WiFi interface name
    $ wifi-menu # Open graphical interface to select WiFi network
    $ ping google.com # Check connection, might take a few seconds

### Create Partitions 
Use `lsblk -f` or `fdisk -l` to identify the [block devices](https://unix.stackexchange.com/a/259200). You should see at least two devices (the USB and the internal hard drive) - identify the name (e.g. `/dev/sda` or `/dev/nvme0n1`) of your internal hard drive. This is the device file where the hard drive is mounted.

We need to create 3 partitions for the Linux installation - the main filesystem, the boot partition, and the swap partition. We will now use `gdisk` to create the partitions:

    #!bash
    $ gdisk /dev/nvme0n1 # Open gdisk partitioning utility
    $ n # Create new partition (for boot)
    $ <Enter> # Use default partition number
    $ <Enter> # Automatically starts at beginning of unallocated space
    $ +200MB # Set space for the boot partition
    $ 8300 # Hex code for Linux filesystem
    $ n # Create new partition (for swap partition)
    $ <Enter> # Use default partition number
    $ <Enter> # Automatically starts at beginning of unallocated space
    $ +8GB # Size of the swap partition (can also use 16 GB)
    $ 8200 # Hex code for Linux swap partition
    $ n # Create new partition (for filesystem)
    $ <Enter> # Use default partition number
    $ <Enter> # Automatically starts at beginning of unallocated space
    $ <Enter> # Use the rest of the space
    $ 8300 # Hex code for Linux filesystem
    $ w # Write changes
    $ Y # Confirm

Now, use `gdisk -l /dev/nvme0n1` to find the number of the swap partition.

### Encrypt Filesystem
First, [securely wipe the data on the machine](https://wiki.archlinux.org/index.php/Securely_wipe_disk) to [prepare](https://wiki.archlinux.org/index.php/Dm-crypt/Drive_preparation) for the encryption. We do this as follows (where `X` refers to the partition number of the partition(s) you wish to wipe (at minimum, do the main filesystem partition)).

    #!bash
    $ cryptsetup open --type plain -d /dev/urandom /dev/nvme0n1pX to_be_wiped # opens a temporary crypt device
    $ lsblk # Check that there is a crypt device under /dev/nvme0n1pX
    $ dd if=/dev/zero of=/dev/mapper/to_be_wiped status=progress # Wipes the drive with /dev/zero
    $ cryptsetup close to_be_wiped # Close the temporary crypt device

Now, we will encrypt the partition. See the [related](https://wiki.archlinux.org/index.php/Dm-crypt/Device_encryption) [Arch](https://wiki.archlinux.org/index.php/Dm-crypt/Specialties) [wiki](https://wiki.archlinux.org/index.php/Dm-crypt/Encrypting_a_non-root_file_system#Partition) [pages](https://wiki.archlinux.org/index.php/Dm-crypt/Encrypting_an_entire_system#Simple_partition_layout_with_LUKS) for details. We use `X` to refer to the partition number of the Linux root filesystem (third partition created above). Use [this answer](https://unix.stackexchange.com/questions/254017/how-to-interpret-cryptsetup-benchmark-results) to choose encryption options.

    #!bash
    $ cryptsetup benchmark # Choose your cipher settings
    $ cryptsetup -y -v luksFormat --type luks2 /dev/nvme0n1pX # Set up cryptdevice on the partition
    $ cryptsetup open /dev/nvme0n1pX cryptroot # Open the device as cryptroot
    $ mkfs -t ext4 -L "Arch Linux" /dev/mapper/cryptroot # Make the filesystem on the encrypted device
    $ mount /dev/mapper/cryptroot /mnt # Mount the filesystem to /mnt (/mnt is on the USB)

Now, check the mapping to make sure it works.

    #!bash
    $ umount /mnt
    $ cryptsetup close cryptroot
    $ cryptsetup open /dev/nvme0n1pX cryptroot
    $ mount /dev/mapper/cryptroot /mnt

### Turn on Swap Partition
We refer to the swap partition created above as `Y`.

    #!bash
    $ mkswap -L "Linux Swap" /dev/nvme0n1pY # Make the swap partition
    $ swapon /dev/nvme0n1pY # Turn on the swap partition
    $ free -m # Check whether swap is on

### Create Boot Partition
We refer to the boot partition created above as `Z`. 

    #!bash
    $ mkfs -t ext4 /dev/nvme0n1pZ # Create boot partition filesystem
    $ mkdir /mnt/boot # Create boot mount point
    $ mount /dev/nvme0n1pZ /mnt/boot
    $ mkdir /mnt/boot/efi # Create efi boot folder
    $ gdisk -l # Find the partition number of the existing EFI partition (from Windows) - U
    $ mount /dev/nvme0n1pU /mnt/boot/efi # Mount the EFI partition

## Installing Arch Linux
Use [pacstrap](https://git.archlinux.org/arch-install-scripts.git/tree/pacstrap.in) to install the basic system:

    #!bash
    $ pacstrap /mnt base # Just install the basic set of packages

### Configure the System
Create an [fstab](https://wiki.archlinux.org/index.php/Fstab) file for the system, using [UUID](https://wiki.archlinux.org/index.php/Persistent_block_device_naming#by-uuid) naming:

    #!bash
    $ genfstab -pU /mnt >> /mnt/etc/fstab

Make sure that `/mnt/etc/fstab` lists `/boot` and `/boot/efi` as filesystems. If it doesn't, you will have to add them manually, look that up online. Use `ls -l /dev/disk/by-uuid/`. 
Optionally, change `relatime` to `noatime` on SSD disks to reduce the wear and tear.

## Boot into the Arch Install
Arch Linux is now completely installed on the system. We are ready to begin setting up the system directly. First, `chroot` into the newly installed system.

    #!bash
    $ arch-chroot /mnt

### [Basic System Setup](https://wiki.archlinux.org/index.php/installation_guide#Configure_the_system)
First we setup the time system. Refer to [Arch Wiki Time](https://wiki.archlinux.org/index.php/time) for more information.

    #!bash
    $ ln -s /usr/share/zoneinfo/<Region>/<City> /etc/localtime # Set the local timezone
    $ hwclock --systohc # Create /etc/adjtime to synchronize the hardware clock

Now, we set the locale. Uncomment `en_US.UTF-8 UTF-8` in `/etc/locale.gen` and run 

    #!bash
    $ locale-gen

Then, set `LANG=en_US.UTF-8` in `/etc/locale.conf`
Now, we set the hostname with

    #!bash
    $ echo MYHOSTNAME > /etc/hostname

and update [`/etc/hosts`](http://man7.org/linux/man-pages/man5/hosts.5.html)

    #!text
    127.0.0.1       localhost
    ::1             localhost
    127.0.1.1       MYHOSTNAME.localdomain MYHOSTNAME # optional, as far as I can tell

See [Arch network configuration](https://wiki.archlinux.org/index.php/Network_configuration) for more information.

Finally, reset the `root` password:

    #!bash
    $ passwd

### [Bootloader (GRUB) Setup](https://wiki.archlinux.org/index.php/GRUB) and Initial Boot Configuration
Install the relevant packages:

    #!bash
    pacman -Syu grub efibootmgr dosfstools

Now, we will make sure all of the partitions are properly mounted.

    #!bash
    $ mount -a # Mount all of the partitions listed in fstab
    $ lsblk # List block devices, and check that /, /boot, /boot/efi are listed

If they are properly mounted, we will edit [`/etc/mkinitcpio.conf`](https://wiki.archlinux.org/index.php/mkinitcpio) to include relevant hooks and kernel parameters.

    #!text
    HOOKS = (... keymap encrypt filesystems keyboard ...)

We will now generate the [initrd](https://www.ibm.com/developerworks/library/l-initrd/index.html) with 

    #!bash
    $ mkinitcpio -p linux

Now, we will setup GRUB by setting the following in `/etc/default/grub` (where `<device-id>` is the [UUID](https://wiki.archlinux.org/index.php/persistent_block_device_naming#by-uuid) of the encrypted partition from `ls -l /dev/disk/by-uuid/`):

    #!text
    GRUB_CMDLINE_LINUX="cryptdevice=UUID=<device-id>:cryptroot
    GRUB_CMDLINE_LINUX_DEFAULT="quiet pci=nomsi"
    GRUB_ENABLE_CRYPTODISK=y

Install GRUB and generate the config file with

    #!bash
    $ grub-install --target=x86_64-efi --efi-director=/boot/efi --bootloader-id=grub
    $ grub-mkconfig -o /boot/grub/grub.cfg # GRUB configuration

Now, install `intel-ucode` in order to [enable Intel microcode](https://wiki.archlinux.org/index.php/Microcode#Enabling_Intel_microcode_updates). 

    #!bash
    $ pacman -S intel-ucode # Install relevant package
    $ grub-mkconfig -o /boot/grub/grub.cfg # regenerate GRUB configuration to use intel-ucode

Also install `os-prober` so that Windows will be properly set in GRUB on reboot (alternatively, you could create a Windows entry in the GRUB config manually).

    #!bash
    $ pacman -S os-prober

### WiFi Setup
Before starting up the new machine, we will also install necessary packages to connect to WiFi on restart. We will use [`netctl`](https://wiki.archlinux.org/index.php/netctl) to manage the WiFi connection.
First, we install [WPA Supplicant](https://wiki.archlinux.org/index.php/WPA_supplicant) to manage secure WiFi connections.

    #!bash
    $ pacman -S wpa_supplicant
    $ cp /etc/netctl/examples/wireless-wpa /etc/netctl/wireless-wpa # copy the interface file
    $ vim /etc/netctl/wireless-wpa # fill out the relevant fields
    $ wpa_passphrase SSID passphrase # hash passphrase for network

Copy the `psk` field from the `wpa_passphrase` command as the `Key` in the `wireless-wpa` profile.

### Finish up
Finally, unmount everything and reboot the system - go back into Arch.

    #!bash
    $ exit # exit out of chroot back to the archiso 
    $ umount -R /mnt # unmount all the devices
    $ reboot

You will now boot directly into the Arch install (rather than the `archiso` on the USB). 
There is some basic setup remaining. First, run `os-prober` and update the GRUB config with

    #!bash
    $ os-prober # detects the Windows installation and adds it to GRUB config
    $ grub-mkconfig -p /boot/grub/grub.cfg

Then, make sure you can connect to WiFi with `netctl`.

    #!bash
    $ sudo netctl start wireless-wpa # use the profile created above
    $ ping google.com # may take a few moments

Finally, create a new (non-root) user for general use.

    #!bash
    $ useradd -m -G wheel <username> # Create user
    $ passwd <username> # Set password

You should also set up [`sudo`](https://wiki.archlinux.org/index.php/sudo) and use `visudo` to allow the `wheel` group to use sudo.

Restart one more time, and make sure that Windows is listed as an option in the initial GRUB boot window. Choose to boot into it and make sure everything works. Notably, the clock will be off because of the hardware clock settings in Linux - to remedy this, see [here](https://wiki.archlinux.org/index.php/time#UTC_in_Windows). You will have to use `regedit` to add the `DWORD` 

    #!text
    HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\TimeZoneInformation\RealTimeIsUniversal

with value `1` to the registry. In addition, turn off Internet time synchronization in *Control Panel > Clock and Region > Date and Time > Internet Time*.
Reboot to put these changes into effect.

Check back for Part 2 to read about basic system configuration, including (but not limited to):

 - NVIDIA drivers
 - [Turn on TRIM](https://wiki.archlinux.org/index.php/Dm-crypt/Specialties#Discard.2FTRIM_support_for_solid_state_drives_.28SSD.29)
 - Store encrypt key on disk
 - X setup
