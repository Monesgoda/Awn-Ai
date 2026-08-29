Option Explicit
Dim shell, script, fso
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

script = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "src\main.py")

If findExe("pyw.exe") Then
    shell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
    shell.Run "pyw.exe """ & script & """", 0, False
ElseIf findExe("pythonw.exe") Then
    shell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
    shell.Run "pythonw.exe """ & script & """", 0, False
Else
    MsgBox "Python not found (need pyw.exe or pythonw.exe in PATH).", 48, "StealthClip"
End If

Function findExe(exe)
    Dim cmd, line
    On Error Resume Next
    Set cmd = shell.Exec("where.exe " & exe)
    line = cmd.StdOut.ReadLine()
    findExe = (Err.Number = 0)
End Function