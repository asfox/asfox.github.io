#!/apps/linux/bin/python
"""loni2condor.py
  Author:     Andrew S. Fox <asfox@wisc.edu>
  Program:    LONI Pipeline XML to Condor Files.
  Date:       June 2005

  Description:  This program simply reads a LONI Pipeline XML
                Module and translates it into the files needed
                to submit a Condor DAG.

  Resources:    Condor: http://www.cs.wisc.edu/condor
                LONI Pipeline: http://www.loni.ucla.edu/Software/
"""
__author__ = 'Andrew S. Fox'


import sys
from optparse import OptionParser
import xml.dom.minidom
import re
import os


class LONIFile:
    """ A File/Variable that is used by a LONI Pipeline Module

    """
    def __init__(self, inOutText ):
        """Create a new LONI File, and set it to either an input or output file.
        
        Arguments:
        inOutText -- either INFILE or OUTFILE
        
        Variables:
        PARENT_INPUT -- LONI Modules using this LONI File as an input.
        PARENT_OUTPUT -- LONI Modules using this LONI File as an output.
        fileList -- The list of files represented by this LONI File.
        needsParsing -- '1' if this LONI File requires some parsing, '0' if not.
        PARAMS -- A dict that contains XML parameters of the LONI File; all parameters are set to their defaults.

        """
        if( inOutText == 'INFILE' ):
            self.isInput  = 1;
            self.isOutput = 0;
        if( inOutText == 'OUTFILE' ):
            self.isInput  = 0;
            self.isOutput = 1;
        self.PARENT_INPUT = [];
        self.PARENT_OUTPUT = [];
        self.fileList = [];
        self.needsParsing = 0;
        self.PARAMS = {'DESCRIPTION':"",
            'INDEX':"",
            'TYPE':"",
            'CHECK':"true",
            'SYNOPSIS':"",
            'EXTENDER':"",
            'READFROM':"",
            'FILENAME':"",
            'GROUPED':"",
            'EXTENDABLE':"false",
            'EXPORTABLE':"false",
            'ISOPTIONAL':"false",
            'OVERWRITING':"true" }
    def set_attribute( self, attrib, value ):
        """Set a parameter (attrib) to a given value (value).
        
        Arguments:
        attrib -- The name of the XML Parameter to be set.
        value -- The value to set the XML Parameter to.

        """
        self.PARAMS[attrib] = value;
    def add_input( self, parent ):
        """Set the input parent.

        Arguments:
        parent -- The parent LONI Module that uses this LONI File as input.

        """
        self.PARENT_INPUT.append( parent );
    def add_output( self, parent ):
        """Set the output parent.

        Arguments:
        parent -- The parent LONI Module that uses this LONI File as output.

        """
        self.PARENT_OUTPUT.append( parent );
    def checkFilePermissions( self ):
        """Check the File Permissions
        
        Notes: This function does not currently work properly... it produces many false positives.

        """
        if( self.PARAMS['CHECK'].lower() == 'true' ):
            if( self.PARAMS['TYPE'].lower() == 'file' ):
                errorCode = 0;
                if( (self.PARAMS['READFROM'] == '') & (self.isInput == 1) ):
                    for file in self.fileList:
                        if( os.access(file, os.R_OK ) != True ):
                            print "Error: Can't read from "+file
                            errorCode = 1;
                else:
                    for file in self.fileList:
                        if( os.access( file, os.F_OK ) == True ):
                            if( self.PARAMS['OVERWRITING'].lower() != "true" ):
                                print "Error: "+file+" already exists.";
                                errorCode = 2;
                            else:
                                if( os.access( file, os.W_OK ) != True ):
                                    print "Error: Can't write to "+file
                                    errorCode = 1;
                        else:
                            file_dir = re.search( r'(\S*)[\\|/]\S+s*$', file );
                            file_dir = file_dir.group(1);
                            if( os.access( file_dir, os.W_OK ) != True ):
                                print "Error: Can't create files in "+file_dir
                                errorCode = 1; 
    
                if( errorCode == 1 ):
                    print "\nThe Condor files will be created, but you will need to fix this before execution. \n";
                elif( errorCode == 2 ):
                    print "The Condor files will be created, but this is a serious error and you MUST fix this before execution or risk destroying data."
            

