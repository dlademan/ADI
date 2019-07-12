************************************************************

*Product Name: Alternative Daz Importer

*Copyright: 7/2019

Please Contact indusfre via Renderosity Site Mail

************************************************************

-------------------------------------------------------------------------------

Product description

-------------------------------------------------------------------------------

ADI facilitates the installation and uninstallation of assets for Daz Studio.

Features:
	- Saves the structure of zips to uninstall later, without the zip needing 
	  to be present
	- Tree view to categorize your zip packages
	- List view for easy readability
	- Search for assets via asset name or dynamic tags based on folder structure
	- Queue multiple assets to be installed simultaneously
	- View info about the zip file in ADI
	- View the contents of the zip in ADI

-------------------------------------------------------------------------------

System requirements

-------------------------------------------------------------------------------

Windows versions 7 and newer.

-------------------------------------------------------------------------------

Necessary Files

------------------------------------------------------------------------------- 

This is a stand alone program, merely run it separate from Daz Studio. 

It is recommended to restart Daz after installing assets.

-------------------------------------------------------------------------------

Setup and Use instructions

-------------------------------------------------------------------------------

ADI is a package manager that installs assets and manages your library for ease
of use.

All assets must be supplied to ADI as a zip file, and an error will show in the 
log file if the zip has errors or is malformed. If an asset is not detected by
ADI, please check that the asset package is not a rar and is a valid zip file.

Setup:

	1) Download the most recent version of ADI from renderosity.
	
	2) Extract to desired location. 
	   ADI will not install as a windows application.
	   
	3) Navigate into the ADI folder inside, and run adi.exe to start the program
	
First Launch:

	Upon first launch of ADI, the Configuration window will pop up. Default 
	directories of Daz Studio are provided, but yours will likely be different.
	Read below for descriptions of each setting.
	
Configuration Options:
	
	Zip Archive: 
		This is where your asset packages are located. As described before, 
		only valid zip files are accepted by ADI. Feel free to sort your assets
		in folders, as ADI will reflect this in the tree view. 
		
		The folder structure of your archive will apply tags to the asset, 
		allowing you to search for tags that are not in the asset's title. 
		e.g. an asset in "Genesis 8/Hair/" can be searchable by "genesis 8" OR
		"hair", capitalization and spaces not needed.
		
	Daz Library:
		This is where assets are installed to, the folder that Daz Studio looks
		in for assets. Be sure to not point it at the folder containing 
		"My Library" or "Content". ADI will automatically format zips to not 
		include the "Content" folder included in DIM zips and "My Library"
		used in other stores formats such as Renderosity.
		
	Clear Queue on program close:
		This option wipes your queue each time you start ADI. Mark to personal
		preference.
		
	Expand tree fully:
		This applies to the tree view for assets, starting with a completely
		expanded tree when you refresh the UI or start ADI.
		
	Close queue dialog upon completion:
		When you start a queue or install/uninstall a single asset, a dialog 
		appears to show the progress of each asset operation being completed. 
		This options will close the dialog automatically upon finishing all 
		required tasks.
		
Processing Assets:
	
	ADI will let you install and uninstall single assets via the context menu 
	(right click) or the appropriate button under the asset description. A 
	dialog will appear, with the asset being processed along with a progress 
	bar showing how far along it is.
	
	If one wants to process multiple assets at once, use the context menu or
	applicable button to queue the asset to be processed. You can view the
	status of the queue under the asset description area on the Queue tab.
	There is a clear queue button on the toolbar for quick wiping.
	
	When all assets are queued to the user's satisfaction, press start queue
	at the top left of the program. A similar dialog will appear with asset 
	names and progress bars, each process occuring on their own thread.
		
Tree View:
	
	The tree view will crawl your provided Zip Archive and create a tree based 
	on the folder structure. This folder structure is where ADI creates tags for 
	assets.
	
List View:

	The List View lists all of your assets in the ADI databse. The user can 
	directly act with assets here just as with the tree view.
	
Directory Options:
	
	Queue Directory to be Installed:
		This only queues assets to be installed if the asset is not 
		installed  at the moment. It will ignore all assets already 
		installed.
		
	Queue Directory to be Uninstalled:
		This only queues assets to be installed if the asset is installed 
		at the moment. It will ignore all assets not installed.
		
	Open Location:
		Opens the selected directory in explorer.
		
	Detect Assets in Directory:
		This option allows the user to selectively detect assets, only 
		checking the assets in this directory.
		
	Refresh:
		This option will rebuild the tree view and list view from scratch,
		and add any files that have been added to the archive since ADI has 
		started.
		
Asset Options:

	Install:
		Immediately installs the asset to the provided library location.
		
	Queue Install:
		Queues the asset to be installed at a later time.
		
	Uninstall:
		Immediately uninstalls the asset to the provided library location.
		
	Queue Uninstall:
		Queues the asset to be uninstalled at a later time.
		
	Open File Location:
		Opens the folder containing this zip file, if it exists.
		
	Detect Asset:
		Detects if this specific asset is installed.
		
	Refresh:
		This option will rebuild the tree view and list view from scratch,
		and add any files that have been added to the archive since ADI has 
		started.
	
