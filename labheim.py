from datetime import datetime
import os
import re
from enum import Enum
from time import sleep
import libvirt


class Job:
    # OS Options
    class OSName(Enum):
        Ws19 = "Windows-Server 19"
        Ws22 = "Windows-Server 22"
        W10e = "Windows 10"
        UbuS = "Ubuntu-Server"
        UbuD = "Ubuntu-Desktop"

    # ISO RE Patterns
    class ISOName(Enum):
        Ws19 = "winserver_2019\.[a-zA-Z]+"
        Ws22 = "winserver_2022\.[a-zA-Z]+"
        W10e = "windows10_21h2_ENT\.[a-zA-Z]+"
        UbuS = "ubuntu_server_21\.10_amd64\.[a-zA-Z]+"
        UbuD = "ubuntu_desktop_21\.04_amd64\.[a-zA-Z]+"

    # Role Options
    class RoleName(Enum):
        VAN = "Vanilla"
        DJ = "Domain Joined"
        DC = "Domain Controller"

    # Creates Job Obj
    def __init__(self, Job):
        self.Host = Job["VMName"]
        self.Name = Job["Credentials"]["Username"]
        self.Pwd = Job["Credentials"]["Password"]
        self.Path = f"/kvm/{self.Host}"
        self.Os = int(Job["OS"])
        self.Role = int(Job["Role"])
        self.AS = bool(Job["AutoStart"])
        self.CPU = int(Job["vCPU"])
        self.RAM = int(Job["RAM"])
        self.Net = Job["Network"]

    # Gets OS Name from Int
    def getOSName(self):
        """Gets OS Name for Verbose Output
        \nOS Int --> OS Str
        """
        if self.Os == 0:
            return self.OSName.Ws19.value
        elif self.Os == 1:
            return self.OSName.Ws22.value
        elif self.Os == 2:
            return self.OSName.W10e.value
        elif self.Os == 3:
            return self.OSName.UbuS.value
        elif self.Os == 4:
            return self.OSName.UbuD.value
        else:
            raise Exception("Invalid OS Int Provided")

    # Gets Role Name from Int
    def getRoleName(self):
        """Gets Role Name for Verbose Output
        \nRole Int --> Role Str
        """
        if self.Role == 0:
            return self.RoleName.VAN.value
        elif self.Role == 1:
            return self.RoleName.DJ.value
        elif self.Role == 2:
            return self.RoleName.DC.value
        else:
            raise Exception("Invalid Role Int Provided")

    # Gets ISO Path
    def getISO(self, ISOPath: str):
        """Gets .ISO file Path, and Associated .Hash File
        \n >> ISO Path
        \n >> ISO MD5 Hash
        """
        if self.Os == 0:
            Name = self.ISOName.Ws19.value
        elif self.Os == 1:
            Name = self.ISOName.Ws22.value
        elif self.Os == 2:
            Name = self.ISOName.W10e.value
        elif self.Os == 3:
            Name = self.ISOName.UbuS.value
        elif self.Os == 4:
            Name = self.ISOName.UbuD.value
        else:
            raise Exception("Invalid OS Int Provided")
        Iso = list()
        for i in os.listdir(ISOPath):
            try:
                Iso.append(re.search(Name, i).group(0))
            except:
                pass
        if not Iso:
            raise Exception(f"No .ISOs or .HASH Found in '{ISOPath}'")
        ISOfile = f"{ISOPath}{Iso[0]}"
        Hash = open(f"{ISOPath}{Iso[1]}", "r").read()
        return ISOfile, Hash

    def ValJob(self, Type: int, VHead="CONFIG", Log=...):
        """Validates if Domain already exists.
        Checks if Domain is Defined in KVM, or files exist in the Target Path.
        """
        # QEMU State
        Qemu = libvirt.open("qemu:///system")
        # KVM Eval
        try:
            (Qemu.lookupByName(self.Host)).isActive()
            kvm = True
        except:
            kvm = False
        # File Eval
        try:
            os.listdir(self.Path)
            file = True
        except:
            file = False

        class Error(Enum):
            PreKVM = ".X0F100"
            PreFile = ".X0F100"
            PostKVM = ".X0F001"
            PostFile = ".X0F002"

        # ValMatrix 0 == Pre; 1 == Post
        # KVM Val
        if Type == 0 and kvm == True or Type == 1 and kvm == False:
            if Type == 0:
                e = Error.PreKVM.value
            elif Type == 1:
                e = Error.PostKVM.value
            VLog(
                Header="FAILURE",
                MSG=f"KVM Validation Failure [{e}] for Domain '{self.Host}'. Ending Job... ",
                DIR=Log,
            )
            return e
        else:
            VLog(
                Header=VHead,
                MSG=f"KVM Validation Successful for Domain '{self.Host}'.",
                DIR=Log,
            )
        # File Val
        if Type == 0 and file == True or Type == 1 and file == False:
            if Type == 0:
                e = Error.PreFile.value
            elif Type == 1:
                e = Error.PostFile.value
            VLog(
                Header="FAILURE",
                MSG=f"File Validation Failure [{e}] for Domain '{self.Host}'. Ending Job ",
                DIR=Log,
            )
            return e
        else:
            VLog(
                Header=VHead,
                MSG=f"File Validation Successful for Domain '{self.Host}'.",
                DIR=Log,
            )
            return

    def DefineBuild(self):
        """Defines Packer Built Domain, as a KVM Domain"""
        VHead = "KVM"
        Log = f"logs/{self.Host}_KVM.log"
        build = open("templates/virt-install-win.temp", "r").read()
        VLog(Header=VHead, MSG="Generating KVM|QEMU Domain", DIR=Log)
        if self.AS == True:
            As = "--autostart"
        else:
            As = ""
        build = (
            build.replace("$HOST$", self.Host)
            .replace("$vCPU$", str(self.CPU))
            .replace("$RAM$", str(self.RAM))
            .replace("$Net$", self.Net)
            .replace("$DiskPath$", self.Path)
            .replace("$AStrt$", As)
        )
        os.system(f"{build} > {Log}")


