import os

name = 'VMillion'
root = os.getcwd()

s = f"""[Unit]
Description=Labheim-VMillion-Deploy

[Service]
Type=simple
ExecStart=/usr/bin/python3 {root}/main.py
WorkingDirectory={root}
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""

open(f"/etc/systemd/system/{name}.service","w").write(s)
os.system(f"systemctl daemon-reload && systemctl enable {name} && systemctl start {name} --no-block")