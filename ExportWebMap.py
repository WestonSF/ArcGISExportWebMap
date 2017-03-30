#-------------------------------------------------------------
# Name:       Export Web Map
# Purpose:    Creates a map layout based of an MXD template and webmap input. Will create a seperate legend page
#             for maps with a number of layers.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    29/03/2017
# Last Updated:    30/03/2017
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcMap 10.3+
# Python Version:   2.7
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib

# Set global variables
# Logging
enableLogging = "false" # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...") and to print messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = "" # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
# Email logging
sendErrorEmail = "false"
emailServerName = "" # e.g. smtp.gmail.com
emailServerPort = 0 # e.g. 25
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
# Output
output = None
# ArcGIS desktop installed
arcgisDesktop = "true"

# If ArcGIS desktop installed
if (arcgisDesktop == "true"):
    # Import extra modules
    import arcpy
    # Enable data to be overwritten
    arcpy.env.overwriteOutput = True
# Python version check
if sys.version_info[0] >= 3:
    # Python 3.x
    import urllib.request as urllib2
else:
    # Python 2.x
    import urllib2
import uuid


# Start of main function
def mainFunction(webmapJSON,layoutTemplatesFolder,layoutTemplate,format,outputFile): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        # Get the requested map document
        templateMxd = os.path.join(layoutTemplatesFolder, layoutTemplate + '.mxd')

        # Convert the WebMap to a map document
        printMessage("Converting web map to a map document...","info")
        result = arcpy.mapping.ConvertWebMapToMapDocument(webmapJSON, templateMxd)
        mxd = result.mapDocument

        # Reference the data frame that contains the webmap
        # Note: ConvertWebMapToMapDocument renames the active dataframe in the template_mxd to "Webmap"
        df = arcpy.mapping.ListDataFrames(mxd, 'Webmap')[0]

        # If there is a legend element
        legendPDF = ""
        if (len(arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")) > 0):
            # Reference the legend in the map document
            legend = arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")[0]

            # Get a list of service layers that are on in the legend because the incoming
            # JSON can specify which service layers/sublayers are on/off in the legend
            legendServiceLayerNames = [lslyr.name for lslyr in legend.listLegendItemLayers()
                               if lslyr.isServiceLayer and not lslyr.isGroupLayer]

            # If legend is full for PDFs
            if ((legend.isOverflowing) and (format.lower() == "pdf")):
                printMessage("Legend is full, creating legend on new page...","info")

                # Create legend page
                legendPDF = createLegend(mxd)

                # Remove the legend by moving it off the page
                legend.elementPositionX = -5000
                legend.elementPositionY = -5000

                ### Custom code for WCC ###
                # Remove all graphic elements
                #for element in arcpy.mapping.ListLayoutElements(mxd, "GRAPHIC_ELEMENT"):
                #    # Remove the graphic by moving it off the page
                #    element.elementPositionX = -5000
                #    element.elementPositionY = -5000
                # Resize data frame element if needed by adding values - Height, width, X and Y
                #dataFrameElement = arcpy.mapping.ListLayoutElements(mxd, "DATAFRAME_ELEMENT")[0]
                #reSizeElement(mxd,"DATAFRAME_ELEMENT",dataFrameElement.elementHeight,mxd.pageSize.width-2,dataFrameElement.elementPositionX,dataFrameElement.elementPositionY)
        # No legend element
        #else:
            ### Custom code for WCC ###
            # Remove all graphic elements
            #for element in arcpy.mapping.ListLayoutElements(mxd, "GRAPHIC_ELEMENT"):
            #    # Remove the graphic by moving it off the page
            #    element.elementPositionX = -5000
            #    element.elementPositionY = -5000
            # Resize data frame element if needed by adding values - Height, width, X and Y
            #dataFrameElement = arcpy.mapping.ListLayoutElements(mxd, "DATAFRAME_ELEMENT")[0]
            #reSizeElement(mxd,"DATAFRAME_ELEMENT",dataFrameElement.elementHeight,mxd.pageSize.width-2,dataFrameElement.elementPositionX,dataFrameElement.elementPositionY)

        # Use the uuid module to generate a GUID as part of the output name
        # This will ensure a unique output name
        output = 'Map_{}.{}'.format(str(uuid.uuid1()), format)
        outputFile = os.path.join(arcpy.env.scratchFolder, output)

        # Export the WebMap
        printMessage("Exporting map to an output file...","info")
        if format.lower() == "pdf":
            # If legend page for PDF
            if (legendPDF):
                # Create a new PDF and append the pages
                output = 'Map1_{}.{}'.format(str(uuid.uuid1()), format)
                outputFile1 = os.path.join(arcpy.env.scratchFolder, output)
                arcpy.mapping.ExportToPDF(mxd, outputFile1)
                outputPDF = arcpy.mapping.PDFDocumentCreate(outputFile)
                outputPDF.appendPages(outputFile1)
                outputPDF.appendPages(legendPDF)
            # Just one page PDF
            else:
                arcpy.mapping.ExportToPDF(mxd, outputFile)
        elif format.lower() == "jpg":
            arcpy.mapping.ExportToJPEG(mxd, outputFile)
        elif format.lower() == "png":
            arcpy.mapping.ExportToPNG(mxd, outputFile)

        # Clean up - delete the map document reference
        filePath = mxd.filePath
        del mxd, result
        os.remove(filePath)
        # --------------------------------------- End of code --------------------------------------- #
        # If called from gp tool return the arcpy parameter
        if __name__ == '__main__':
            # Return the output if there is any
            if outputFile:
                # If ArcGIS desktop installed
                if (arcgisDesktop == "true"):
                    arcpy.SetParameter(4, outputFile)
                # ArcGIS desktop not installed
                else:
                    return output
        # Otherwise return the result
        else:
            # Return the output if there is any
            if output:
                return output
        # Logging
        if (enableLogging == "true"):
            # Log end of process
            logger.info("Process ended.")
            # Remove file handler and close log file
            logMessage.flush()
            logMessage.close()
            logger.handlers = []
    # If arcpy error
    except arcpy.ExecuteError:
        # Build and show the error message
        errorMessage = arcpy.GetMessages(2)
        printMessage(errorMessage,"error")
        # Logging
        if (enableLogging == "true"):
            # Log error
            logger.error(errorMessage)
            # Log end of process
            logger.info("Process ended.")
            # Remove file handler and close log file
            logMessage.flush()
            logMessage.close()
            logger.handlers = []
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)
    # If python error
    except Exception as e:
        errorMessage = ""
        # Build and show the error message
        # If many arguments
        if (e.args):
            for i in range(len(e.args)):
                if (i == 0):
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = unicode(e.args[i]).encode('utf-8')
                else:
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = errorMessage + " " + str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
        # Else just one argument
        else:
            errorMessage = e
        printMessage(errorMessage,"error")
        # Logging
        if (enableLogging == "true"):
            # Log error
            logger.error(errorMessage)
            # Log end of process
            logger.info("Process ended.")
            # Remove file handler and close log file
            logMessage.flush()
            logMessage.close()
            logger.handlers = []
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)
# End of main function


