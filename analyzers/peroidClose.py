
#+=================================================================================+
# |Author : Koushik Chakraborty
# |Creation date : 28-Jul-2016
# |Modified On : 10-Aug-2016
# |Version : 1.0
# |Catagory : MT
# |DESCRIPTION 
# |   used to prepare plan for EBS Payables Period Close Analyzer (Doc ID 1489381.1)
# |PLATFORM      
# |   Linux 
#+=================================================================================+

######################################################
# EBS Payables Period Close Analyzer (Doc ID 1489381.1)
######################################################

from functions import *


def chooseOption():
	print '''
	 Available Options :

			1. Run "ap_period_close_analyze.sql" via SQLPlus 
			2. Register as a concurrent Program
	'''
	global analyzeScript, regConcProg
	analyzeScript, regConcProg = False, False

	choice = input("Please enter your choice(1/2) : ")
	if (choice == 1):
		analyzeScript = True
	elif (choice == 2):
		regConcProg = True
	else:
		print "Invalid Option. Enter a valid option\n";
		chooseOption()

def getVersions():
	global latestVersion, installedVersion
	print '''
	EBS Payables Period Close Analyzer (Doc ID 1489381.1)
	(URL: https://mosemp.us.oracle.com/epmos/faces/DocumentDisplay?id=1489381.1)
	'''
	rawLatestVersion = raw_input("Please Enter the latest version of Analyzer from the above URL(e.g 200.10) : ")
	try :
		rawInstalledVersion = rawVersion.split()[3]
		shiftAmount = max(len(rawLatestVersion.split('.')[1]), len(rawInstalledVersion.split('.')[1]))
		latestVersion = int(rawLatestVersion.split('.')[0])*10**shiftAmount + int(rawLatestVersion.split('.')[1])
		installedVersion = int(rawInstalledVersion.split('.')[0])*10**shiftAmount + int(rawInstalledVersion.split('.')[1])
		if latestVersion < installedVersion:
			print "\nYou entered a lower version. Please enter the correct lastest version.\n"
			getVersions()
	except:
		print "\nWrong input. Version should contain only numeric characters(e.g 200.10)...\n"
		getVersions()


commandCeckVersion = '''set head off
set feedback off
select text from dba_source where name = 'AP_PCLOSE_ANALYZER_PKG' and text like '%$Id%';
'''
commandCheckPkg = '''
set feedback off
set head off
select status from dba_objects where object_type like 'PACKAGE%'and object_name = 'AP_PCLOSE_ANALYZER_PKG';
'''
commandCheckConc = '''
set feedback off
set head off
select USER_CONCURRENT_PROGRAM_NAME from fnd_concurrent_programs_vl where USER_CONCURRENT_PROGRAM_NAME = 'Payables Period Close Analyzer';
'''

#### __main__

verifyPasswd()

appVersion = getAppsVersion()
if appVersion[:2] == '11' or appVersion[:2] == '10':
	print "This Analyzer is only applicable for Version 12.0.0 and later"
	sys.exit()

chooseOption()


rawVersion = runSqlQuery(commandCeckVersion)[0]
versionAvailable = rawVersion != ''
latestVersion, installedVersion = 1, 0

if versionAvailable:
	getVersions()


pkgInstalled = runSqlQuery(commandCheckPkg)[0] != ''

ConcRegistered = runSqlQuery(commandCheckConc)[0] != ''

#############################
# Print Findings
print "\n\n\n"
print '''
  FINDINGS:
  #########

  DATE :
  -------
 ''',
print time.strftime("%d/%m/%Y")
print '''
  INSTANCE DETAILS:
  ---------------------
  '''
## Get instance details
command1 = '''show user;
select name,created from v$database;
select release_name from apps.fnd_product_groups;
'''
system("id;hostname -f; uname -a")
print runSqlQuery(command1)[0]

print '''STATUS OF AP_PCLOSE_ANALYZER_PKG :
-------------------------------------------'''

command2 = '''
col owner for a12;
col object_name for a30;
col object_type for a12;
col status for a7;
select owner,object_name,object_type,status,CREATED from dba_objects where object_type like 'PACKAGE%'and object_name = 'AP_PCLOSE_ANALYZER_PKG';
'''

print "select owner,object_name,object_type,status,CREATED from dba_objects where object_type like 'PACKAGE%'and object_name = 'AP_PCLOSE_ANALYZER_PKG';"
print runSqlQuery(command2)[0]

print "select text from dba_source where name = 'AP_PCLOSE_ANALYZER_PKG' and type like 'PACKAGE%' and text like '%$Id%';"
print runSqlQuery("select text from dba_source where name = 'AP_PCLOSE_ANALYZER_PKG' and type like 'PACKAGE%' and text like '%$Id%';")[0]

print "select USER_CONCURRENT_PROGRAM_NAME from fnd_concurrent_programs_vl where USER_CONCURRENT_PROGRAM_NAME = 'Payables Period Close Analyzer';"
print runSqlQuery("select USER_CONCURRENT_PROGRAM_NAME from fnd_concurrent_programs_vl where USER_CONCURRENT_PROGRAM_NAME = 'Payables Period Close Analyzer';")[0]