class LONIModule:
    """A LONI Module that represents a commandline argument.

    """
    def __init__(self, cmd_num):
        """Create a new LONI Module, and give it a command number.

        Arguments:
        cmd_num -- Useless?

        Variables: 
        NUMBER -- Useless?
        PARAMS -- A dict that contains XML parameters of the LONI Module; all parameters are set to nothing.
        INFILE -- An array of LONI Files used as input.
        OUTFILE -- An array of LONI Files used as output.
        CHILD -- An array of Modules that depend on this Module.
        PARENT -- An array of Modules that this Module depends on.
        
        """
        self.NUMBER = cmd_num;
        self.PARAMS = {'NAME':"",
            'LOCATION':"", 
            'COMMAND':"",
            'HELPFILE':"",
            'STDIN':"",
            'STDOUT':"",
            'X':"",
            'Y':"" }
        self.INFILE = []
        self.OUTFILE = []
        self.CHILD = []
        self.PARENT = ''
    def set_attribute(self, attrib, value):
        """Set a parameter (attrib) to a given value (value).
        
        Arguments:
        attrib -- The name of the XML Parameter to be set.
        value -- The value to set the XML Parameter to.

        """
        self.PARAMS[attrib] = value;    
    def add_infile( self, cFile):
        """Add an input LONI File to the Module.

        Arguments:
        cFile -- The LONI File that the Module uses as input.

        """
        while( int(cFile.PARAMS['INDEX']) >= len( self.INFILE ) ):
            self.INFILE.append( '' );
        self.INFILE[int(cFile.PARAMS['INDEX'])] = cFile;
    def add_outfile( self, cFile):
        """Add an output LONI File to the Module.

        Arguments:
        cFile -- The LONI File that the Module uses as output.

        """
        while( int(cFile.PARAMS['INDEX']) >= len( self.OUTFILE ) ):
            self.OUTFILE.append( '' );
        self.OUTFILE[int(cFile.PARAMS['INDEX'])] = cFile;
    def add_child( self, myChild ):
        """Add a child LONI Module to the Module.

        Arguments:
        myChild -- The LONI Module that depends on the current Module.

        """
        self.CHILD.append( myChild )
        myChild.add_parent( self );
    def add_parent( self, myParent ):
        """Add a parent LONI Module to the Module.

        Arguments:
        myChild -- The LONI Module that the current Module depends on.

        """
        self.PARENT = myParent;
    def numInFiles(self):
        """Return the number of Input Files.

        """
        return len(self.INFILE);