# Start of re-size element function
def reSizeElement(mxd,elementType,height,width,X,Y):
    # Resize element by setting the values below
    element = arcpy.mapping.ListLayoutElements(mxd, elementType)[0]
    element.elementHeight = height
    element.elementWidth = width
    element.elementPositionX = X
    element.elementPositionY = Y
# End of re-size element function


# Start of create legend function
def createLegend(mxd):
    # Create a copy of the MXD
    copyMXD = 'Legend_{}.{}'.format(str(uuid.uuid1()), ".mxd")
    mxd.saveACopy(copyMXD)
    legendMXD = arcpy.mapping.MapDocument(copyMXD)

    # Remove all data frame elements
    for element in arcpy.mapping.ListLayoutElements(legendMXD, "DATAFRAME_ELEMENT"):
        # Remove the data frame by moving it off the page
        element.elementPositionX = -5000
        element.elementPositionY = -5000
    # Remove all text elements
    for element in arcpy.mapping.ListLayoutElements(legendMXD, "TEXT_ELEMENT"):
        # Remove the text by moving it off the page
        element.elementPositionX = -5000
        element.elementPositionY = -5000
    # Remove all picture elements
    for element in arcpy.mapping.ListLayoutElements(legendMXD, "PICTURE_ELEMENT"):
        # Remove the picture by moving it off the page
        element.elementPositionX = -5000
        element.elementPositionY = -5000
    # Remove all graphic elements
    for element in arcpy.mapping.ListLayoutElements(legendMXD, "GRAPHIC_ELEMENT"):
        # Remove the graphic by moving it off the page
        element.elementPositionX = -5000
        element.elementPositionY = -5000
    # Remove all map surround elements
    for element in arcpy.mapping.ListLayoutElements(legendMXD, "MAPSURROUND_ELEMENT"):
        # Remove the map surround by moving it off the page
        element.elementPositionX = -5000
        element.elementPositionY = -5000

    # Resize legend element by adding values - Height, width, X and Y
    legend = arcpy.mapping.ListLayoutElements(legendMXD, "LEGEND_ELEMENT")[0]
    height = legendMXD.pageSize.height-2 # Resize legend to whole page
    width = legendMXD.pageSize.width-2 # Resize legend to whole page
    X = 1  # Move the legend to the top left corner of the page
    Y = legendMXD.pageSize.height - 1 # Move the legend to the top left corner of the page
    reSizeElement(legendMXD,"LEGEND_ELEMENT",height,width,X,Y)
    # Use the uuid module to generate a GUID as part of the output name
    # This will ensure a unique output name
    output = 'Legend_{}.{}'.format(str(uuid.uuid1()), ".pdf")
    outputFile = os.path.join(arcpy.env.scratchFolder, output)
    # Export the WebMap
    printMessage("Exporting legend to an output file...","info")
    arcpy.mapping.ExportToPDF(legendMXD, outputFile)
    return outputFile
