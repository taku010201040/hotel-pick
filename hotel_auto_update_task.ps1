# ホテル情報の自動調査を毎朝 08:00 に実行するタスクを登録する
# 実行: PowerShell で 「.\hotel_auto_update_task.ps1」
# 解除: Unregister-ScheduledTask -TaskName 'HotelAutoUpdate' -Confirm:$false
$bat = Join-Path $PSScriptRoot 'hotel_auto_update.bat'
if (-not (Test-Path $bat)) { throw "hotel_auto_update.bat が見つかりません: $bat" }

$action  = New-ScheduledTaskAction -Execute $bat
$trigger = New-ScheduledTaskTrigger -Daily -At '08:00'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName 'HotelAutoUpdate' -Action $action -Trigger $trigger -Settings $settings -Force -Description '主要まとめサイト20サイトと各ホテルの公式HP/クーポンページを巡回して hotel-pick.html を更新'
Write-Host 'タスク HotelAutoUpdate を登録しました(毎日 08:00)。'
