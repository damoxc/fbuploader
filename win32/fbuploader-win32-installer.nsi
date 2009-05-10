# FBUploader installer script
# Version 0.1 10-May-2009
#
# Copyright (c) 2009 Damien Churchill <damoxc@gmail.com>
#
# FBUploader is free software
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# FBUploader is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have receieved a copy fo the GNU General Public License
# along with fbuploader. If not, write to:
#		The Free Software Foundation, Inc.,
#		51 Franklin Street, Fifth Floor
#		Boston, MA	02110-1301, USA.
#

SetCompressor lzma

!define FBUPLOADER_INSTALLER_VERSION "0.1"

# Program Info
!define PROGRAM_NAME "FBUploader"
!define PROGRAM_VERSION "0.1"
!define PROGRAM_WEB_SITE "http://fbuploader.damoxc.net"

!define FBUPLOADER_BBFREEZE_OUTPUT_DIR "..\dist\${PROGRAM_NAME}-${PROGRAM_VERSION}"

!define FBUPLOADER_GTK_DEPENDENCY "gtk2-runtime-2.61.1-2009-04-21-ash.exe"

# --- Interface settings ---

# Modern User Interface 2
!include MUI2.nsh

# Installer
!define MUI_ICON "fbuploader.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "installer-top.bmp"
!define MUI_WELCOMEFINISHPAEG_BITMAP "installer-side.bmp"
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_ABORTWARNING

# Uninstaller
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
#!define MUI_HEADERIMAGE_UNBITMAP "installer-top.bmp
!define MUI_WELCOMEFINISHPAGE_UNBITMAP "installer-side.bmp"
!define MUI_UNFINISHPAGE_NOAUTOCLOSE

# --- Start of Modern User Interface ---

# Welcome page
!insertmacro MUI_PAGE_WELCOME

# License page
!insertmacro MUI_PAGE_LICENSE "..\COPYING"

# Components page
!insertmacro MUI_PAGE_COMPONENTS

# Let the user select the installation directory
!insertmacro MUI_PAGE_DIRECTORY

# Run installation
!insertmacro MUI_PAGE_INSTFILES

# Display 'finished' page
!insertmacro MUI_PAGE_FINISH

# Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

# Language files
!insertmacro MUI_LANGUAGE "English"


# --- Functions ---

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Do you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

# --- Installation sections ---

# Compare versions
!include "WordFunc.nsh"

!define PROGRAM_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}"
!define PROGRAM_UNINST_ROOT_KEY "HKLM"

# Branding text
BrandingText "FBUploader Windows Installer v${FBUPLOADER_INSTALLER_VERSION}"

Name "${PROGRAM_NAME} ${PROGRAM_VERSION}"
OutFile "..\dist\FBUploader-${PROGRAM_VERSION}-win32-setup.exe"

# The Python bbfreeze files will be placed here
!define FBUploader_PYTHON_SUBDIR "$INSTDIR\FBUploader-Python"

InstallDir "$PROGRAMFILES\FBUploader"

ShowInstDetails show
ShowUnInstDetails show

# Install main application
Section "Deluge Bittorrent Client" Section1
  SectionIn RO
  
  Rmdir /r "${FBUPLOADER_PYTHON_SUBDIR}"
  SetOutPath "${FBUPLOADER_PYTHON_SUBDIR}"
  File /r "${FBUPLOADER_BBFREEZE_OUTPUT_DIR}\*.*"
  
  # Clean up previous confusion between Deluge.ico and deluge.ico (seems to matter on Vista registry settings?)
  Delete "$INSTDIR\Deluge.ico"    
    
  SetOverwrite ifnewer
  SetOutPath $INSTDIR
  File "..\COPYING"
  File "StartX.exe"
  File "fbuploader.ico"
  
  # Create fbuploader.cmd file
  fileOpen $0 "$INSTDIR\fbuploader.cmd" w
  fileWrite $0 '@ECHO OFF$\r$\n'
  fileWrite $0 'SET FBUPLOADERFOLDER="$INSTDIR"$\r$\n'
  fileWrite $0 '"$INSTDIR\StartX.exe" /B /D%FBUPLOADERFOLDER% "$INSTDIR\FBUploader-Python\fbuploader.exe "%1" "%2" "%3" "%4""$\r$\n'
  fileClose $0
SectionEnd

Section -StartMenu_Desktop_Links
  WriteIniStr "$INSTDIR\homepage.url" "InternetShortcut" "URL" "${PROGRAM_WEB_SITE}"

  CreateDirectory "$SMPROGRAMS\FBUploader"
  CreateShortCut "$SMPROGRAMS\FBUploader\FBUploader.lnk" "$INSTDIR\fbuploader.cmd" "" "$INSTDIR\fbuploader.ico"
  CreateShortCut "$SMPROGRAMS\FBUploader\Project homepage.lnk" "$INSTDIR\homepage.url"
  CreateShortCut "$SMPROGRAMS\FBUploader\Uninstall FBUploader.lnk" "$INSTDIR\FBUploader-uninst.exe" 
  CreateShortCut "$DESKTOP\FBUploader.lnk" "$INSTDIR\fbuploader.cmd" "" "$INSTDIR\fbuploader.ico"
