variable "HostName" {
  type    = string
  default = "VMD-Default"
}
variable "FloppyFiles" {
  type = list(string)
  default = [
    "./answer_files/autounattend.xml",
    "./answer_files/djsp.pwd"
  ]
}
variable "CDFiles" {
  type = list(string)
  default = [
    "./drivers/",
    "./Post-build/"
  ]
}
variable "UserName" {
  type    = string
  default = "Administrator"
}
variable "PassWord" {
  type      = string
  sensitive = true
}
variable "OutputPath" {
  type = string
}
variable "isoPath" {
  type = string
}
variable "isoSum" {
  type = string
}



source "qemu" "VMillion" {
  # ISO Image
  # Use ISO on fastest storage to increase speed of install
  iso_url      = var.isoPath
  iso_checksum = var.isoSum

  # H-Visor Settings
  accelerator = "kvm"
  # Equinox required the absolute path to "OVMF.fd"
  firmware         = "/usr/share/ovmf/OVMF.fd"
  output_directory = var.OutputPath
  # If no Gui on host, set to True
  headless = true

  # Import Files
  floppy_files = var.FloppyFiles
  cd_files     = var.CDFiles

  # VM-Infra. settings
  vm_name        = "vdisk0"
  cpus           = 2
  memory         = "2048"
  disk_size      = "40G"
  format         = "raw"
  disk_interface = "virtio"
  # CANT USE BRIDGES WITHOUT NetworkManager. if using systemd-networkd, use virtio-net
  net_device       = "virtio-net"
  display          = "vnc=0.0.0.0"
  vnc_bind_address = "0.0.0.0"

  # Packer-Remote-Access Settings
  communicator   = "winrm"
  winrm_username = var.UserName
  winrm_password = var.PassWord
  winrm_timeout  = "20m"

  # Custom KVM Arguments (Fixes "CPU Feature not supported Error")
  qemuargs = [["-cpu", "host"]]

  # Build Config
  boot_wait = "5s"
  boot_command = [
    #Waiting for "Press Any Key" prompt, then enter for 2nd prompt. extra inputs to ensure boot to CD.
    "<enter><enter><enter><enter><enter><enter><enter><enter><wait2s><enter><enter><enter><enter>",
    #Wait for Prompt to install Windows + Wait for Post install scripts and installs
    "<wait5m><enter><enter><wait15m>",
  ]
  # Gracefull shutdown command, when packer is done.
  shutdown_command = "shutdown /s /t 10 /f /d p:4:1 /c \"Packer Initiated Shutdown\""
}

build {
  sources = ["source.qemu.VMillion"]
}