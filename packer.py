import os
import re
from enum import Enum
import subprocess
from labheim import VLog, Job
import tempfile


class Packer:
    class CMD(Enum):
        i = "init"
        f = "fmt"
        v = "validate"
        b = "build"

    # Creates packer Obj
    def __init__(self, job: Job, Path: str = "./", GenLog: str = ...):
        if not isinstance(job, Job):
            raise Exception("Object is not Class 'Job'")
        self.Path = str(Path)
        self.PLog = f"logs/{job.Host}_Pkr.log"
        open(self.PLog, "w")
        self.GLog = GenLog

    # Packer Init
    def Init(self):
        """Initilizes Packer"""
        if not isinstance(self, Packer):
            raise Exception("Object is not Class 'Packer'")
        cmd = ["PACKER_LOG=1", "packer", self.CMD.i.value, self.Path, ">>", self.PLog]
        try:
            re.search("Error", subprocess.run(cmd, capture_output=True).stdout)
            raise Exception("Packer Initilization Failed")
        except:
            VLog("PACKER", "Packer Inititization was Successful", self.GLog)
            return

    # Packer Format
    def Format(self):
        if not isinstance(self, Packer):
            raise Exception("Object is not Class 'Packer'")
        cmd = ["PACKER_LOG=1", "packer", self.CMD.f.value, self.Path, ">>", self.PLog]
        try:
            re.search("Error", subprocess.run(cmd, capture_output=True).stdout)
            raise Exception("Packer Formating Failed")
        except:
            VLog("PACKER", "Packer Formating was Successful", self.GLog)
            return

    # Packer Validate
    def Validate(self):
        if not isinstance(self, Packer):
            raise Exception("Object is not Class 'Packer'")
        cmd = ["PACKER_LOG=1", "packer", self.CMD.v.value, self.Path, ">>", self.PLog]
        try:
            re.search("Error", subprocess.run(cmd, capture_output=True).stdout)
            raise Exception("Packer Validation Failed")
        except:
            VLog("PACKER", "Packer Validation was Successful", self.GLog)
            return

    # Packer Build
    def Build(self):
        if not isinstance(self, Packer):
            raise Exception("Object is not Class 'Packer'")
        VLog("PACKER", "Packer Build Starting...", self.GLog)
        cmd = ["packer", self.CMD.b.value, "-machine-readable", self.Path]
        with tempfile.TemporaryFile() as temp:
            subprocess.Popen(cmd, stdout=temp).wait()
            temp.seek(0)
            a = str(temp.read())
            for i in a.split("\\n"):
                ir = PrsOut(i)
                if ir:
                    open(self.PLog, "a").write(str(ir))
                    open(self.PLog, "a").write("\n")
                try:
                    re.search(
                        "==> Builds finished\. The artifacts of successful builds are:",
                        ir,
                    ).group(0)
                    VLog("PACKER", "Packer Build was Successful", self.GLog)
                    return
                except:
                    pass
            raise Exception("Packer Build Failure, Check Logs")


# Packer Output Normalization
def PrsOut(In: str):
    """Parse-Out, Normalizes Packer Output
    \n Cuts out the special Characters from the Raw Output. Provides only Event data.
    """

    class Reg(Enum):
        r = "[0-9]+,,ui,say,==> qemu\.VMillion: *"
        r2 = "[0-9]+,,ui,message    qemu.VMillion: *"
        r3 = "    qemu.VMillion: *"
        r4 = "[0-9]+,,ui,say,"
        e = "[0-9]+,,ui,error,Build 'qemu\.VMillion' *"
        e2 = "[0-9]+,,ui,error,Error: *"

    # First item ' b" ' catch
    try:
        In = In.replace('b"', "")
    except:
        pass

    if In == "\\" or In == '"':
        return
    while True:
        # Normal Filtering
        try:
            Out = In.replace((re.search(Reg.r.value, In).group(0)), "")
            break
        except:
            pass
        try:
            Out = In.replace((re.search(Reg.r2.value, In).group(0)), "")
            break
        except:
            pass
        try:
            Out = In.replace((re.search(Reg.r3.value, In).group(0)), "")
            break
        except:
            pass
        try:
            Out = In.replace((re.search(Reg.r4.value, In).group(0)), "")
            break
        except:
            pass
        # Error Filtering
        try:
            Out = In.replace((re.search(Reg.e.value, In).group(0)), "")
            break
        except:
            try:
                Out = In.replace((re.search(Reg.e2.value, In).group(0)), "")
                break
                # Output is unmapped
            except:
                In = In.replace("* ", "")
                Out = In
                break
    return Out
