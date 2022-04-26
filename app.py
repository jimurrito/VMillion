#
#  <>-<[VMillion KVM VM Deployer]>-<>
#
# VM builder and Orchestrator, using Packer and KVM/QEMU64

# [Modules]
from datetime import datetime, date
import hashlib
import os
import json
from time import sleep
import libvirt
import hashlib


# [Parameters]
#
Verbose = True
MountOnly = False
GenLog = "logs/VMD.log"

# [Functions]
# Intake .Json from '.\WorkOrders' & Parse for variables
# Parse and modify dependant files for build paramters
# Packer Orchestration
# KVM Orchestration


def DocPrep(
    TYPE: int = 99,
    HOST: str = "VMDly",
    NAME: str = "Administrator",
    PWD: str = "Password1",
    DiskPath: str = "",
    ISOPATH: str = "",
    ISOSUM: str = "",
    Src: str = "templates/autounattend.xml",
):
    doc = (open(Src, "r")).read()
    if TYPE != 99:
        if TYPE == 0:
            FLC = open("templates/FLC-Vanilla.xml", "r").read()
        if TYPE == 1:
            FLC = open("templates/FLC-DJ.xml", "r").read()
        doc = doc.replace("$FLC$", FLC)
    doc = doc.replace("$HOST$", HOST)
    doc = doc.replace("$UserName$", NAME)
    doc = doc.replace("$Password$", PWD)
    doc = doc.replace("$DiskPath$", DiskPath)
    doc = doc.replace("$osPath$", ISOPATH)
    doc = doc.replace("$osSum$", ISOSUM)
    return doc


def VLog(
    PHASE: str = "PHASE",
    HEADER: str = "HEADER",
    MSG: str = "Message",
    DIR: str = GenLog,
    CLEAR: bool = False,
):
    """Verbose Log Function will default to Appending, unless CLEAR == True"""
    Time = (datetime.now()).isoformat(timespec="seconds")
    Output = f"[{Time}]-[{PHASE}]-[{HEADER}]-[{MSG}]"
    if CLEAR == True:
        (open(f"./{DIR}", "w")).write(Output)
    else:
        (open(f"./{DIR}", "a")).write("\n")
        (open(f"./{DIR}", "a")).write(Output)
    print(Output)



def SelectMatrix(
    TYPE: int = 0,
    IN: int = 0,
    ROOT: str = "/cd_disk/KVM/iso/"
):
    if TYPE == 0:
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
        c = open(f"{b.replace('.iso','.hash')}","r").read()
        return a, b, c

    if TYPE == 1:
        if IN == 0:
            a = "Vanilla"
        if IN == 1:
            a = "Domain Joined"
        if IN == 2:
            a = "Domain Controller"
        return a


def VMBuilder(
    AStrt: bool, HOST: str, vCPU: str, RAM: str, Net: str, DiskPath: str, Log: str
):
    build = open("templates/virt-install-win.temp", "r").read()
    vCPU = str(vCPU)
    RAM = str(RAM)
    if AStrt == True:
        AStrt = "--autostart"
    else:
        AStrt = ""
    build = build.replace("$HOST$", HOST)
    build = build.replace("$vCPU$", vCPU)
    build = build.replace("$RAM$", RAM)
    build = build.replace("$Net$", Net)
    build = build.replace("$DiskPath$", DiskPath)
    build = build.replace("$AStrt$", AStrt)
    os.system(f"{build} > {Log}")


# [Main()]
#