Menu options:
	
	File:
		
		Refresh:
			This option will rebuild the tree view and list view from scratch,
			and add any files that have been added to the archive since ADI has 
			started.
			
		Quit:
			Safely closes ADI. This is the same as pressing the X on the main 
			window frame to close ADI.
			
	Library:
		
		Open Zip Archive:
			This opens a new explorer window to the location of your zip 
			archive.
			
		Open Library:
			This opens a new explorer window to the location where your assets
			are installed.
			
		Detect Installed Assets:
			This analyzes your current library and compares them to the assets
			imported to ADI. Assets installed manually or via DIM will be 
			detected, allowing ADI to work with existing libraries.
			
		Merge Backed up Assets:
			All asset information is saved to local files in 
			<local roaming>ADI/Backup/
			
			If your ADI databased ever becomes corrupt, you can use this option
			to import these assets back into ADI, without needing the original 
			zip. ADI will then be allowed to detect them and uninstall if 
			desired.
			
		Reimport All Assets:
			This will wipe the ADI databased currently being used and reimport
			all assets in your archive. If you do not still have a zip file for
			an asset, please merge the backups with the previous option.
			
		Clean Library:
			This option removes assets from your ADI database if it is not 
			installed and the zip does not exist. This can be used to get rid
			of assets you had installed but no longer use.
			
	View:
	
		Log:
			This is a log of all actions performed by ADI located in 
			<local roaming>ADI/
			Use this to check what you last did, or diagnose problems when
			reporting errors to me.
			
		Configuration:
			This launches the settings dialog, and is the same action as the
			button on the toolbar.
			
		About:
			Information about me and ADI.
			
Useful terms:

	DNE:
		Does not Exist
		
		This is used when a zip package has been removed from your archive but
		is still in ADI.

-------------------------------------------------------------------------------

Files list


ADI
Readme_.txt
Renderosity License.txt
ADI\adi.exe
ADI\aepic.dll
ADI\bcp47mrm.dll
ADI\chakra.dll
ADI\cldapi.dll
ADI\concrt140.dll
ADI\contactactivation.dll
ADI\coremessaging.dll
ADI\coreuicomponents.dll
ADI\cryptnet.dll
ADI\cryptngc.dll
ADI\crypttpmeksvc.dll
ADI\d3d12.dll
ADI\d3dscache.dll
ADI\dbgcore.dll
ADI\dbgeng.dll
ADI\dbgmodel.dll
ADI\dmenterprisediagnostics.dll
ADI\dsclient.dll
ADI\dsreg.dll
ADI\dxilconv.dll
ADI\edgeiso.dll
ADI\edpauditapi.dll
ADI\edputil.dll
ADI\efscore.dll
ADI\efswrt.dll
ADI\fwbase.dll
ADI\fwpolicyiomgr.dll
ADI\hid.dll
ADI\icons
ADI\ieapfltr.dll
ADI\libcrypto-1_1-x64.dll
ADI\libssl-1_1-x64.dll
ADI\mi.dll
ADI\miutils.dll
ADI\msiso.dll
ADI\msvcp110_win.dll
ADI\msvcp140.dll
ADI\msvcp_win.dll
ADI\msvcrt.dll
ADI\ngcrecovery.dll
ADI\pkeyhelper.dll
ADI\policymanager.dll
ADI\pyexpat.pyd
ADI\python37.dll
ADI\rmclient.dll
ADI\select.pyd
ADI\sqlite3.dll
ADI\srpapi.dll
ADI\textinputframework.dll
ADI\tokenbinding.dll
ADI\tpmcoreprovisioning.dll
ADI\unicodedata.pyd
ADI\userdatatypehelperutil.dll
ADI\vcruntime140.dll
ADI\webauthn.dll
ADI\wer.dll
ADI\win32u.dll
ADI\windowsperformancerecordercontrol.dll
ADI\winipcfile.dll
ADI\winmsipc.dll
ADI\winsound.pyd
ADI\wpaxholder.dll
ADI\wpcwebfilter.dll
ADI\wsock32.dll
ADI\wuceffects.dll
ADI\wx
ADI\wxbase30u_net_vc140_x64.dll
ADI\wxbase30u_vc140_x64.dll
ADI\wxmsw30u_adv_vc140_x64.dll
ADI\wxmsw30u_core_vc140_x64.dll
ADI\_asyncio.pyd
ADI\_bz2.pyd
ADI\_ctypes.pyd
ADI\_decimal.pyd
ADI\_elementtree.pyd
ADI\_hashlib.pyd
ADI\_lzma.pyd
ADI\_msi.pyd
ADI\_multiprocessing.pyd
ADI\_overlapped.pyd
ADI\_queue.pyd
ADI\_socket.pyd
ADI\_sqlite3.pyd
ADI\_ssl.pyd
ADI\icons\about.png
ADI\icons\adi_logo.png
ADI\icons\clear.png
ADI\icons\clear_queue.png
ADI\icons\config.png
ADI\icons\queue_start.png
ADI\wx\siplib.pyd
ADI\wx\_adv.pyd
ADI\wx\_core.pyd



-------------------------------------------------------------------------------
