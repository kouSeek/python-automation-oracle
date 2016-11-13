#+=================================================================================+
# |Author : Koushik Chakraborty
# |Creation date : 21-Jul-2016
# |Modified On : 10-Aug-2016
# |Version : 1.0
# |Catagory : MT
# |DESCRIPTION 
# |   used to prepare plan for EBS Procurement Approval Analyzer (Doc ID 1525670.1)
# |PLATFORM      
# |   Linux 
#+=================================================================================+

######################################################
# EBS Procurement Approval Analyzer (Doc ID 1525670.1)
######################################################

from functions import *


def chooseOption():
	print '''
	 Available Options :

			1. Run "po_approval_analyze_single.sql" via SQLPlus (to be run on a single document type and number)
			2. Run "po_approval_analyze_all.sql" via SQLPlus (to check ALL documents within a specific date range)
			3. Register as a concurrent Program
	'''
	global analyzeSingle, analyzeAll, regConcProg
	analyzeSingle, analyzeAll, regConcProg = False, False, False

	choice = input("Please enter your choice(1/2/3) : ")
	if (choice == 1):
		analyzeSingle = True
	elif (choice == 2):
		analyzeAll = True
	elif (choice == 3):
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
		print "\nWrong input. Version should contain only numeric characters(e.g 200.9)...\n"
		getVersions()


commandCeckVersion = '''set head off
set feedback off
select text from dba_source where name = 'PO_APPRVL_ANALYZER_PKG' and type = 'PACKAGE BODY' and text like '%$Id%';
'''
commandCheckPkg = '''
set feedback off
set head off
select status from dba_objects where object_type like 'PACKAGE%'and object_name = 'PO_APPRVL_ANALYZER_PKG';
'''
commandCheckConc = '''
set feedback off
set head off
select USER_CONCURRENT_PROGRAM_NAME from fnd_concurrent_programs_vl where USER_CONCURRENT_PROGRAM_NAME like 'Procurement Approval Analyzer%';
'''

#### __main__

verifyPasswd()

appVersion = getAppsVersion()
if appVersion[:2] == '11' or appVersion[:2] == '10':
	print "This Analyzer is only applicable for Version 12.0.0 to 12.2.4 [Release 12 to 12.2]"
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

print '''STATUS OF PO_APPRVL_ANALYZER_PKG :
-------------------------------------------'''

command2 = '''
col owner for a12;
col object_name for a30;
col object_type for a12;
col status for a7;
select owner,object_name,object_type,status,CREATED from dba_objects where object_type like 'PACKAGE%'and object_name = 'PO_APPRVL_ANALYZER_PKG';
'''

print "select owner,object_name,object_type,status,CREATED from dba_objects where object_type like 'PACKAGE%'and object_name = 'PO_APPRVL_ANALYZER_PKG';"
print runSqlQuery(command2)[0]

print "select text from dba_source where name = 'PO_APPRVL_ANALYZER_PKG' and type like 'PACKAGE%' and text like '%$Id%';"
print runSqlQuery("select text from dba_source where name = 'PO_APPRVL_ANALYZER_PKG' and type like 'PACKAGE%' and text like '%$Id%';")[0]

print "select USER_CONCURRENT_PROGRAM_NAME from fnd_concurrent_programs_vl where USER_CONCURRENT_PROGRAM_NAME like 'Procurement Approval Analyzer%';"
print runSqlQuery("select USER_CONCURRENT_PROGRAM_NAME from fnd_concurrent_programs_vl where USER_CONCURRENT_PROGRAM_NAME like 'Procurement Approval Analyzer%';")[0]