# End of create legend function


# Start of print message function
def printMessage(message,type):
    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        if (type.lower() == "warning"):
            arcpy.AddWarning(message)
        elif (type.lower() == "error"):
            arcpy.AddError(message)
        else:
            arcpy.AddMessage(message)
    # ArcGIS desktop not installed
    else:
        print(message)
# End of print message function


# Start of set logging function
def setLogging(logFile):
    # Create a logger
    logger = logging.getLogger(os.path.basename(__file__))
    logger.setLevel(logging.DEBUG)
    # Setup log message handler
    logMessage = logging.FileHandler(logFile)
    # Setup the log formatting
    logFormat = logging.Formatter("%(asctime)s: %(levelname)s - %(message)s", "%d/%m/%Y - %H:%M:%S")
    # Add formatter to log message handler
    logMessage.setFormatter(logFormat)
    # Add log message handler to logger
    logger.addHandler(logMessage)

    return logger, logMessage
# End of set logging function


# Start of send email function
def sendEmail(message):
    # Send an email
    printMessage("Sending email...","info")
    # Server and port information
    smtpServer = smtplib.SMTP(emailServerName,emailServerPort)
    smtpServer.ehlo()
    smtpServer.starttls()
    smtpServer.ehlo
    # Login with sender email address and password
    smtpServer.login(emailUser, emailPassword)
    # Email content
    header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + '\n'
    body = header + '\n' + emailMessage + '\n' + '\n' + message
    # Send the email and close the connection
    smtpServer.sendmail(emailUser, emailTo, body)
# End of send email function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Test to see if ArcGIS desktop installed
    if ((os.path.basename(sys.executable).lower() == "arcgispro.exe") or (os.path.basename(sys.executable).lower() == "arcmap.exe") or (os.path.basename(sys.executable).lower() == "arccatalog.exe")):
        arcgisDesktop = "true"

    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        argv = tuple(arcpy.GetParameterAsText(i)
            for i in range(arcpy.GetArgumentCount()))
    # ArcGIS desktop not installed
    else:
        argv = sys.argv
        # Delete the first argument, which is the script
        del argv[0]
    # Logging
    if (enableLogging == "true"):
        # Setup logging
        logger, logMessage = setLogging(logFile)
        # Log start of process
        logger.info("Process started.")
    # Setup the use of a proxy for requests
    if (enableProxy == "true"):
        # Setup the proxy
        proxy = urllib2.ProxyHandler({requestProtocol : proxyURL})
        openURL = urllib2.build_opener(proxy)
        # Install the proxy
        urllib2.install_opener(openURL)
    mainFunction(*argv)