def main():
    # Startup Icon
    print((open("templates/logo", "r")).read())
    (open(f"./{GenLog}", "w")).write((open("templates/logo", "r")).read())

    PHASE = "PREP"
    VLog(PHASE=PHASE, HEADER="Start-Up", MSG="Start-Up")
    # Main Loop
    while True:

        # Loop Waiting for WorkOrders
        PHASE = "PREP"
        HEADER = "Waiting"
        Ca = 0
        while True:
            Ca += 1
            VLog(
                PHASE=PHASE,
                HEADER=HEADER,
                MSG=(f"Looking for New WorkOrders... ({Ca}/5)"),
            )
            WorkOrders = os.listdir("WorkOrders/")
            Cb = str(WorkOrders).count(".json")
            if Cb:
                VLog(PHASE=PHASE, HEADER=HEADER, MSG=(f"({Cb}) WorkOrder(s) Found"))
                break
            if Ca >= 5:
                VLog(PHASE=PHASE, HEADER=HEADER, MSG="Going into Long Rest (5 Min)")
                sleep(300)
                Ca = 0
            else:
                VLog(
                    PHASE=PHASE,
                    HEADER=HEADER,
                    MSG="No WorkOrders Found, Going into Short Rest (30 Sec)",
                )
                sleep(30)
        # Foreach Job
        Cc = 0
        for JobPath in WorkOrders:
            PHASE = "BUILD"
            HEADER = "Configuration"
            Cc += 1
            VLog(PHASE=PHASE, HEADER=HEADER, MSG=(f"Working on Job ({Cc}/{Cb})"))

            # [Injest WorkOrder]
            # Grabs job from folder, loads it into json format
            Job = json.loads(open(f"WorkOrders/{JobPath}", "r").read())
            VLog(PHASE=PHASE, HEADER=HEADER, MSG="Injesting and Parsing WorkOrders")
            HOST = Job["VMName"]
            NAME = Job["Credentials"]["Username"]
            PWD = Job["Credentials"]["Password"]
            PATH = f"/kvm/{HOST}"

            # [Pre-Validation]
            # Ensures VM doesn't Already Exist
            Qemu = libvirt.open("qemu:///system")
            try:
                if (Qemu.lookupByName(HOST)).isActive():
                    VLog(
                        PHASE=PHASE,
                        HEADER=HEADER,
                        MSG=f"Domain '{HOST}' already Exists. Ending Job [X0F010]",
                    )
                    NewPath = JobPath.replace(".json", ".X0F010")
                    os.rename(f"WorkOrders/{JobPath}", f"WorkOrders/{NewPath}")
                    break
            except:
                VLog(
                    PHASE=PHASE,
                    HEADER=HEADER,
                    MSG=(f"Domain '{HOST}' not currently defined."),
                )
                try:
                    open(f"/kvm/{HOST}")
                    VLog(
                        PHASE=PHASE,
                        HEADER=HEADER,
                        MSG=f"Files for Domain '{HOST}' already Exist. Ending Job [X0F020]",
                    )
                    NewPath = JobPath.replace(".json", ".X0F020")
                    os.rename(f"WorkOrders/{JobPath}", f"WorkOrders/{NewPath}")
                    break
                except:
                    VLog(
                        PHASE=PHASE,
                        HEADER=HEADER,
                        MSG=f"Files for Domain '{HOST}' not Found. Building Domain.",
                    )
            # [OS-Selection]
            # WS19      == 0
            # WS21      == 1
            # W10       == 2
            # Ubntu-Svr == 3
            # Ubntu-Dsk == 4
            OS, OSPath, OSSum = SelectMatrix(TYPE=0,IN=int(Job["OS"]))
            VLog(
                PHASE=PHASE,
                HEADER=HEADER,
                MSG=f"Domain '{HOST}' OS will be '{OS}'",
            )

            # [Role-Selection]
            # Vanilla   == 0
            # DJ        == 1
            # DC        == 2
            Role = SelectMatrix(TYPE=1,IN=int(Job["Role"]))
            VLog(
                PHASE=PHASE,
                HEADER=HEADER,
                MSG=f"Domain '{HOST}' Role will be '{Role}'",
            )

            # [DOCMOD]
            # Inject Workorder Params into autounattend.xml
            (open("./answer_files/autounattend.xml", "w")).write(
                DocPrep(TYPE=int(Job["Role"]), HOST=HOST, NAME=NAME, PWD=PWD)
            )
            VLog(PHASE=PHASE, HEADER=HEADER, MSG="New AutoUnattend.xml Generated")
            # Inject WorkOrder Params into vars.auto.pkrvars.hcl
            (open("./vars.auto.pkrvars.hcl", "w")).write(
                DocPrep(
                    HOST=HOST,
                    NAME=NAME,
                    PWD=PWD,
                    DiskPath=PATH,
                    ISOPATH=OSPath,
                    ISOSUM=OSSum,
                    Src=("templates/vars.pkrvars.hcl"),
                )
            )
            VLog(PHASE=PHASE, HEADER=HEADER, MSG="New Packer Variable File Generated")
            # Inject WorkOrder Params into WinRM Config Script
            (open("Post-build/scripts/winRM_config_enable.ps1", "w")).write(
                DocPrep(NAME=NAME, PWD=PWD, Src=("templates/winRM.temp.ps1"))
            )
            VLog(
                PHASE=PHASE, HEADER=HEADER, MSG="New WinRM Configuration File Generated"
            )

            # [PACKER]
            if MountOnly == False:
                PHASE = "PACKER"
                PakLog = f"logs/{HOST}_Packer.log"
                # Init.
                VLog(PHASE=PHASE, HEADER=HEADER, MSG="Packer Initilizing")
                os.system(f"packer init ./ > {PakLog}")
                # Fmt.
                VLog(PHASE=PHASE, HEADER=HEADER, MSG="Packer Formating Template")
                os.system(f"packer fmt ./ >> {PakLog}")
                # Validate
                VLog(PHASE=PHASE, HEADER=HEADER, MSG="Packer Validation of Template")
                os.system(f"packer validate ./ >> {PakLog}")
                # Build.
                VLog(PHASE=PHASE, HEADER=HEADER, MSG="Packer Build Starting")
                os.system(f"PACKER_LOG=1 packer build ./ >> {PakLog}")
                VLog(PHASE=PHASE, HEADER=HEADER, MSG="Packer Build Build Complete")

            # [KVM]
            # Installs New Image as a KVM Domain
            PHASE = "KVM"
            KVMLog = f"logs/{HOST}_KVM.log"
            VLog(PHASE=PHASE, HEADER=HEADER, MSG="Generating KVM|QEMU Domain")
            VMBuilder(
                AStrt=bool(Job["AutoStart"]),
                HOST=HOST,
                vCPU=(Job["vCPU"]),
                RAM=(Job["RAM"]),
                Net=(Job["Network"]),
                DiskPath=(f"{PATH}/vdisk0"),
                Log=KVMLog,
            )
            # Validating Domain was Set
            try:
                if (Qemu.lookupByName(HOST)).isActive():
                    VLog(PHASE=PHASE, HEADER=HEADER, MSG="Domain Successfully Deployed")
                    # Remove Workorder
                    os.remove(f"WorkOrders/{JobPath}")
            except:
                VLog(
                    PHASE=PHASE,
                    HEADER=HEADER,
                    MSG="Domain Failed to be Deployed [X0F001] ",
                )
                NewPath = JobPath.replace(".json", ".X0F001")
                os.rename(f"WorkOrders/{JobPath}", f"WorkOrders/{NewPath}")
                break


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
main()
