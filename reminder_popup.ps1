while ($true) {
    Start-Sleep -Seconds 1200
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show('วินัย Ai', 'AI Discipline Reminder', 'OK', 'Warning')
}
