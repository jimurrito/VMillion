HostName = "test"

UserName = "Administrator"
PassWord = "YourMom!!1"

OutputPath = "/kvm/test"

isoPath = "/cd_disk/KVM/iso/winserver_2022.iso"
isoSum  = "md5:e7908933449613edc97e1b11180429d1"

FloppyFiles = [
  "./answer_files/autounattend.xml",
  "./answer_files/djsp.pwd"
]
CDFiles = [
  "./drivers/",
  "./Post-build/"
]

