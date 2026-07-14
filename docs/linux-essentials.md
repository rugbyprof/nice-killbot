# Linux Essentials

## 2.1 Moving Around the Filesystem

```bash
pwd                 # print current directory
ls -lah              # list files (long, all, human-readable sizes)
cd projects/         # move into a directory
cd ..                # up one level
cd ~                 # jump to home directory
cd -                 # jump back to previous directory
                     #  (griffin learned this from claude this summer but it different than ..?)
```

## 2.2 Working with Files and Directories

```bash
mkdir -p projects/smartcar-ir   # create a directory (and parents)
cp file.py backup.py             # copy a file
cp -r dir1/ dir2/                # copy a directory recursively
mv old.py new.py                 # move/rename
rm file.py                       # delete a file
rm -r old_project/               # delete a directory recursively (careful!)
find . -name "*.py"              # find files by name
nano main.py                     # simple terminal text editor
cat main.py                      # print a file's contents
less main.py                     # scroll through a file (q to quit)
```

## 2.3 System Info and Processes

```bash
hostname             # this machine's name
hostname -I           # this machine's IP address(es)
df -h                 # disk usage
htop                  # live process viewer (q to quit)
top                   # like htop, always available
ps aux                # snapshot of running processes
kill <pid>             # stop a process by PID
```

## 2.4 SSH

```bash
ssh username@hostname.local        # connect
ssh -v username@hostname.local     # connect with debug output (auth failures, etc.)
exit                                # disconnect
scp file.py username@hostname.local:~/projects/smartcar-ir/   # copy file to Pi
scp username@hostname.local:~/projects/smartcar-ir/file.py .  # copy file from Pi
```

If a connection hangs or is refused, check that the Pi is powered on,
connected to Wi-Fi, and has had a minute to finish booting.

## 2.5 SSH Keys

Password logins work fine for this class, but keys are faster and are
worth knowing:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"   # generate a keypair (press Enter for defaults)
ssh-copy-id username@hostname.local                  # install your public key on the Pi
ssh username@hostname.local                          # now connects without a password
```

Your private key (`~/.ssh/id_ed25519`) never leaves your laptop.
Only the public key (`~/.ssh/id_ed25519.pub`) gets copied to the Pi.

## 2.6 Wireless / Network Debugging

Useful when the Pi "disappears" from the network or won't connect to
Wi-Fi:

```bash
ip a                          # list network interfaces and their IP addresses
ip link show wlan0            # is the Wi-Fi interface up?
nmcli device status           # NetworkManager's view of all interfaces
nmcli device wifi list        # scan and list nearby Wi-Fi networks
sudo nmcli device wifi connect "SSID" password "PASSWORD"  # connect manually
iw dev wlan0 link             # current connection + signal strength
sudo rfkill list              # is Wi-Fi blocked in software/hardware?
sudo rfkill unblock wifi       # un-block it if so
```

Testing connectivity and finding devices on the network:

```bash
ping 8.8.8.8                  # is there internet access at all?
ping hostname.local            # does the Pi's hostname resolve and respond?
arp -a                         # devices this machine has already talked to on the LAN
sudo nmap -sn 192.168.1.0/24   # scan the whole subnet for live devices (adjust to your network)
```

`nmap` isn't installed by default:

```bash
sudo apt install -y nmap
```

Use it when `hostname.local` won't resolve — scan the subnet, look for
the Pi's MAC vendor (Raspberry Pi Foundation) in the results, and SSH
to that IP directly.

Watching logs live while debugging a flaky connection:

```bash
journalctl -u NetworkManager -f
```