class LONIXML(LONIModule):
    """A LONI XML Pipeline.

    """
    def __init__(self):
        """Create a new LONI XML Pipeline.

        Variables:
        numExecutions -- The nubmer of times a module will execute; starts at zero.

        """
        LONIModule.__init__(self, 0)
        self.numExecutions = 0;
    def setNodeAttributes( self, node, parentName ):
        """Set the attributes of an XML node to the Module.

        Arguments:
        node -- The XML Node containing the target attributes.
        parentName -- The name of the Parent LONI Module.
        
        """
        attrNum = 0;
        while( attrNum < node.attributes.length ):
            if( node.attributes.item(attrNum).nodeName.upper() == 'NAME' ):
                node.name = ''.join( [parentName, "/", node.attributes.item(attrNum).nodeValue ])
                self.set_attribute( node.attributes.item(attrNum).nodeName.upper(), node.name )
            else:
                self.set_attribute( node.attributes.item(attrNum).nodeName.upper(), node.attributes.item(attrNum).nodeValue )
            attrNum = attrNum+1;
    def traverse( self, topnode, parentModule):
        """Traverse the current LONI Module and explore its children, 
           converting each XML Node into a LONI Module or LONI File.

        Arguments:
        topnode -- The top XML Node to be traversed.
        parentModule -- The parent LONI Module that this Module depends on.

        """
        if( parentModule == '' ):   
            parentName = '';
        else:
            parentName = parentModule.PARAMS['NAME'];
        self.setNodeAttributes( topnode, parentName );
        i = 0;
        while( len(topnode.childNodes) > i):
            node = topnode.childNodes[i];
            if( node.nodeName == "Module" ):
                newModule = LONIXML();
                newModule.traverse( node, self );
                self.add_child( newModule );
            elif node.nodeName == 'InFile':
                self.traverseInFile(node, self.PARAMS['NAME'])
            elif node.nodeName == 'OutFile':
                self.traverseOutFile(node, self.PARAMS['NAME'])
            elif node.nodeName != "#text":
                "THERE MAY BE AN ERROR IN YOUR LONI XML FILE..."
                "\tLONI XML does not account for", node.nodeName
            i = i+1;

    def traverseInFile(self, node, parentName):
        """Converts an InFile XML Node into a LONI File

        Arguments:
        node -- The XML Node to be converted.
        parentName -- The name of the parent LONI Module.

        """
        item = LONIFile('INFILE')
        item.add_input(  self );
        attrNum=0;
        while( attrNum < node.attributes.length ):
            item.set_attribute( node.attributes.item(attrNum).nodeName.upper(), node.attributes.item(attrNum).nodeValue )
            attrNum = attrNum+1;        
        self.add_infile( item )

    def traverseOutFile(self, node, parentName):
        """Converts an OutFile XML Node into a LONI File

        Arguments:
        node -- The XML Node to be converted.
        parentName -- The name of the parent LONI Module.

        """
        item = LONIFile('OUTFILE')
        item.add_output( self );
        attrNum=0;
        while( attrNum < node.attributes.length ):
            item.set_attribute( node.attributes.item(attrNum).nodeName.upper(), node.attributes.item(attrNum).nodeValue )
            attrNum = attrNum+1;
        self.add_outfile( item )

    def getModuleByName(self, name):
        """Traverse the each Module and it's children and return the Module named 'name'.

        Arguments:
        name -- The name of the Module to return.

        """
        returnValue=-1;
        if( name == self.PARAMS['NAME'] ):
            if( self.PARAMS['NAME'] != name ):
                self.fixReadFromVar( myName, name ); 
            name = self.PARAMS['NAME'];
            returnValue = self;
            return returnValue;
        if( hasattr( self, 'CHILD' ) ):
            i=0;
            while( i < len(self.CHILD) ):
                found = self.CHILD[i].getModuleByName( name )
                if( found != -1 ):
                    returnValue = found;
                    return returnValue;
                i=i+1;
        return returnValue;

    def getModuleByPartialReadFromName( self, curFile ):
        """Traverse each Module and it's children and return the Module that the current file uses as input.

        Variables:
        curFile -- The current file whos input Module should be identified.

        """
        returnValue=-1;
        name = curFile.PARAMS['READFROM']
        if( name != '' ):
            myName = re.sub(r'(?P<badChar>[\.\*\+\?\\\(\)\[\]\{\}\|\$\^])', r'\\\g<badChar>', name );
            searchString = '.*?'+myName+'+\s*$'
            if( re.match( searchString, self.PARAMS['NAME'] ) ):
                curFile.PARAMS['READFROM'] = self.PARAMS['NAME']; 
                returnValue = self;
                return returnValue;
            if( hasattr( self, 'CHILD' ) ):
                i=0;
                while( i < len(self.CHILD) ):
                    found = self.CHILD[i].getModuleByPartialReadFromName( curFile )
                    if( found != -1 ):
                        returnValue = found;
                        return returnValue;
                    i=i+1;
        return returnValue;

    def completeInFiles(self, topModule):
        """Parse the filenames that need to be parsed.

        Description:
        Since some input filenames are defined based on the output of other files,
        the Pipeline must be parsed and flushed out.

        Arguments:
        topModule -- The top module of the pipeline to be parsed.

        Note:
        This does not appropriately deal with grouping yet.

        """
        if( hasattr( self, 'INFILE' ) ):
            inFileNum = 0;
            isList = re.compile( r'\.list$' );
            checkIfFileNeedsParsing = re.compile( r'[\+|\-]|\$\{.+\}' );
            while( inFileNum < len(self.INFILE) ):
                if( self.INFILE[inFileNum] != '' ):
                    curFile = self.INFILE[inFileNum]
                    if( isList.search( curFile.PARAMS['FILENAME'] ) != None ):
                        if( curFile.PARAMS['GROUPED'] != 'true' ):
                            curFile.fileList = ReadListOfFiles( curFile.PARAMS['FILENAME'] );
                            curFile.PARENT_INPUT[0].numExecutions = len(curFile.fileList)
                            needsParsing = 0;
                        else:
                            curFile.fileList[0] = curFile.PARAMS['FILENAME'];
                            needsParsing = 0;
                    # check to see if readfrom is needed...
                    checkReadFrom = re.compile(r'^-OutFile')
                    if( checkReadFrom.search(curFile.PARAMS['FILENAME']) ):
                        inputModule = ''.join( ['/', curFile.PARAMS['READFROM']] )
                        parentModule = topModule.getModuleByName( inputModule )
                        if( parentModule == -1 ):
                            parentModule = topModule.getModuleByPartialReadFromName( curFile )
                        curFile.add_output( parentModule );
                    if( curFile.fileList == [] ):
                        # Parse the file list...
                        if( checkIfFileNeedsParsing.search( curFile.PARAMS['FILENAME']) == None ):
                            curFile.fileList.append( curFile.PARAMS['FILENAME'] );
                            curFile.needsParsing = 0;
                        else:
                            curFile.fileList.append( curFile.PARAMS['FILENAME'] );
                            curFile.needsParsing = 1;
                    del(curFile)
                inFileNum = inFileNum+1;
        if( hasattr(self, 'OUTFILE' )):
            outFileNum = 0;
            while( outFileNum < len(self.OUTFILE)):
                if( self.OUTFILE[outFileNum] != '' ):
                    curFile = self.OUTFILE[outFileNum]
                    if( isList.search( curFile.PARAMS['FILENAME'] ) != None ):
                        curFile.fileList = ReadListOfFiles(curFile.PARAMS['FILENAME']);
                        self.numExecutions = len(curFile.fileList)
                        needsParsing = 0;
                    if( curFile.fileList == [] ):
                        if( checkIfFileNeedsParsing.search( curFile.PARAMS['FILENAME']) == None ):
                            curFile.fileList.append( curFile.PARAMS['FILENAME'] );
                            curFile.PARENT_INPUT[0].numExecutions = len(curFile.fileList)
                            curFile.needsParsing = 0;
                        else:
                            curFile.fileList.append( curFile.PARAMS['FILENAME'] );
                            curFile.needsParsing = 1;
                    del( curFile )
                outFileNum=outFileNum+1;
        if( hasattr( self, 'CHILD' ) ):
            childNum = 0;
            while( childNum < len(self.CHILD )):
                self.CHILD[childNum].completeInFiles(topModule)
                childNum = childNum+1;

    def parseLONIRegEx( self,curFile, parentFile, eachVar ):
        """Parse LONI's filenaming scheme.

        Arguments:
        parentFile -- The File that this file reads from and depends on.
        eachVar -- The variable to parse, i.e. ${1:b},  etc.

        """
        parseWholePath = re.compile(r'^(?P<d>\S*(?=[\/\\]))[\\\/]?(?P<b>[^\s\\\/]+(?=[\.|\s*$]))\.?(?P<e>(?<=\.)\S*)\s*$' );
        parseFileNamePath = re.compile(r'^[\\\/]?(?P<b>[^\s\.\\\/]+(?=[\.|\s*$]))\.?(?P<e>(?<=\.)\S*)\s*$' );
        parseRootPath = re.compile(r'^(?P<d>\S*(?=[\/\\]))[\\\/]?(?P<b>[^\s\\\/]+(?=[\.|\s*$]))\.?\s*$' );
        parseDirPath = re.compile(r'^(?P<d>\S*(?=[\/\\]))[\\\/]?\s*$' );
        parseExtentionPath = re.compile(r'^(?P<e>(?<=\.)\S*)\s*$' );
        parseBasePath = re.compile(r'^[\\\/]?(?P<b>[^\s\\\/]+(?=[\.|\s*$]))\.?\s*$' );
        fileNum = 0;
        while( fileNum < len(parentFile.fileList) ):
            thisMatch = ''.join( ['\$\{', eachVar.group('parent') ])
            # Insert the replacement text... rather than ${1:b} etc.
            curPath = parseWholePath.search( parentFile.fileList[fileNum] )
            if( curPath == None ):
                curPath = parseFileNamePath.search( parentFile.fileList[fileNum] );
                if( curPath == None ):
                    curPath = parseRootPath.search( parentFile.fileList[fileNum] );
                    if( curPath == None ):
                        curPath = parseBasePath.search( parentFile.fileList[fileNum] );
                        if( curPath == None ):
                            curPath = parseDirPath.search( parentFile.fileList[fileNum] );
                            if( curPath == None ):
                                curPath = parseExtentionPath.search( parentFile.fileList[fileNum] );
                                if( curPath == None ):
                                    print "Error looking for variable that isn't there...", parentFile.fileList[fileNum]
                                else: 
                                    curPath = curPath.groupdict() ;
                                    curPath['b']='';
                                    curPath['d']='';
                            else: 
                                curPath = curPath.groupdict() ;
                                curPath['b']='';
                                curPath['e']='';
                        else: 
                            curPath = curPath.groupdict() ;
                            curPath['d']='';
                            curPath['e']='';
                    else: 
                        curPath = curPath.groupdict() ;
                        curPath['e']='';
                else: 
                    curPath = curPath.groupdict() ;
                    curPath['d']='';
            else: 
                curPath = curPath.groupdict() ;

            if( eachVar.group('filepart') == 'b' ):
                curPath = curPath['b'];
                thisMatch = ''.join([thisMatch, '\:', eachVar.group('filepart')])
            elif( eachVar.group('filepart') == 'f' ):
                curPath = ''.join((curPath['b'],'.', curPath['e']))
                thisMatch = ''.join([thisMatch, '\:', eachVar.group('filepart')])
            elif( eachVar.group('filepart') == 'd' ):
                curPath = ''.join([curPath['d'], '/']);
                thisMatch = ''.join([thisMatch, '\:', eachVar.group('filepart')])
            elif( eachVar.group('filepart') == 'r' ):
                curPath = ''.join((curPath['d'],'/', curPath['b']))
                thisMatch = ''.join([thisMatch, '\:', eachVar.group('filepart')])
            elif( eachVar.group('filepart') == 'e' ):
                curPath = ''.join(['.', curPath['e']]);
                thisMatch = ''.join([thisMatch, '\:', eachVar.group('filepart')])
            else:
                curPath = parentFile.fileList[fileNum];
            thisMatch = ''.join([thisMatch, '\}'])
            curFile.fileList[fileNum] = re.sub( thisMatch, curPath, curFile.fileList[fileNum] );
            del(thisMatch);
            del(curPath);
            fileNum = fileNum+1;

    def parseLONICombineStrings( self, curFile ):
        """Correctly concatanate and subtract from strings.
        
        Arguments:
        curFile -- The LONI File to parse.

        """
        individuallyParse = re.compile( r'(.*?)\s+(\+|\-)\s+(.*)' )
        getNextPart = re.compile( r'^\s*(\S+)(\s*.*)$' )
        removeSpecialChars = re.compile( r'(?P<n>\\|\{|\}|\(|\)|\+|\?|\||\^|\.|\$)' )

        fileNum = 0;
        while( fileNum < len(curFile.fileList) ):
            eachPart = individuallyParse.search( curFile.fileList[fileNum] );
            while( eachPart != None ):
                wantedPath = '';
                if( eachPart.group(2) == '+' ):
                    wantedPath = ''.join([eachPart.group(1), eachPart.group(3)]);
                elif( eachPart.group(2) == '-' ):
                    nextPart = getNextPart.search( eachPart.group(3) )
                    replacedSpecialChars = removeSpecialChars.sub( '\\\\\g<n>', nextPart.group(1) )
                    stripEnd = re.compile( ''.join([ replacedSpecialChars ]) )
                    wantedPath = stripEnd.sub( '', eachPart.group(1) );
                    wantedPath = ''.join([wantedPath, nextPart.group(2)]);
                else:
                    print "Maybe I shouldn't be here... \t<-----\n"
                    wantedPath = curFile.fileList[fileNum];
                curFile.fileList[fileNum] = wantedPath;
                eachPart = individuallyParse.search( curFile.fileList[fileNum] );
            fileNum = fileNum+1;

    def completeParse( self, topModule ):
        """Parse a pipeline and make sure that all filenames are filled in.

        Arguments:
        topModule -- The top module to be parsed.


        """
        checkForVar = re.compile(r'\$\{(?P<parent>\d+)\:?(?P<filepart>[fdrbe]?)\}', re.IGNORECASE );
    
        if( hasattr( self, 'INFILE' ) ):
            inFileNum = 0;
            while( inFileNum < len(self.INFILE) ):
                if( self.INFILE[inFileNum] != '' ):
                    curFile = self.INFILE[inFileNum];
                    if( curFile.needsParsing == 1 ):
                        for eachVar in checkForVar.finditer( curFile.PARAMS['FILENAME'] ) :
                            parentModule = topModule.getModuleByName( curFile.PARAMS['READFROM'] )
                            if( parentModule == -1 ):
                                parentModule = topModule.getModuleByPartialReadFromName( curFile )
                                if( parentModule == -1 ):
                                    parentModule = self;
                            parentFile = parentModule.INFILE[int(eachVar.group('parent'))] ;
                            if( parentFile.needsParsing == 1 ):
                                parentFile.PARENT_INPUT[0].completeParse( topModule );
                            if( len(curFile.fileList) != len(parentFile.fileList) ):
                                if( len(curFile.fileList) == 1 ):
                                    i=1;
                                    while( i < len(parentFile.fileList) ):
                                        curFile.fileList.append( curFile.fileList[0] );
                                        i=i+1;
                                    curFile.PARENT_INPUT[0].numExecutions = len(curFile.fileList)
                                elif( len(parentFile.fileList) == 1 ):    
                                    i=1;
                                    # print "Make curFile.fileList as large as parentFile.fileList"
                                    # THE ABOVE PRINT STATEMENT IS WRONG. I SHOULD NOT.
                            self.parseLONIRegEx( curFile, parentFile, eachVar )
                            del(parentFile);
                            del(parentModule);
                        findOutFile = re.compile( r'\-OutFile(?P<parentIndex>\d+)' );
                        for eachOutFile in findOutFile.finditer( curFile.PARAMS['FILENAME'] ):
                            parentModule = topModule.getModuleByName(''.join(['/', curFile.PARAMS['READFROM']]))
                            if( parentModule == -1 ):
                                parentModule = topModule.getModuleByPartialReadFromName( curFile )
                                if( parentModule == -1 ):
                                    print "\nERROR:"
                                    print "    The module \"", curFile.PARAMS['READFROM'], "\" does not exist."
                                    print "    This may be due to a pipeline within a pipeline that is not specified as such in the xml file..."
                                    print "    Drew should fix this sometime.\n"
                                    sys.exit()
                            parentFile = parentModule.OUTFILE[int(eachOutFile.group('parentIndex'))];

                            if( parentFile.needsParsing == 1 ):
                                parentModule.completeParse( topModule ); 
                            if( len(curFile.fileList) != len(parentFile.fileList) ):
                                if( len(curFile.fileList) == 1 ):
                                    i=1;
                                    while( i < len(parentFile.fileList) ):
                                        curFile.fileList.append( curFile.fileList[0] );
                                        i=i+1;
                                    curFile.PARENT_INPUT[0].numExecutions = len(curFile.fileList)
                                elif( len(parentFile.fileList) == 1 ):    
                                    print "Make curFile.fileList as large as parentFile.fileList"
                                    # THE ABOVE PRINT STATEMENT IS WRONG. I SHOULD NOT.
                            fileNum = 0;
                            while( fileNum < len(parentFile.fileList) ):
                                thisMatch = ''.join(['-OutFile',eachOutFile.group('parentIndex')])
                                curPath = parentFile.fileList[fileNum];
                                curFile.fileList[fileNum] = re.sub( thisMatch, curPath, curFile.fileList[fileNum] )
                                del(curPath)
                                del(thisMatch)
                                fileNum = fileNum+1;
                            del(parentFile)
                            del(parentModule)
                        self.parseLONICombineStrings( curFile )
                        curFile.needsParsing = 0;
                    del(curFile);
                inFileNum = inFileNum+1;
        if( hasattr( self, 'OUTFILE' ) ):
            outFileNum = 0;
            while( outFileNum < len(self.OUTFILE) ):
                if( self.OUTFILE[outFileNum] != '' ):
                    curFile = self.OUTFILE[outFileNum];
                    if( curFile.needsParsing == 1 ):
                        for eachVar in checkForVar.finditer( curFile.PARAMS['FILENAME'] ) :
                            parentFile = self.INFILE[int(eachVar.group('parent'))] ;
                            if( parentFile.needsParsing == 1 ):
                                print "\t\t---- POTENTIAL ERROR ----\t\t";
                                parentFile.PARENT_INPUT[0].completeParse( topModule );
                            if( len(curFile.fileList) != len(parentFile.fileList) ):
                                if( len(curFile.fileList) == 1 ):
                                    i=1;
                                    while( i < len(parentFile.fileList) ):
                                        curFile.fileList.append( curFile.fileList[0] );
                                        i=i+1;
                                elif( len(parentFile.fileList) == 1 ):    
                                    print "Make curFile.fileList as large as parentFile.fileList"
                                    # THE ABOVE PRINT STATEMENT IS WRONG. I SHOULD NOT.
                            self.parseLONIRegEx( curFile, parentFile, eachVar )
                            del(parentFile);
                        self.parseLONICombineStrings( curFile )
                        curFile.needsParsing = 0;
                    del(curFile)
                outFileNum = outFileNum+1;
        if( hasattr( self, 'CHILD' ) ):
            childNum = 0;
            while( childNum < len(self.CHILD) ):
                self.CHILD[childNum].completeParse( topModule );
                childNum = childNum+1;


