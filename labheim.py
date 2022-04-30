from datetime import datetime
import os
import re


def DocPrep(
    Type: int = 99,
    Host: str = "VMDly",
    Name: str = "Administrator",
    Pwd: str = "Password1",
    DiskPath: str = "",
    ISOPATH: str = "",
    ISOSUM: str = "",
    Src: str = "templates/autounattend.xml",
):
    doc = (open(Src, "r")).read()
    if Type != 99:
        if Type == 0:
            FLC = open("templates/FLC-Vanilla.xml", "r").read()
        if Type == 1:
            FLC = open("templates/FLC-DJ.xml", "r").read()
        doc = doc.replace("$FLC$", FLC)
    doc = doc.replace("$HOST$", Host)
    doc = doc.replace("$UserName$", Name)
    doc = doc.replace("$Password$", Pwd)
    doc = doc.replace("$DiskPath$", DiskPath)
    doc = doc.replace("$osPath$", ISOPATH)
    doc = doc.replace("$osSum$", ISOSUM)
    return doc


def VLog(
    Header: str = "Header",
    MSG: str = "Message",
    DIR: str = "log",
):
    Time = (datetime.now()).isoformat(timespec="seconds")
    Output = f"[{Time}]-[{Header}]-[{MSG}]"
    (open(f"./{DIR}", "a")).write("\n")
    (open(f"./{DIR}", "a")).write(Output)
    print(Output)


def SelectMatrix(Type: int = 0, IN: int = 0, ROOT: str = "/cd_disk/KVM/iso/"):
    if Type == 0:
        if IN == 0:
            a = "Windows-Server 19"
            b = f"{ROOT}winserver_2019.iso"
        if IN == 1:
            a = "Windows-Server 22"
            b = f"{ROOT}winserver_2022.iso"
        if IN == 2:
            a = "Windows 10"
            b = f"{ROOT}windows10_21h2_ENT.iso"
        if IN == 3:
            a = "Ubuntu-Server"
            b = f"{ROOT}ubuntu_server_21.10_amd64.iso"
        if IN == 4:
            a = "Ubuntu-Desktop"
            b = f"{ROOT}ubuntu_desktop_21.04_amd64.iso"
        c = open(f"{b.replace('.iso','.hash')}", "r").read()
        return a, b, c

    if Type == 1:
        if IN == 0:
            a = "Vanilla"
        if IN == 1:
            a = "Domain Joined"
        if IN == 2:
            a = "Domain Controller"
        return a


def Packer(cmd: str, Path: str = "./", Plog: str = "PackerLog"):
    Tlog = "tlog"
    if cmd == "build":
        os.system(f"PACKER_LOG=1 packer build {Path} | tee {Plog} {Tlog}")
        while True:
            try:
                re.search("Error", open(Tlog, "r").read()).group(0)
                try:
                    re.search("permission denied", open(Tlog, "r").read()).group(0)
                    c = 2
                    break
                except:
                    c = 1
                    break
            except:
                pass
            try:
                re.search(
                    "Builds finished\. The artifacts of successful builds are:",
                    open(Tlog, "r").read(),
                ).group(0)
                c = 0
                break
            except:
                pass
        os.remove(Tlog)
    else:
        os.system(f"packer {cmd} {Path} | tee {Plog} {Tlog} ")
        try:
            re.search("Error", open(Tlog, "r").read()).group(0)
            c = 1
        except:
            c = 0
        os.remove(Tlog)
    return c


def VMBuilder(
    auto_start: bool,
    hostname: str,
    v_cpus: str,
    ram: str,
    network_bridge: str,
    disk_path: str,
    log_file: str,
) -> None:
    """
    Formats and runs the Build VM command

    Parameters
    ----------
    auto_start : bool
        Set the VM to autostart
    hostname : str
        The Hostname of the VM
    v_cpus : str
        The number of vCPUs
    ram : str
        The amount of RAM
    network_bridge : str
        The type of network interface
    disk_path : str
        The path to the ISO
    log_file : str
        The path to the log file

    Returns
    -------
    None
    """

    command = (
        open("templates/virt-install-win.temp", "r")
        .read()
        .replace("$Host$", str(hostname))
        .replace("$vCPU$", str(v_cpus))
        .replace("$RAM$", str(ram))
        .replace("$Net$", str(network_bridge))
        .replace("$DiskPath$", str(disk_path))
        .replace("$AStrt$", "--autostart" if auto_start else "")
        + f" > {str(log_file)}"
    )

    os.system(command)
