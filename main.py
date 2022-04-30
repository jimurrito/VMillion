#
#  <>-<[VMillion KVM VM Deployer]>-<>
#
# VM builder and Orchestrator, using Packer and KVM/QEMU64
# 4 python, dont push
#
# [Modules]
import os
import json
from time import sleep
import re
import libvirt
import labheim


# [Parameters]
#
Verbose = True
MountOnly = False
GenLog = "logs/VMD.log"


def main():
    # Startup Icon
    print((open("templates/logo", "r")).read())
    (open(f"./{GenLog}", "w")).write((open("templates/logo", "r")).read())

    Header = "PREP"
    labheim.VLog(Header="Start-Up", MSG="Start-Up", DIR=GenLog)
    # Main Loop
    while True:

        # Loop Waiting for WorkOrders
        Header = "IDLE"
        labheim.VLog(Header=Header, MSG=("Waiting for New WorkOrders"), DIR=GenLog)
        n = 0
        while True:
            WorkOrders = os.listdir("WorkOrders/")
            if WorkOrders:
                for Order in WorkOrders:
                    try:
                        re.search(".json", Order).group(0)
                    except:
                        WorkOrders.remove(Order)
                if WorkOrders:
                    break
            else:
                sleep(30)
                n += 1
                
                if n == 900:
                    # 30m heart-beat
                    labheim.VLog(
                        Header=Header, MSG=(f"Waiting loop Heart-beat"), DIR=GenLog
                    )
                    n = 0
        # Count
        Cb = 0
        Ca = sum(1 for c in WorkOrders if c.endswith(".json"))
        # Foreach Job
        for JobPath in WorkOrders:
            Header = "CONFIG"
            Cb += 1
            labheim.VLog(Header=Header, MSG=(f"Working on Job ({Cb}/{Ca})"), DIR=GenLog)

            # [Injest WorkOrder]
            # Grabs job from folder, loads it into json format
            Job = json.loads(open(f"WorkOrders/{JobPath}", "r").read())
            labheim.VLog(
                Header=Header, MSG="Injesting and Parsing WorkOrders", DIR=GenLog
            )
            Host = Job["VMName"]
            Name = Job["Credentials"]["Username"]
            Pwd = Job["Credentials"]["Password"]
            Path = f"/kvm/{Host}"

            # [Pre-Validation]
            # QEMU State
            Qemu = libvirt.open("qemu:///system")
            try:
                if (Qemu.lookupByName(Host)).isActive():
                    labheim.VLog(
                        Header="FAILURE",
                        MSG=f"Domain '{Host}' already Exists. Ending Job [X0F010]",
                        DIR=GenLog,
                    )
                    PreVal = True
                    ErNum = ".X0F010"
            except:
                labheim.VLog(
                    Header=Header,
                    MSG=(f"Domain '{Host}' not currently defined."),
                    DIR=GenLog,
                )
                try:
                    os.listdir(f"/kvm/{Host}")
                    labheim.VLog(
                        Header="FAILURE",
                        MSG=f"Files for Domain '{Host}' already Exist. Ending Job [X0F020]",
                        DIR=GenLog,
                    )
                    PreVal = True
                    ErNum = ".X0F020"
                except:
                    labheim.VLog(
                        Header=Header,
                        MSG=f"Files for Domain '{Host}' not Found. Building Domain.",
                        DIR=GenLog,
                    )
            # PreValidation Filter
            try:
                if PreVal:
                    NewPath = JobPath.replace(".json", ErNum)
                    if JobPath.endswith(".json"):
                        os.rename(
                            f"WorkOrders/{JobPath}", f"WorkOrders/finished/{NewPath}"
                        )
                    break
            except:
                labheim.VLog(
                    Header=Header,
                    MSG=f"PreValidation Successful, Starting Build for '{Host}'",
                    DIR=GenLog,
                )

            # [OS-Selection]
            # WS19      == 0
            # WS21      == 1
            # W10       == 2
            # Ubntu-Svr == 3
            # Ubntu-Dsk == 4
            Os, OSPath, OSSum = labheim.SelectMatrix(Type=0, IN=int(Job["OS"]))
            labheim.VLog(
                Header=Header, MSG=f"Domain '{Host}' OS will be '{Os}'", DIR=GenLog
            )

            # [Role-Selection]
            # Vanilla   == 0
            # DJ        == 1
            # DC        == 2
            Role = labheim.SelectMatrix(Type=1, IN=int(Job["Role"]))
            labheim.VLog(
                Header=Header, MSG=f"Domain '{Host}' Role will be '{Role}'", DIR=GenLog
            )

            # [DOCMOD]
            # Inject Workorder Params into autounattend.xml
            (open("./answer_files/autounattend.xml", "w")).write(
                labheim.DocPrep(Type=int(Job["Role"]), Host=Host, Name=Name, Pwd=Pwd)
            )
            labheim.VLog(
                Header=Header, MSG="New AutoUnattend.xml Generated", DIR=GenLog
            )
            # Inject WorkOrder Params into vars.auto.pkrvars.hcl
            (open("./vars.auto.pkrvars.hcl", "w")).write(
                labheim.DocPrep(
                    Host=Host,
                    Name=Name,
                    Pwd=Pwd,
                    DiskPath=Path,
                    ISOPATH=OSPath,
                    ISOSUM=OSSum,
                    Src=("templates/vars.pkrvars.hcl"),
                )
            )
            labheim.VLog(
                Header=Header, MSG="New Packer Variable File Generated", DIR=GenLog
            )
            # Inject WorkOrder Params into WinRM Config Script
            (open("Post-build/scripts/winRM_config_enable.ps1", "w")).write(
                labheim.DocPrep(Name=Name, Pwd=Pwd, Src=("templates/winRM.temp.ps1"))
            )
            labheim.VLog(
                Header=Header, MSG="New WinRM Configuration File Generated", DIR=GenLog
            )

            # [PACKER]
            if MountOnly == False:
                Header = "PACKER"
                PakLog = f"logs/{Host}_Packer.log"
                # Init.
                if labheim.Packer(cmd="init", Plog=PakLog) == 0:
                    labheim.VLog(Header=Header, MSG="Packer Initilized", DIR=GenLog)
                else:
                    labheim.VLog(
                        Header=Header, MSG="Packer Initilization Failed", DIR=GenLog
                    )
                    PFail = True
                # Fmt.
                if labheim.Packer(cmd="fmt", Plog=PakLog) == 0:
                    labheim.VLog(Header=Header, MSG="Packer Files Formated", DIR=GenLog)
                else:
                    labheim.VLog(
                        Header=Header, MSG="Packer Files Failed to Format", DIR=GenLog
                    )
                    PFail = True
                # Validate
                if labheim.Packer(cmd="validate", Plog=PakLog) == 0:
                    labheim.VLog(
                        Header=Header, MSG="Packer Files Validated", DIR=GenLog
                    )
                else:
                    labheim.VLog(
                        Header=Header,
                        MSG="Packer Files Failed to Validated",
                        DIR=GenLog,
                    )
                    PFail = True
                # Build
                p = labheim.Packer(cmd="build", Plog=PakLog)
                if p == 0:
                    labheim.VLog(
                        Header=Header, MSG="Packer Build Completed", DIR=GenLog
                    )
                elif p == 2:
                    labheim.VLog(
                        Header=Header,
                        MSG="Packer Build Lacks Required Premissions",
                        DIR=GenLog,
                    )
                    PFail = True
                else:
                    labheim.VLog(Header=Header, MSG="Packer Build Failed", DIR=GenLog)
                    PFail = True
            # Packer Fail Catch
            if PFail:
                exit(
                    "Critical Error. Packer Failed to Build. Check Packer Logs for More Information. VMD Exiting"
                )

            # [KVM]
            # Installs New Image as a KVM Domain
            Header = "KVM"
            KVMLog = f"logs/{Host}_KVM.log"
            labheim.VLog(Header=Header, MSG="Generating KVM|QEMU Domain", DIR=GenLog)
            labheim.VMBuilder(
                AStrt=bool(Job["AutoStart"]),
                Host=Host,
                vCPU=(Job["vCPU"]),
                RAM=(Job["RAM"]),
                Net=(Job["Network"]),
                DiskPath=(f"{Path}/vdisk0"),
                Log=KVMLog,
            )
            # Validating Domain was Set
            try:
                if (Qemu.lookupByName(Host)).isActive():
                    labheim.VLog(
                        Header=Header, MSG="Domain Successfully Deployed", DIR=GenLog
                    )

                    NewPath = JobPath.replace(".json", ".X0")
                    if JobPath.endswith(".json"):
                        os.rename(
                            f"WorkOrders/{JobPath}", f"WorkOrders/finished/{NewPath}"
                        )
            except:
                labheim.VLog(
                    Header=Header,
                    MSG="Domain Failed to be Deployed [X0F001] ",
                    DIR=GenLog,
                )
                Path = Job.replace(".json", ".X0F001")
                os.rename(f"WorkOrders/{Job}", f"WorkOrders/finished/{Path}")
                break
        else:
            continue


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":
    main()