class CondorSubmitFile:
    """A Condor File that represents a LONI Module that can be submitted to Condor.

    """
    def __init__( self, dir, filename, curModule):
        """Create a new Condor Submit File and convert an existing LONI Parameter Module into 
            a Condor Submit File.

        Arguments:
        dir -- The directory to create the Condor Files in.
        filename -- The name of the submit file to create.
        curModule -- The module being represented.

        Note: This function assumes that this script assumes Condor is running in an environment with a shared filesystem, containing only linux machines.

        """
        self.parameters = {};
        self.dir = dir;
        self.filename = filename;
        self.description = ''.join(['No description provided for:', filename ]);

        self.addParam( 'universe', 'vanilla' );
        self.addParam( 'requirements', 'Memory > 10' );
        self.addParam( 'transfer_executable', 'False')
        self.addParam( 'output', ''.join( [dir, "condorFiles/", filename, ".output"]));
        self.addParam( 'error', ''.join( [dir, "condorFiles/", filename, ".error"]));
        self.addParam( 'log', ''.join([dir, "condorFiles/", filename, ".log"]));
        self.addParam( 'notification', 'never' );
        self.addParam( 'should_transfer_files', 'no' );
        self.addParam( 'initialdir', dir );
        self.addParam( 'getenv', 'True' );

        myExec = re.search(r'^\s?(?P<cmd>\S+(?=\s))(?P<args>.*)', curModule.PARAMS['COMMAND'])
        parseArgs = re.compile(r'-(?P<fileType>Out|In)File(?P<fileNum>\d+)');
        myArgs = ''
        for eachArg in parseArgs.finditer( myExec.group('args') ):
            myArgs = myArgs+'$('+eachArg.group('fileType')+'File'+chr(int(eachArg.group('fileNum'))+65)+') ' 
            
        self.addParam( 'Executable', myExec.group('cmd') )
        self.addParam( 'Arguments', myArgs )
        
    def addParam( self, paramName, param ):
        """Add a parameter to the Condor Submit File.

        Arguments:
        paramName -- The name of the parameter to define.
        param -- The value to be assigned to the parameter.

        """
        self.parameters[paramName] = param;

    def printSubmitFile( self ):
        """Prints a the Submit File.

        """
        submitFile = open(''.join([self.dir, 'condorFiles/', self.filename, '.submit']), 'w' )
        submitFile.write("################################\n");
        submitFile.write(''.join(["#", self.filename, "\n"]));
        submitFile.write(''.join([ "#    ", self.description, "\n"]));
        submitFile.write("################################\n");
        
        for paramName, param in self.parameters.iteritems(): 
            submitFile.write( paramName+" = "+param+"\n" )
        submitFile.write("queue");

        submitFile.close();
    
