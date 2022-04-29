HostName = "test"

UserName = "Administrator"
PassWord = "YourMom!!1"

OutputPath = "/kvm/test"

isoPath = "/cd_disk/KVM/iso/winserver_2019.iso"
isoSum  = "md5:70fec2cb1d6759108820130c2b5496da"

FloppyFiles = [
  "./answer_files/autounattend.xml",
  "./answer_files/djsp.pwd"
]
CDFiles = [
  "./drivers/",
  "./Post-build/"
]

