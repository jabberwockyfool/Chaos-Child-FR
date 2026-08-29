; ============================================================================
;  CHAOS;CHILD - Patch Francais  |  Les Enfants du ChaoS
;  Installeur Inno Setup : copie le contenu de DIST\ a la racine du jeu.
;  Build : installer\build-installer.ps1  (lance build-dist.ps1 puis ISCC)
; ============================================================================

#define AppName        "CHAOS;CHILD - Patch Francais"
#define AppShortName   "ChaosChildFR"
; surchargeable : ISCC /DAppVersion=1.1.0
#ifndef AppVersion
  #define AppVersion   "1.0.0"
#endif
#define AppPublisher   "Les Enfants du ChaoS"
#define AppUrl         "https://github.com/jabberwockyfool/Chaos-Child-FR"
#define DistDir        "..\DIST"
#define SteamAppId     "970570"
#define BackupSubDir   "languagebarrier\frpatch\backup"
#define MetaSubDir     "languagebarrier\frpatch"

[Setup]
AppId={{8F3C1A64-2D77-4B19-9A5E-CC0F00000001}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
VersionInfoVersion={#AppVersion}

; {app} = racine du jeu. Elle est pre-remplie par le code de detection.
DefaultDirName={code:GetDefaultGameDir}
DirExistsWarning=no
AppendDefaultDirName=no
DisableProgramGroupPage=yes
DisableReadyPage=no
AllowNoIcons=yes

; Steam peut etre sous Program Files : on demande l'elevation seulement si besoin.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Icone de l'installeur, du desinstalleur et de l'entree "Applications installees".
SetupIconFile=..\ICON.ico
UninstallDisplayName={#AppName}
UninstallDisplayIcon={uninstallexe}
UninstallFilesDir={app}\{#MetaSubDir}
CreateUninstallRegKey=yes

OutputDir=output
OutputBaseFilename={#AppShortName}-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
fr.GameDirPageCaption=Dossier d'installation du jeu
fr.GameDirPageDesc=Ou CHAOS;CHILD est-il installe ?
fr.GameDirPageLabel=Selectionnez la racine du jeu, c'est-a-dire le dossier qui contient Game.exe. Le patch y sera copie.
fr.NotAGameDir=Ce dossier ne contient pas Game.exe. Selectionnez la racine de CHAOS;CHILD (par ex. ...\steamapps\common\CHAOS;CHILD).
fr.NoCozPatch=Le patch anglais du Committee of Zero (v2.2.0) ne semble pas installe dans ce dossier : le sous-dossier "languagebarrier" est introuvable.%n%nLe patch francais s'installe PAR-DESSUS le patch CoZ. Installez-le d'abord, puis relancez cet installeur.%n%nContinuer quand meme ?
fr.GameRunning=CHAOS;CHILD (Game.exe) semble en cours d'execution. Fermez le jeu avant de continuer.
fr.BackupStatus=Sauvegarde des fichiers d'origine...
fr.FinishedInfo=Le patch francais a ete installe. Lancez le jeu normalement (Steam, GOG ou LauncherC0.exe).
en.GameDirPageCaption=Game installation folder
en.GameDirPageDesc=Where is CHAOS;CHILD installed?
en.GameDirPageLabel=Select the game root, i.e. the folder containing Game.exe. The patch will be copied there.
en.NotAGameDir=This folder does not contain Game.exe. Please select the CHAOS;CHILD root folder.
en.NoCozPatch=The Committee of Zero English patch (v2.2.0) does not appear to be installed here: the "languagebarrier" subfolder is missing.%n%nThe French patch installs ON TOP of the CoZ patch. Install it first, then run this installer again.%n%nContinue anyway?
en.GameRunning=CHAOS;CHILD (Game.exe) appears to be running. Please close the game before continuing.
en.BackupStatus=Backing up original files...
en.FinishedInfo=The French patch has been installed. Launch the game as usual.

[Messages]
fr.WizardSelectDir={cm:GameDirPageCaption}
fr.SelectDirDesc={cm:GameDirPageDesc}
fr.SelectDirLabel3={cm:GameDirPageLabel}
en.WizardSelectDir={cm:GameDirPageCaption}
en.SelectDirDesc={cm:GameDirPageDesc}
en.SelectDirLabel3={cm:GameDirPageLabel}

[Files]
; Charge utile : tout DIST\ est deverse tel quel a la racine du jeu.
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Manifeste : extrait tot (dontcopy) pour la sauvegarde. Il est ensuite copie par
; le code dans le dossier de sauvegarde -- surtout PAS via [Files], sinon Inno le
; supprimerait avant l'etape de restauration de la desinstallation.
Source: "manifest.txt"; Flags: dontcopy

[Code]
var
  GameDirDetected: string;

// ---------------------------------------------------------------- utilitaires

function IsGameDir(const Dir: string): Boolean;
begin
  Result := (Dir <> '') and FileExists(AddBackslash(Dir) + 'Game.exe');
end;

function HasCozPatch(const Dir: string): Boolean;
begin
  Result := DirExists(AddBackslash(Dir) + 'languagebarrier');
end;

// ------------------------------------------------------- detection Steam/GOG

function TrySteamUninstallKey(var Dir: string): Boolean;
var
  S: string;
begin
  Result := False;
  if RegQueryStringValue(HKLM32,
       'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App {#SteamAppId}',
       'InstallLocation', S) then
    if IsGameDir(S) then
    begin
      Dir := S;
      Result := True;
    end;
end;

function TrySteamLibraries(var Dir: string): Boolean;
var
  SteamPath, Vdf, Line, P, Candidate: string;
  Lines: TArrayOfString;
  I, Q1, Q2: Integer;
begin
  Result := False;
  if not RegQueryStringValue(HKCU, 'Software\Valve\Steam', 'SteamPath', SteamPath) then
    Exit;
  StringChangeEx(SteamPath, '/', '\', True);
  Vdf := AddBackslash(SteamPath) + 'steamapps\libraryfolders.vdf';
  if not FileExists(Vdf) then Exit;
  if not LoadStringsFromFile(Vdf, Lines) then Exit;

  for I := 0 to GetArrayLength(Lines) - 1 do
  begin
    Line := Trim(Lines[I]);
    if Pos('"path"', Line) = 1 then
    begin
      // "path"  "D:\\SteamLibrary"  ->  on extrait la seconde chaine entre guillemets
      P := Copy(Line, 7, Length(Line));
      Q1 := Pos('"', P);
      if Q1 = 0 then Continue;
      P := Copy(P, Q1 + 1, Length(P));
      Q2 := Pos('"', P);
      if Q2 = 0 then Continue;
      P := Copy(P, 1, Q2 - 1);
      StringChangeEx(P, '\\', '\', True);
      Candidate := AddBackslash(P) + 'steamapps\common\CHAOS;CHILD';
      if IsGameDir(Candidate) then
      begin
        Dir := Candidate;
        Result := True;
        Exit;
      end;
    end;
  end;
end;

function TryGog(var Dir: string): Boolean;
var
  Keys: TArrayOfString;
  I: Integer;
  Name, Path: string;
begin
  Result := False;
  if not RegGetSubkeyNames(HKLM32, 'SOFTWARE\GOG.com\Games', Keys) then Exit;
  for I := 0 to GetArrayLength(Keys) - 1 do
  begin
    if RegQueryStringValue(HKLM32, 'SOFTWARE\GOG.com\Games\' + Keys[I], 'gameName', Name) then
      if Pos('CHAOS', Uppercase(Name)) > 0 then
        if RegQueryStringValue(HKLM32, 'SOFTWARE\GOG.com\Games\' + Keys[I], 'path', Path) then
          if IsGameDir(Path) then
          begin
            Dir := Path;
            Result := True;
            Exit;
          end;
  end;
end;

function GetDefaultGameDir(Param: string): string;
var
  Dir: string;
begin
  if GameDirDetected = '' then
  begin
    Dir := '';
    if TrySteamUninstallKey(Dir) or TrySteamLibraries(Dir) or TryGog(Dir) then
      GameDirDetected := Dir
    else
      GameDirDetected := ExpandConstant('{autopf}\CHAOS;CHILD');
  end;
  Result := GameDirDetected;
end;

// ------------------------------------------------------------------ sauvegarde

procedure BackupOriginals;
var
  Manifest, Rel, Src, Dst, AppDir, BackupRoot: string;
  Lines: TArrayOfString;
  I: Integer;
begin
  ExtractTemporaryFile('manifest.txt');
  Manifest := ExpandConstant('{tmp}\manifest.txt');
  if not LoadStringsFromFile(Manifest, Lines) then Exit;

  AppDir := AddBackslash(ExpandConstant('{app}'));
  BackupRoot := AppDir + '{#BackupSubDir}';

  // Le desinstalleur relit ce manifeste : il doit vivre la ou Inno ne le suit pas.
  ForceDirectories(BackupRoot);
  CopyFile(Manifest, AddBackslash(BackupRoot) + 'manifest.txt', False);

  for I := 0 to GetArrayLength(Lines) - 1 do
  begin
    Rel := Trim(Lines[I]);
    if Rel = '' then Continue;
    Src := AppDir + Rel;
    Dst := AddBackslash(BackupRoot) + Rel;
    // On ne sauvegarde qu'une fois : une reinstallation ne doit pas ecraser
    // la sauvegarde d'origine avec des fichiers deja francises.
    if FileExists(Src) and (not FileExists(Dst)) then
    begin
      ForceDirectories(ExtractFileDir(Dst));
      CopyFile(Src, Dst, False);
    end;
  end;
end;

// ---------------------------------------------------------------------- wizard

function InitializeSetup: Boolean;
begin
  GameDirDetected := '';
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    if not IsGameDir(WizardDirValue) then
    begin
      MsgBox(CustomMessage('NotAGameDir'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not HasCozPatch(WizardDirValue) then
      if MsgBox(CustomMessage('NoCozPatch'), mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
        Exit;
      end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    WizardForm.StatusLabel.Caption := CustomMessage('BackupStatus');
    BackupOriginals;
  end;
end;

// -------------------------------------------------------------- desinstallation

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir, BackupRoot, Manifest, Rel, Src, Dst: string;
  Lines: TArrayOfString;
  I: Integer;
begin
  if CurUninstallStep <> usPostUninstall then Exit;

  AppDir := AddBackslash(ExpandConstant('{app}'));
  BackupRoot := AppDir + '{#BackupSubDir}';
  Manifest := AddBackslash(BackupRoot) + 'manifest.txt';
  if not FileExists(Manifest) then Exit;
  if not LoadStringsFromFile(Manifest, Lines) then Exit;

  for I := 0 to GetArrayLength(Lines) - 1 do
  begin
    Rel := Trim(Lines[I]);
    if Rel = '' then Continue;
    Src := AddBackslash(BackupRoot) + Rel;
    Dst := AppDir + Rel;
    if FileExists(Src) then
    begin
      ForceDirectories(ExtractFileDir(Dst));
      CopyFile(Src, Dst, False);   // restaure l'original anglais
    end
    else
      DeleteFile(Dst);             // fichier ajoute par le patch FR : on l'enleve
  end;

  // Dossier cree par le patch FR pour le Rich Presence : vide une fois l'exe
  // supprime par la boucle ci-dessus, il ne doit pas rester derriere.
  RemoveDir(AppDir + 'languagebarrier\rpc');

  DelTree(BackupRoot, True, True, True);
  // Le dossier meta ne part que s'il est vide : unins000.exe s'y auto-supprime apres coup.
  RemoveDir(AppDir + '{#MetaSubDir}');
end;