############################
# variables for storing Plans for different options
planBkpPkg = '''	a) Take the backup of package body and specification of AP_PCLOSE_ANALYZER_PKG

		command:
		~~~~~~~~
		SET LINESIZE 100
		SET VERIFY OFF
		SET FEEDBACK OFF
		SET PAGESIZE 999
		set echo off
		set heading off
		SPOOL /ood_repository/scripts/<RFC_number>/AP_PCLOSE_ANALYZER_PKG_bkp.sql
		Select text from dba_source where name='AP_PCLOSE_ANALYZER_PKG';
		SPOOL OFF
		SET VERIFY ON FEEDBACK ON

	b) Run below script:
	drop_ap_period_close_analyzer.sql
'''
planCreatePkg = '''  
	3. Run the script 
	  ap_period_close_analyzer.sql
	
	4. Make sure the package and package body 'AP_PCLOSE_ANALYZER_PKG' is in valid status :

		SELECT OWNER, OBJECT_NAME, STATUS FROM DBA_OBJECTS WHERE OBJECT_NAME 
		like 'AP_PCLOSE_ANALYZER_PKG';
'''
planAnalyzeScript = '''<Note to Planner:
If value of parameter 'AP Data Validation Report' = Y then perform below activity and include step a) in plan:
Download the latest ap_gdf_detect_pkg.zip (Doc ID 1360390.1)
from URL = https://mosemp.us.oracle.com/epmos/faces/DocumentDisplay?id=1360390.1
upload the zip file to host in location(= /ood_repository/scripts/<RFC_number>) and unzip all the contents

	a) Run ap_gdf_detect_pkg.sql>

	Run the script 'ap_period_close_analyze.sql'
	<Note to Planner: Fill the below parameters with the values provided in the RFC>

		PARAMETERS:
		**********
		a) Ledger ID: (REQUIRED) 
		b) Period Name: (REQUIRED)
		c) Operating Unit: (OPTIONAL)
		d) AP Data Validation Report: (OPTIONAL)
		e) Maximum Number of Rows: (DEFAULT of 10)
'''
planRegConcProg = '''
	A) Register the concurrent program "Payables Period Close Analyzer" in the Purchasing application:

	  1. Run below command from bash
  
	  FNDLOAD apps/<appspw> 0 Y UPLOAD $FND_TOP/patch/115/import/afcpprog.lct AP_PCLOSEAZ.ldt CUSTOM_MODE=FORCE
  
	  2. Navigate to System Administrator => Security -> Responsibility -> Request

	Search for "All Reports" group and application "Payables" and include the program "Payables Period Close Analyzer"

	B) <Note to Planner:
	Customer needs to provide the responsibility they will use to run the program.
	If that request_group does not include all Payables programs at the application level then only proceed with steps below (5.B)>

	  1.  To determine what report group your responsibility uses, connect to the System Administrator responsibility
	  2.  Navigate to Security > Responsibility > Define 
	  3.  Under "Request Group" note down the name and query up this request group in Security > Responsibility > Request
	  4.  If there is no entry with Type=Application and Name=Payables, then you may need to add an entry for these programs here.

	  		Payables Period Close Analyzer
'''
planUpload = '''Upload the output AP_PCLOSE_Analyzer_<machine>_<sid>_<date>.html
	to RFC and update the SR/Customer."
'''

############################
# Print Action Plan

if ConcRegistered and regConcProg and (installedVersion == latestVersion):
	print "\nThis program is already registered as Concurrent Program.\n"
	sys.exit()

else:
	print '''
	  ACTION PLAN
	  #############

	Note to Planner:
	---------------
	< Download the EBS Payables Period Close Analyzer (Doc ID 1489381.1)
	 (URL: https://mosemp.us.oracle.com/epmos/faces/DocumentDisplay?id=1489381.1)
	 upload the zip file to host in location(= /ood_repository/scripts/<RFC_number>) and unzip all the contents >

	1. cd /ood_repository/scripts/<RFC_number>

	2. sqlplus apps
	'''
	if pkgInstalled:
		if not versionAvailable:
			print planBkpPkg
			print planCreatePkg
			if analyzeScript:
				print "\t5. ",planAnalyzeScript
				print "\t6. ",planUpload
			elif regConcProg:
				print "\t5. ",planRegConcProg

		else:
			if installedVersion < latestVersion:
				print planBkpPkg
				print planCreatePkg
				if analyzeScript:
					print "\t5. ",planAnalyzeScript
					print "\t6. ",planUpload
				elif regConcProg:
					print "\t5. ",planRegConcProg

			elif installedVersion == latestVersion:
				if analyzeScript:
					print "\t3. ",planAnalyzeScript
					print "\t4. ",planUpload
				elif regConcProg:
					sys.stdout.write("\033[F\033[F") # Move to Previously printed line
					sys.stdout.write("\033[K") # Delete that line (2. sqlplus apps)
					print "\t2. ",planRegConcProg
				
	else:
		print planCreatePkg
		if analyzeScript:
			print "\t5. ",planAnalyzeScript
			print "\t6. ",planUpload
		elif regConcProg:
			print "\t5. ",planRegConcProg


	print '''
	  ESTIMATE TIME
	  ##############
	   
	  WINDOW : SERVICE
	  TIME   : 1.5 Hours

	'''
