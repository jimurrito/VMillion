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
    AStrt: bool, Host: str, vCPU: str, RAM: str, Net: str, DiskPath: str, Log: str
):
    build = open("templates/virt-install-win.temp", "r").read()
    vCPU = str(vCPU)
    RAM = str(RAM)
    if AStrt == True:
        AStrt = "--autostart"
    else:
        AStrt = ""
    build = build.replace("$Host$", Host)
    build = build.replace("$vCPU$", vCPU)
    build = build.replace("$RAM$", RAM)
    build = build.replace("$Net$", Net)
    build = build.replace("$DiskPath$", DiskPath)
    build = build.replace("$AStrt$", AStrt)
    os.system(f"{build} > {Log}")
