# Domain Join + Restart
$DJSP_Pwdfile = 'A:\djsp.pwd'

# Generates Domain Join Credential
$DJSP_Username = 'domainjoin@jimurrito.com'
$DJSP_Password = Get-Content $DJSP_Pwdfile | ConvertTo-SecureString -AsPlainText -Force
$DJSP_Cred = New-Object System.Management.Automation.PSCredential -ArgumentList $DJSP_Username, $DJSP_Password

# Joins machine to domain
Add-Computer -DomainName jimurrito.com -Credential $DJSP_Cred