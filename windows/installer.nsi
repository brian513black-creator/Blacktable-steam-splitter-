Unicode true
ManifestDPIAware true
RequestExecutionLevel user
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!include "WinVer.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"

!define PRODUCT "Blacktable Studio by Brian"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlacktableStudio"

Name "${PRODUCT}"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\Blacktable Studio"
BrandingText "${PRODUCT}"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${PRODUCT}"
VIAddVersionKey "FileDescription" "Blacktable Studio Setup"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "CompanyName" "Brian"

!define MUI_ICON "blacktable.ico"
!define MUI_UNICON "blacktable.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\Blacktable Studio.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Open Blacktable Studio"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${IfNot} ${IsNativeAMD64}
  ${OrIfNot} ${AtLeastBuild} 22000
    MessageBox MB_ICONSTOP|MB_OK "Blacktable requires 64-bit Windows 11." /SD IDOK
    SetErrorLevel 1
    Quit
  ${EndIf}
FunctionEnd

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*"
  CreateShortcut "$SMPROGRAMS\Blacktable Studio.lnk" "$INSTDIR\Blacktable Studio.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${PRODUCT}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\Blacktable Studio.exe"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "Brian"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\Blacktable Studio.lnk"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
  RMDir /r "$INSTDIR\runtime"
  RMDir /r "$INSTDIR\ffmpeg"
  RMDir /r "$INSTDIR\web"
  Delete "$INSTDIR\app.py"
  Delete "$INSTDIR\Third-party notices.txt"
  Delete "$INSTDIR\Blacktable Studio.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
SectionEnd
