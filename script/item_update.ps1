# This script updates the item data for the Missile Wars.

$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $script_dir/���ҵ���ս�����ݰ�����

#py.exe .\description_updator.py
#py.exe .\cost_updator.py
#py.exe .\book_updator.py

py.exe .\compare_packs.py .\data "D:\czm�ҵ�����\.minecraft\versions\1.21-Fabric 0.15.11\saves\Missile Wars\datapacks\Missile Wars Fusion for 1.21\data" --output .\diff.txt

$choice = Read-Host "Do you want to apply the changes? (y/n)"

$choice = $choice.ToLower()

if ($choice -eq 'y') {
    py.exe .\sync_packs.py .\data "D:\czm�ҵ�����\.minecraft\versions\1.21-Fabric 0.15.11\saves\Missile Wars\datapacks\Missile Wars Fusion for 1.21\data"
    Write-Host "Changes applied successfully."
} else {
    Write-Host "No changes were applied."
}