class CondorDag:
    """A Condor Directed Acyclic Graph (DAG) file that represents the dependencies between Modules.
    
    """
    def __init__( self, startDir ):
        """Create a new DAG File, in the start directory.

        Arguments:
        startDir -- The directory to start in.

        Variables:
        jobList -- The list of Jobs to run.
        dependencies -- The list of dependencies between the defined Jobs.
        varList -- The list of variables that are passed to the different submit files.
        submitFiles -- The submit files that need to be created.

        """
        
        self.jobList = [];
        self.dependencies = [];
        self.varList = {};
        self.submitFiles = [];
        self.dir = startDir;
    def write(self):
        """Write the DAG File.

        """
        if( os.access(self.dir, os.W_OK) != True ):
            print "Error: Can't write to "+self.dir
        if( os.access(''.join([self.dir,'condorFiles']), os.F_OK ) != True ):
            os.mkdir( ''.join([self.dir,'condorFiles']) )
        
        self.verifyAndCleanDag();

        dagFile = open( ''.join([self.dir, 'condorFiles/MASTER_CONDOR_SCRIPT.dag']), 'w' );
        for job in self.jobList :
            dagFile.write( job+"\n" );
        for dependency in self.dependencies:
            dagFile.write( dependency+"\n" );
        for moduleName, paramArray in self.varList.iteritems():
            if( paramArray != [] ):
                dagFile.write( "VARS "+moduleName+" ");
                dagFile.write( paramArray );
            dagFile.write( "\n" );
        dagFile.write("\n\nDOT "+self.dir+'condorFiles/visualGraph.dot' );
        dagFile.close();
        for submitFile in self.submitFiles:
            submitFile.printSubmitFile()
        
    def verifyAndCleanDag( self ):
        """Verify the DAG is appropriately constructed, and correct errors.

        """
        findParentChild = re.compile( r'^PARENT\s+(?P<parent>\S+)\s+CHILD\s+(?P<child>\S+)\s*$' );
        findJobName = re.compile(r'^JOB\s+(?P<name>\S+)\s+\S+\s*$');

        newDependencies = [];
        for dependency in self.dependencies:
            childFoundInJobList = 0;
            parentFoundInJobList = 0;
            myDependency = findParentChild.search( dependency );
            for job in self.jobList:
                job = findJobName.search( job );
                job = job.group('name')
                if( job == myDependency.group('child') ):
                    childFoundInJobList = 1;
                    if( parentFoundInJobList == 1 ):
                        break;
                if( job == myDependency.group('parent') ):
                    parentFoundInJobList = 1;
                    if( childFoundInJobList == 1 ):
                        break;
            if( childFoundInJobList != 1 ):
                for dependencyToFix in self.dependencies:
                    needsFixing = findParentChild.search( dependencyToFix );
                    if( needsFixing.group('parent') == myDependency.group('child') ):
                        newDependency = "PARENT "+myDependency.group('parent')+" CHILD "+needsFixing.group('child')
                        newDependencies.append(newDependency);
            if( parentFoundInJobList != 1 ):
                for dependencyToFix in self.dependencies:
                    needsFixing = findParentChild.search( dependencyToFix );
                    if( needsFixing.group('child') == myDependency.group('parent') ):
                        newDependency = "PARENT "+needsFixing.group('parent')+" CHILD "+myDependency.group('child')
                        newDependencies.append( newDependency );
            if( (parentFoundInJobList == 1) & (childFoundInJobList == 1) ):
                newDependencies.append( dependency );
        i=0;
        while( i < len(newDependencies)-1 ):
            j=i+1;
            while( j < len(newDependencies) ):
                if( newDependencies[i] == newDependencies[j] ):
                    newDependencies.remove( newDependencies[i] )
                    j=i+1;
                j=j+1;
            i=i+1;
        self.dependencies = newDependencies;
        
        newVars = {};
        for varName, paramArray in self.varList.iteritems():
            varFound = 0;
            for job in self.jobList:
                job = findJobName.search( job );
                job = job.group('name')
                if( job == varName ):
                    varFound = 1;
                    newVars[varName] = paramArray;
                    break;
            varName = '';
            paramArray = [];
        self.varList = newVars;
    
    def createCondorFromLoni(self, topModule ):
        """Convert a LONI Pipeline Module into a Condor DAG Module.

        Arguments:
        topModule -- The top module used to define the DAG.

        """
        getRidOfSpaces = re.compile( r' ' );
        removeStartingSlashes = re.compile( r'^[/|\\]' );
        getRidOfSlashes = re.compile( r'[/|\\]' );
        getRidOfParenthases = re.compile( r'[\(\)]' );

        i=0;
        while( i < len(topModule.CHILD) ):
            curModule = topModule.CHILD[i];
            submitFilename = curModule.PARAMS['NAME'].lower()
            submitFilename = getRidOfSpaces.sub( '_', submitFilename );
            submitFilename = removeStartingSlashes.sub( '', submitFilename );
            submitFilename = getRidOfSlashes.sub( '__', submitFilename );
            submitFilename = getRidOfParenthases.sub( '__', submitFilename );
            if( hasattr( curModule, 'CHILD' ) ):
                self.createCondorFromLoni( curModule )
            if( curModule.PARAMS['COMMAND'] != '' ):
                submitFile = CondorSubmitFile( self.dir, submitFilename, curModule )
                self.submitFiles.append( submitFile );
                j=0;
                while( j < curModule.numExecutions ):
                    job = ''.join(["JOB ", submitFilename, "_", str(j), " ", self.dir, 'condorFiles/', submitFilename, ".submit"] )
                    self.jobList.append( job )
                    j = j+1;

            if( hasattr( curModule, 'INFILE' ) ):
                numInFile = 0
                while( numInFile < len(curModule.INFILE) ):
                    if( curModule.INFILE[numInFile] != '' ):
                        self.convertLONIFile( submitFilename, 'inFile', curModule.INFILE[numInFile], curModule )
                    numInFile = numInFile + 1;
            if( hasattr( curModule, 'OUTFILE' ) ):
                numOutFile = 0
                while( numOutFile < len(curModule.OUTFILE) ):
                    if( curModule.OUTFILE[numOutFile] != '' ):
                        self.convertLONIFile( submitFilename, 'outFile', curModule.OUTFILE[numOutFile], curModule )
                    numOutFile = numOutFile + 1;
            i=i+1;

    def convertLONIFile(self, moduleName, inOut, myFile, curModule ):
        """ Convert a LONI FILE into a series of Condor jobs.

        Arguments:
        moduleName -- The name of the Job to run.
        inOut -- Either inFile or outFile.
        myFile -- The file to be converted.
        curModule -- The desired module that is the parent of the file.
        """
        # SHOULD MAKE SURE THAT FILES ARE READ/WRITEABLE... SHOULD ALSO READ OVERWRITE PARAMETER...
        getRidOfSpaces = re.compile( r' ' );
        removeStartingSlashes = re.compile( r'^[/|\\]' );
        getRidOfSlashes = re.compile( r'[/|\\]' );
        getRidOfParenthases = re.compile( r'[\(\)]' );
        
        if( myFile.PARAMS['CHECK'].lower() != "false" ):
            if( inOut == 'inFile' ):
                inOutText = 'In';
            elif( inOut == 'outFile' ):
                inOutText = 'Out';
            if( myFile.PARAMS['READFROM'] != '' ):
                j=0;
                while( j < myFile.PARENT_INPUT[0].numExecutions ):
                    parentFile = myFile.PARAMS['READFROM'].lower()
                    parentFile = getRidOfSpaces.sub( '_', parentFile );
                    parentFile = removeStartingSlashes.sub( '', parentFile );
                    parentFile = getRidOfSlashes.sub( '__', parentFile );
                    parentFile = getRidOfParenthases.sub( '__', parentFile );
                    
                    dependency = ''.join(["PARENT ", parentFile, "_", str(j), " CHILD ", moduleName, "_", str(j)])
                    self.dependencies.append( dependency )
                    j = j+1;
            if( myFile.fileList != '' ):
                myFile.checkFilePermissions()
                curVal = {}
                if( myFile.isInput == 1 ):
                    paramName = 'InFile';
                else:
                    paramName = 'OutFile';
                if( re.search(paramName+myFile.PARAMS['INDEX'], curModule.PARAMS['COMMAND']) ):
                    paramName = paramName+chr(int(myFile.PARAMS['INDEX']) + 65)
                    if( len(myFile.fileList) == 1 ):
                        if( myFile.isInput == 1 ):
                            numIter = myFile.PARENT_INPUT[0].numExecutions;
                        else:
                        # I added this after I got back... and it might be wrong.
                            numIter = myFile.PARENT_OUTPUT[0].numExecutions;
                        j=0;
                        while( j < numIter ):
                            curModuleName = moduleName+"_"+str(j)
                            if( self.varList.has_key(curModuleName) != True ):
                                self.varList[curModuleName] = '';
                            curVal = myFile.PARAMS['SYNOPSIS']+" "+myFile.fileList[0];
                            self.varList[curModuleName] = self.varList[curModuleName]+paramName+"=\""+curVal+"\" "
                            curVal = ''
                            j=j+1;
                    else:
                        j=0;
                        while( j < len(myFile.fileList) ):
                            curModuleName = moduleName+"_"+str(j)
                            if( self.varList.has_key(curModuleName) != True ):
                                self.varList[curModuleName] = '';
                            curVal = myFile.PARAMS['SYNOPSIS']+" "+myFile.fileList[j];
                            self.varList[curModuleName] = self.varList[curModuleName]+paramName+"=\""+curVal+"\" "
                            curVal = ''
                            j=j+1;
    