############################
# variables for storing Plans for different options
planBkpPkg = '''	a) Take the backup of package body and specification of PO_APPRVL_ANALYZER_PKG

		command:
		~~~~~~~~
		SET LINESIZE 100
		SET VERIFY OFF
		SET FEEDBACK OFF
		SET PAGESIZE 999
		set echo off
		set heading off
		SPOOL /ood_repository/scripts/<RFC_number>/PO_APPRVL_ANALYZER_PKG_bkp.sql
		Select text from dba_source where name='PO_APPRVL_ANALYZER_PKG';
		SPOOL OFF
		SET VERIFY ON FEEDBACK ON

	b) Run below script:
	drop_po_approval_analyzer.sql
'''
planCreatePkg = '''  
	3. Run the script 
	  po_approval_analyzer.sql
	
	4. Make sure the package and package body 'PO_APPRVL_ANALYZER_PKG' is in valid status :

		SELECT OWNER, OBJECT_NAME, STATUS FROM DBA_OBJECTS WHERE OBJECT_NAME 
		like 'PO_APPRVL_ANALYZER_PKG';
'''
planAnalyzeSingle = '''Run the script 'po_approval_analyze_single.sql'
	<Note to Planner: Fill the below parameters with the values provided in the RFC>

		PARAMETERS:
		**********
		org_id: 
		trx_type: 
		trx_num:
		rel_num:
		from_date:
		max_rows: 
'''	
planAnalyzeAll = '''Run the script 'po_approval_analyze_all.sql'
	<Note to Planner: Fill the below parameters with the values provided in the RFC>

		PARAMETERS:
		**********
		org_id:
		from_date:
		max_output_rows:
'''
planRegConcProg = '''
	A) Register the concurrent program "Procurement Approval Analyzer" in the Purchasing application:

	  1. Run below command from bash
  
	  FNDLOAD apps/<appspw> 0 Y UPLOAD $FND_TOP/patch/115/import/afcpprog.lct POAPPANALYZERAZ.ldt CUSTOM_MODE=FORCE
  
	  2. Navigate to System Administrator -> Security -> Responsibility -> Request

	Search for "All Reports" group and application "Purchasing" and include the program "Procurement Approval Analyzer"

	B) <Note to Planner:
	Customer needs to provide the responsibility they will use to run the program.
	If that report group does not include all Purchasing programs at the application level then only proceed with steps below (5.B)>

	  1.  To determine what report group your responsibility uses, connect to the System Administrator responsibility
	  2.  Navigate to Security > Responsibility > Define 
	  3.  Under "Request Group" note down the name and query up this request group in Security > Responsibility > Request
	  4.  If there is no entry with Type=Application and Name=Purchasing, then you will need to add an entry for the the following programs here:

	     Procurement Approval Analyzer - SINGLE
	     Procurement Approval Analyzer - ALL
'''
planUpload = '''Upload the output POAPPANALYZER_Analyzer_<machine>_<sid>_<date>.html
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
	< Download the EBS Procurement Approval Analyzer latest version from note id: 1525670.1
	 (URL: https://mosemp.us.oracle.com/epmos/faces/DocumentDisplay?id=1525670.1)
	 upload the zip file to host in location(= /ood_repository/scripts/<RFC_number>) and unzip all the contents >

	1. cd /ood_repository/scripts/<RFC_number>

	2. sqlplus apps
	'''
	if pkgInstalled:
		if not versionAvailable:
			print planBkpPkg
			print planCreatePkg
			if analyzeSingle:
				print "\t5. ",planAnalyzeSingle
				print "\t6. ",planUpload
			elif analyzeAll:
				print "\t5. ",planAnalyzeAll
				print "\t6. ",planUpload
			elif regConcProg:
				print "\t5. ",planRegConcProg

		else:
			if installedVersion < latestVersion:
				print planBkpPkg
				print planCreatePkg
				if analyzeSingle:
					print "\t5. ",planAnalyzeSingle
					print "\t6. ",planUpload
				elif analyzeAll:
					print "\t5. ",planAnalyzeAll
					print "\t6. ",planUpload
				elif regConcProg:
					print "\t5. ",planRegConcProg

			elif installedVersion == latestVersion:
				if analyzeSingle:
					print "\t3. ",planAnalyzeSingle
					print "\t4. ",planUpload
				elif analyzeAll:
					print "\t3. ",planAnalyzeAll
					print "\t4. ",planUpload
				elif regConcProg:
					sys.stdout.write("\033[F\033[F") # Move to Previously printed line
					sys.stdout.write("\033[K") # Delete that line (2. sqlplus apps)
					print "\t2. ",planRegConcProg
				
	else:
		print planCreatePkg
		if analyzeSingle:
			print "\t5. ",planAnalyzeSingle
			print "\t6. ",planUpload
		elif analyzeAll:
			print "\t5. ",planAnalyzeAll
			print "\t6. ",planUpload
		elif regConcProg:
			print "\t5. ",planRegConcProg


	print '''
	  ESTIMATE TIME
	  ##############
	   
	  WINDOW : SERVICE
	  TIME   : 1.5 Hours

	'''
