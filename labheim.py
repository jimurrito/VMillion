from datetime import datetime
import os
import re
from enum import IntEnum


class DocTypes(IntEnum):
    FLC_Vanilla = "FLC-Vanilla"
    FLC_DJ = "FLC-DJ"


def int2DocType(i: int) -> DocTypes:
    # temp solution for DocPrep enum
    if i == 1:
        return DocTypes.FLC_Vanilla
    elif i == 2:
        return DocTypes.FLC_DJ
    else:
        raise Exception("Invalid DocType")


def DocPrep(
    type: DocTypes = ...,
    hostname: str = "VMDly",
    username: str = "Administrator",
    password: str = "Password1",
    disk_path: str = "",
    iso_path: str = "",
    iso_sum: str = "",
    src: str = "templates/autounattend.xml",
) -> str:
    """
    Prepares a string for documentation

    Parameters
    ----------
    type : DocTypes
        The type of document to be prepared
    hostname : str
        The Hostname of the VM
    username : str
        The Username of the VM
    password : str
        The Password of the VM
    disk_path : str
        The path to the ISO
    iso_path : str
        The path to the ISO
    iso_sum : str
        The checksum of the ISO
    src : str
        The path to the source file

    Returns
    -------
    str
    """
    doc = (open(src, "r")).read()

    if isinstance(type, DocTypes):
        FLC = open(f"templates/{type.value}.xml", "r").read()
    else:
        FLC = ""

    if doc.find("$FLC$") != -1:
        doc.replace("$FLC$", FLC)

    return (
        doc.replace("$HOST$", hostname)
        .replace("$UserName$", username)
        .replace("$Password$", password)
        .replace("$DiskPath$", disk_path)
        .replace("$osPath$", iso_path)
        .replace("$osSum$", iso_sum)
    )


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