def ReadListOfFiles( filename ):
    """Read a list of files and return an array that contains the list.
    
    Arguments:
    filename -- The the path to the file you wish to read.

    Note:
    Any line beginning with a $ # or % is ignored.

    """
    tmp = [];
    isComment = re.compile( r'^[$|#|%]' );
    for line in open(filename):
        if( isComment.search(line) == None ):
            tmp.append( line.strip() );
    return tmp;
        

# Specify availible options.
parser = OptionParser();
parser.add_option( "-i", "--loniXML", "--xml", "--in", "--input", action="store", type="string", dest="i", help="The input LONI Pipeline XML File", metavar="FILENAME")
parser.add_option( "-o", "--out", "--condorDir", "--output", "--outDir", action="store", type="string", dest="o", help="The output directory where condor_files will be created.", metavar="DIR_NAME")
(options, args) = parser.parse_args();


# Ensure required positional arguments are used.
if( cmp(str(options.o),'None') & cmp(str(options.i),'None')  ):
    print "Reading from:", options.i
    print "Writing to:", options.o
else:
    print "Error: Incorrect Usage\n"

    print "Usage: loni2condor.py --input=FILENAME --output==DIR_NAME \n    -h, --help\n\tshow this help message and exit\n    -iFILENAME, --loniXML=FILENAME, --xml=FILENAME, --in=FILENAME, --input=FILENAME\n\t The input LONI Pipeline XML File\n    -oDIR_NAME, --out=DIR_NAME, --condorDir=DIR_NAME, --output=DIR_NAME, --outDir=DIR_NAME\n\t The output directory where condor_files will be created.\n";
    sys.exit();


xmlFile = xml.dom.minidom.parse( options.i )

node = xmlFile.firstChild
myPipeline = LONIXML();
myPipeline.traverse( node, '' )
myPipeline.completeInFiles(myPipeline);
myPipeline.completeParse(myPipeline);

myDag = CondorDag(options.o);
myDag.createCondorFromLoni( myPipeline )
myDag.write()