def DocMod(
    job: Job,
    File: str,
    RootPath: str = os.getcwd(),
    ISOPath: str = ...,
    ISOHash: str = ...,
):
    """Pipes Input into Template Files.
    \nCan Consume Class Job Objects
    """

    class FLC(Enum):
        Vanilla = "FLC-Vanilla"
        DJ = "FLC-DJ"

    if not isinstance(job, Job):
        raise Exception("Input Object is not Class Job")
    if File.find("$FLC$") != -1:
        if job.Role == 0:
            Cmd = open(f"{RootPath}/templates/{FLC.Vanilla.value}.xml", "r").read()
        elif job.Role == 1:
            Cmd = open(f"{RootPath}/templates/{FLC.DJ.value}.xml", "r").read()
        else:
            raise Exception("Input Role Not Defined")
        File = File.replace("$FLC$", Cmd)
    if ISOPath != Ellipsis:
        File = File.replace("$osPath$", ISOPath)
    if ISOHash != Ellipsis:
        File = File.replace("$osSum$", ISOHash)
    return (
        File.replace("$HOST$", job.Host)
        .replace("$UserName$", job.Name)
        .replace("$Password$", job.Pwd)
        .replace("$DiskPath$", job.Path)
    )


def JobWait(Dir: str = "WorkOrders/", VHead: str = "IDLE", Log: str = ...):
    if Log == Ellipsis:
        raise Exception("Log Directory Argument Required")
    VLog(Header=VHead, MSG=(f"Waiting for New WorkOrders"), DIR=Log)
    n = 0
    while True:
        WorkOrders = os.listdir(Dir)
        if WorkOrders:
            for Order in WorkOrders:
                try:
                    re.search(".json", Order).group(0)
                except:
                    WorkOrders.remove(Order)
            if WorkOrders:
                return WorkOrders
        sleep(30)
        n += 1
        # 30m heart-beat
        if n == 900:
            VLog(Header=VHead, MSG=(f"Waiting loop Heart-beat"), DIR=Log)
            n = 0


def JobFail(Error: str, Path: str, Root: str = "WorkOrders/"):
    os.rename(
        f"{Root}{Path}",
        f"{Root}finished/" + Path.replace(".json", Error),
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