SectionEnd

Section -Uninstaller
  WriteUninstaller "$INSTDIR\FBUploader-uninst.exe"
  WriteRegStr ${PROGRAM_UNINST_ROOT_KEY} "${PROGRAM_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PROGRAM_UNINST_ROOT_KEY} "${PROGRAM_UNINST_KEY}" "UninstallString" "$INSTDIR\FBUploader-uninst.exe"
  WriteRegStr ${PROGRAM_UNINST_ROOT_KEY} "${PROGRAM_UNINST_KEY}" "DisplayIcon" "$INSTDIR\fbuploader.ico"
SectionEnd

# Install GTK+ 2.16
Section "GTK+ 2.16 runtime" Section3
  # Check whether GTK+ 2.16 is installed on the system; if so skip this section
  # The criterion is whether the registry key HKLM\SOFTWARE\GTK\2.0\Version exists
  ReadRegStr $0 HKLM "SOFTWARE\GTK\2.0" "Version"
  IfErrors GTK_install_start 0
  
  ${VersionCompare} $0 "2.11" $1
  StrCmp $1 "2" 0 +3
  MessageBox MB_ICONEXCLAMATION|MB_OK "Your GTK+ runtime version is $0 and Deluge will not work with GTK+ 2.10 or earlier. \
         The Deluge installer will not download and install GTK+ 2.16 runtime. Sorry, but you will have to resolve this conflict manually. \
         If in doubt, you can ask for help in the Deluge forum or IRC channel."
  Goto GTK_install_exit
  
  ${VersionCompare} $0 "2.13" $1
  StrCmp $1 "1" 0 +3
  MessageBox MB_ICONEXCLAMATION|MB_OK "You have GTK+ $0 installed on your system. \
     The Deluge installer will not download and install the GTK+ 2.16 runtime. \
     Please note that GTK+ 2.14 has not been tested as thoroughly as the GTK+ 2.12 version, but it should work.."
  Goto GTK_install_exit   
  
  MessageBox MB_OK "You have GTK+ $0 installed on your system. The FBUploader installer will not download and install the GTK+ runtime."
  Goto GTK_install_exit

  GTK_install_start:
  MessageBox MB_OK "You will now download and run the installer for the GTK+ 2.16 runtime. \
    You must be connected to the internet before you press the OK button. \
    The GTK+ runtime can be installed in any location, \
    because the GTK+ installer adds the location to the global PATH variable. \
    Please note that the GTK+ 2.16 runtime is not removed by the FBUploader uninstaller. \
    You must use the GTK+ 2.16 uninstaller if you want to remove it together with FBUploader." 
  
  # Download GTK+ installer to TEMP dir
  NSISdl::download http://fbuploader.damoxc.net/downloads/windows/deps/${FBUPLOADER_GTK_DEPENDENCY} "$TEMP\${FBUPLOADER_GTK_DEPENDENCY}"
  
  # Get return value (success, cancel, or string describing the network error)
  Pop $2
  StrCmp $2 "success" 0 GTK_download_error

  ExecWait "$TEMP\${FBUPLOADER_GTK_DEPENDENCY}"
  Goto GTK_install_exit
  
  GTK_download_error:
  MessageBox MB_ICONEXCLAMATION|MB_OK "Download of GTK+ 2.12 installer failed (return code: $2). \
      You must install the GTK+ 2.12 runtime manually, or Deluge will fail to run on your system."
  
  GTK_install_exit:
SectionEnd



LangString DESC_Section1 ${LANG_ENGLISH} "Install FBUploader."
LangString DESC_Section2 ${LANG_ENGLISH} "Select this option unless you have another torrent client which you want to use for opening .torrent files."
LangString DESC_Section3 ${LANG_ENGLISH} "Download and install the GTK+ 2.12 runtime. \
  This is skipped automatically if GTK+ is already installed."
 
# --- Uninstallation section(s) ---

Section Uninstall
  Rmdir /r "${FBUPLOADER_PYTHON_SUBDIR}"
  
  Delete "$INSTDIR\FBUploader-uninst.exe"
  Delete "$INSTDIR\COPYING"
  Delete "$INSTDIR\fbuploader.cmd"
  Delete "$INSTDIR\StartX.exe"
  Delete "$INSTDIR\homepage.url"
  Delete "$INSTDIR\fbuploader.ico"
    
  Delete "$SMPROGRAMS\FBUploader\FBUploader.lnk"
  Delete "$SMPROGRAMS\FBUploader\Uninstall FBUploader.lnk"
  Delete "$SMPROGRAMS\FBUploader\Project homepage.lnk"
  Delete "$DESKTOP\FBUploader.lnk"
  
  RmDir "$SMPROGRAMS\FBUploader"
  RmDir "$INSTDIR"

  DeleteRegKey ${PROGRAM_UNINST_ROOT_KEY} "${PROGRAM_UNINST_KEY}"
  
  FBUPLOADER_skip_delete:
  # This key is only used by FBUploader, so we should always delete it
  DeleteRegKey HKCR "FBUploader"
SectionEnd
