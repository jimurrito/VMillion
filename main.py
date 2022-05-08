#
#  <>-<[VMillion KVM VM Deployer]>-<>
#
# VM builder and Orchestrator, using Packer and KVM/QEMU64
# 4 python, dont push
#
# [Modules]
import os
import json
from labheim import Job, JobWait, VLog, DocMod, JobFail
from packer import Packer


# [Parameters]
#
GenLog = "logs/VMD.log"
RootPath = os.getcwd()
Path_to_ISO = "/cd_disk/KVM/iso/"
MountOnly = False


def main():
    # Startup Icon
    print((open("templates/logo", "r")).read())
    (open(f"./{GenLog}", "w")).write((open("templates/logo", "r")).read())

    Header = "PREP"
    VLog("Start-Up", "Start-Up", GenLog)
    # Main Loop
    while True:

        # Loop Waiting for WorkOrders
        WorkOrders = JobWait(Log=GenLog)

        # Count
        Cb = 0
        Ca = sum(1 for c in WorkOrders if c.endswith(".json"))
        # Foreach Order
        for JobPath in WorkOrders:
            Header = "CONFIG"
            Cb += 1
            VLog(Header, (f"Working on WorkOrder ({Cb}/{Ca})"), GenLog)

            # [Injest WorkOrder]
            # Grabs Order from folder, loads it into json format
            VLog(Header, "Injesting and Parsing WorkOrders", GenLog)
            Order = Job(json.loads(open(f"WorkOrders/{JobPath}", "r").read()))

            if MountOnly != True:

                # Domain Validation
                Error = Order.ValJob(0, Log=GenLog)
                if Error:
                    JobFail(Error, JobPath)
                    break
                else:
                    VLog(
                        Header,
                        f"PreValidation Successful, Starting Build for '{Order.Host}'",
                        GenLog,
                    )
                Error = 0

                # [OS-Selection]
                VLog(
                    Header,
                    f"Domain '{Order.Host}' OS will be '{Order.getOSName()}'",
                    GenLog,
                )
                # [Role-Selection]
                VLog(
                    Header,
                    f"Domain '{Order.Host}' Role will be '{Order.getRoleName()}'",
                    GenLog,
                )

                # Gets ISOPath and MD5-Hash
                ISOPath, Hash = Order.getISO(Path_to_ISO)

                # [DOCMOD]
                # Autounattend.xml
                (open("./answer_files/autounattend.xml", "w")).write(
                    DocMod(Order, (open("templates/autounattend.xml", "r").read()))
                )
                VLog(Header, "New AutoUnattend File Generated", GenLog)
                # vars.auto.pkrvars.hcl
                (open("./vars.auto.pkrvars.hcl", "w")).write(
                    DocMod(
                        Order,
                        (open("templates/vars.pkrvars.hcl", "r").read()),
                        ISOPath=ISOPath,
                        ISOHash=Hash,
                    )
                )
                VLog(Header, "New Packer Variable File Generated", GenLog)
                # winRM_config_enable.ps1
                (open("Post-build/scripts/winRM_config_enable.ps1", "w")).write(
                    DocMod(Order, (open("templates/winRM.temp.ps1", "r").read()))
                )
                VLog(Header, "New WinRM Configuration File Generated", GenLog)

                # [PACKER]
                Header = "PACKER"
                Build = Packer(Order, GenLog=GenLog)
                try:
                    Build.Init()
                except:
                    Error = ".X0F010"
                try:
                    Build.Format()
                except:
                    Error = ".X0F020"
                try:
                    Build.Validate()
                except:
                    Error = ".X0F030"
                try:
                    Build.Build()
                except:
                    Error = ".X0F040"

                # Packer Fail Catch
                if not isinstance(Error, int):
                    VLog(
                        "FAILURE",
                        f"Packer Execution Failure [{Error}] for Domain '{Order.Host}'. Ending Job... ",
                        GenLog,
                    )
                    JobFail(Error, JobPath)
                    break

            # [KVM]
            # Installs New Image as a KVM Domain
            Order.DefineBuild()

            # Validating Domain was Set
            Error = Order.ValJob(1, Log=GenLog)
            if Error:
                JobFail(Error, JobPath)
                break
            else:
                VLog(
                    Header,
                    f"Domain '{Order.Host}' Successfully Deployed.",
                    GenLog,
                )
                os.rename(
                    f"WorkOrders/{JobPath}",
                    f"WorkOrders/finished/" + JobPath.replace(".json", ".X0"),
                )
                break


if __name__ == "__main__":
    main()
