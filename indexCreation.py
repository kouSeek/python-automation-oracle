#+=================================================================================+
# |Author : Koushik Chakraborty
# |Creation date : 28-Sept-2016
# |Modified On : 7-Nov-2016
# |Version : 1.0
# |Catagory : MT
# |DESCRIPTION 
# |   used to prepare plan for Create Index
# |PLATFORM      
# |   Linux 
#+=================================================================================+

###########################################################
# Index creation
############################################################

import re, sys
from subprocess import Popen, PIPE

def runSqlAsSys(sqlCommand):
	session = Popen(['sqlplus', '-S', "/ as sysdba"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
	session.stdin.write(sqlCommand)
	return session.communicate()[0]

def getShellOut(cmd):
	session = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	return session.communicate()[0]

def getMode():
	global mode
	print '''
	Available Options:

	   1. Enter full Create Index statement
	   2. Enter index names, table names, column names etc. separately
	'''
	mode = raw_input("Please enter your choice(1/2) : ")
	if mode != '1' and mode != '2':
		print "Invalid Option. Enter a valid option\n";
		getMode()

def start():
	if mode == '1':
		loopStatements()
	elif mode == '2':
		loopParameters()


#######  functions for mode 1
def loopStatements():
	global count
	while True:
		print "\n\n-------------------\nEnter the Full create INDEX statement(in below mentioned format - table OWNER should be given):"
		print "  Format features --> case INsensitive; multiple spaces between words is allowed; Don't put quotes around column names.."
		print "Example:  create index owner.index on owner.table(column1, cloumn2, ...) .... \n"
		input0 = raw_input("Enter the create INDEX statement/ Press enter to skip :\n")
		if input0 == "":
			break
		else:
			indexStatement.append(input0)
			if indexStatement[count].strip()[-1:] == ";":
				indexStatement[count] = indexStatement[count].strip()[:-1]
			loadIndexData()
			validateInputs()
			count += 1

def loadIndexData():
	searchPattern = "create +index +(\w+)\.([\w$]+) +on +(\w+)\.([\w$]+) *\(([\w,\s]+)\)"
	try:
		indexOwner.append( re.search(searchPattern, indexStatement[count], flags=re.IGNORECASE).group(1).upper() )
		indexName.append(  re.search(searchPattern, indexStatement[count], flags=re.IGNORECASE).group(2).upper() )
		tableOwner.append( re.search(searchPattern, indexStatement[count], flags=re.IGNORECASE).group(3).upper() )
		tableName.append( re.search(searchPattern, indexStatement[count], flags=re.IGNORECASE).group(4).upper() )
		columnNamesCSV.append( re.search(searchPattern, indexStatement[count], flags=re.IGNORECASE).group(5).upper() )
		columnNamesQuotedCSV.append( "'" + "\',\'".join(i.strip() for i in columnNamesCSV[count].split(',')) + "'" )
		# en-quote each column names and trim whitespaces
	except:
		print "\t~~~~~ Create Index statement was not given in proper format... Please enter again\n"
		loopStatements()


#######  functions for mode 2
def loopParameters():
	global count
	while True:
		print "\n\nEnter all the parameters individualy :\n"
		input0 = raw_input("Enter the INDEX owner / or press enter to get the Action Plan : ").upper()
		if input0 == "":
			break
		indexOwner.append(input0)
		indexName.append( raw_input("Enter the INDEX name : ").upper() )
		tableOwner.append( raw_input("Enter the TABLE owner : ").upper() )
		tableName.append( raw_input("Enter the TABLE name : ").upper() )
		columnNamesCSV.append( raw_input("Enter the column names separated by comma(without quotes) : ").upper() )
		columnNamesQuotedCSV.append( "'" + "\',\'".join(i.strip() for i in columnNamesCSV[count].split(',')) + "'"  )

		indexStatement.append("create index " + indexOwner[count] + "." + indexName[count] + " on " + \
		    tableOwner[count] + "." + tableName[count] + "(" + columnNamesCSV[count]+")" )

		validateInputs()
		count += 1



######
def validateInputs():
	global count
	indexNameFree = runSqlAsSys("set feedback off Heading off\nselect index_name from dba_indexes where index_name = '" + indexName[count] + "';") == ""
	tableNameExists = runSqlAsSys("set feedback off Heading off\nselect table_name from dba_tables where table_name = '" + tableName[count] + "' and owner = '" + tableOwner[count] + "';") != ""
	columnNamesExist = ( int(runSqlAsSys("set feedback off Heading off\nselect count(*) from dba_tab_cols where COLUMN_NAME in ("+columnNamesQuotedCSV[count]+") and TABLE_NAME = '"+tableName[count]+"';")) == len(columnNamesCSV[count].split(',')) )

	#### check if there is any index existing on the same table with the same combination of columns
	indexCreatable = True
	existingIndexes = runSqlAsSys("set feedback off Heading off\nselect index_name from user_indexes where table_name = '"+tableName[count]+"';").splitlines()

	columnMatchCount = 0
	inputColumnNamesArray = map(lambda x: x.strip(), columnNamesCSV[count].split(','))
	for i in existingIndexes:
		columnsOfExistingIndex = runSqlAsSys("set feedback off Heading off\nselect column_name from dba_ind_columns where index_name = '"+ i +"';").splitlines()
		for j in columnsOfExistingIndex:
			if j in inputColumnNamesArray:
				columnMatchCount +=1
		if columnMatchCount == len(inputColumnNamesArray) and len(columnsOfExistingIndex) == len(inputColumnNamesArray):
			indexCreatable = False
			break


	#### check if any parameters are null
	paramaterNull = (indexName[count] == '' or tableOwner[count] == '' or tableName[count] == '' or columnNamesCSV[count] == '' )

	if not indexNameFree:
		print "\n~~~~~Index name already exists. Please enter correct input.~~~~~~\n"
	if not tableNameExists:
		print "\n~~~~~The table name doesn't exist under the given Owner. Please enter correct input.~~~~~~\n"
	if paramaterNull:
		print "\n~~~~~Some parameters are given Null. Please enter correct input.~~~~~~\n"
	if not columnNamesExist:
		print "\n~~~~~The given column names are not correct. Please enter correct column names again.~~~~~~\n"
	if not indexCreatable:
		print "\n~~~~~There already exists an index on the same table with the same combination of columns. So this index can not be created.~~~~~~\n"

	if not indexNameFree or not tableNameExists or paramaterNull or not columnNamesExist or not indexCreatable:
		indexStatement.pop()
		indexOwner.pop()
		indexName.pop()
		tableOwner.pop()
		tableName.pop()
		columnNamesCSV.pop()
		columnNamesQuotedCSV.pop()
		start()


def printFindings():
	print '''
Findings
##############

	'''
	print "## Instance Details:"
	print runSqlAsSys("show user;\nselect name, created from v$database;\nselect release_name from apps.fnd_product_groups;")

	print "\t## Details of given tables:"
	print '''
SQL> col OBJECT_NAME for a30
SQL> col OBJECT_TYPE for a15
SQL> col OWNER for a10
SQL> select OBJECT_NAME,OWNER from dba_objects where OBJECT_TYPE = 'TABLE' and OBJECT_NAME in (\'''' + "','".join(tableName) + "');"
	print runSqlAsSys("col OBJECT_NAME for a30\ncol OBJECT_TYPE for a15\ncol OWNER for a10\nselect OBJECT_NAME,OWNER from\
	 dba_objects where OBJECT_TYPE = 'TABLE' and OBJECT_NAME in ('" + "','".join(tableName) + "');")

	print "\t## Size of given tables:\n"
	print "SQL> select segment_name, sum(BYTES)/1024/1024 MB from dba_segments where segment_name in ('" + "','".join(tableName) + "') group by segment_name;"
	print runSqlAsSys("col segment_name for a30\nselect segment_name, sum(BYTES)/1024/1024 MB from dba_segments where segment_name in ('" + "','".join(tableName) + "') group by segment_name;")


	for i in range(len(indexStatement)):
		print "SQL> select INDEX_NAME,TABLE_NAME,COLUMN_NAME from dba_ind_columns where COLUMN_NAME in \
(" + columnNamesQuotedCSV[i] + ") and TABLE_NAME = '" + tableName[i] + "';" 
		print runSqlAsSys("set lines 200\ncol INDEX_NAME for a35\ncol TABLE_NAME for a30\ncol COLUMN_NAME for a20\n\
		select INDEX_NAME,COLUMN_NAME,TABLE_NAME from dba_ind_columns where COLUMN_NAME in (" + columnNamesQuotedCSV[i] + ") and TABLE_NAME = '" + tableName[i] + "';" )

		print "SQL> explain plan for " + indexStatement[i] + ";"
		print "SQL> @$ORACLE_HOME/rdbms/admin/utlxplp"
		print runSqlAsSys("explain plan for " + indexStatement[i] + ";\nset linesize 250\n@$ORACLE_HOME/rdbms/admin/utlxplp")



##### __main__

currentUser = getShellOut("whoami")
if currentUser[:2] != "or":
	print "Please login to DB node and run this automation as 'or' user... "
	sys.exit()

count = 0
 # Dynamic array allocation
indexStatement = []
indexOwner = []
indexName = []
tableOwner = []
tableName = []
columnNamesCSV = []
columnNamesQuotedCSV = []

getMode()
start()

if len(indexStatement) == 0:
	print "No valid Indexes found."
	sys.exit()

printFindings()

############################
# Print Action Plan
print '''\n\n
FINAL ACTION PLAN
###################

1) Take backup of invalids

2) Login to DB Node as sys user

3) Run below statements for Creating Indexes:
'''
for i in indexStatement:
	print i, "nologging parallel;\n"

print "\n4) Run below:\n"
for i in range(len(indexStatement)):
	print "alter index " + indexOwner[i] + '.' + indexName[i] + " logging noparallel;\n"

print '''
5) Check and compile new invalids

6) Verification :

set lines 130
col INDEX_NAME for a40
col TABLE_NAME for a45
col COLUMN_NAME for a45
Select INDEX_NAME,TABLE_NAME,COLUMN_NAME from dba_ind_columns where INDEX_NAME in (\'''' + "','".join(indexName) + '''\');
\n
	WINDOW
	########

	WINDOW TYPE : Service Window
	PERIOD      : < Hours >

<< Please use the timing information from explain plan >>

'''
