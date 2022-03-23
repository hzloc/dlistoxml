import datetime
from distutils.command.upload import upload
from distutils.log import error
from lib2to3.pgen2.tokenize import untokenize
from lib2to3.pytree import Base
from uuid import uuid1, uuid3
from google.protobuf.descriptor import Error
from numpy.core.fromnumeric import std
import pandas as pd
import streamlit as st
from wrapper import dlisioWrapper, xmlGen, LasChunker, detailsLasFile, check
from dlisio import dlis
import lasio
import numpy as np
#Time
from datetime import datetime
import time


ALLOWED_FILE_TYPE=['las','dlis', 'csv', 'xlsx']
wellDetails = {"WELL": '', 
                "COMP": "",
                "FLD": "",
                "SRVC": "",
                "NULL": "",}

servicetypes = {
    "CT": "Coiled Tubing",
    "WL": "Wireline",
    "SL": "Slickline",
    "HWU": "Heavy Workover Unit",
    "SNUB": "Snubbing",
    "BLH": "Bullheading",
}
datatypes = {
    "OP": "Operational data",
    "RT": "Subsurface real-time logging data",
    "PJ": "Subsurface raw data from memory",
    "FNL": "Final corrected data",
}


# Upload file to the uploads folder
def initFile(uploadedFile, name):
    with open("./uploads/" + name, "wb") as f:
        f.writelines(uploadedFile)
    return f"./uploads/{name}"


uploadedFile = st.file_uploader("Upload a dlis file",
                                accept_multiple_files=False,
                                type=ALLOWED_FILE_TYPE
                               )

if uploadedFile is not None:
    filedetails = {
        "Name": uploadedFile.name,
        "Type": uploadedFile.type,
        "Size": uploadedFile.size,
    }
    st.write("### File basic information")
    st.write(pd.DataFrame(filedetails, index=[0]))
    file_ext = str(uploadedFile.name).split(".")[-1]
    # """
    # when uploaded file size is bigger than 100mb
    # seperate into multiple files
    # when it is not we gonna directly process them
    # """
    lastUpload = initFile(uploadedFile, uploadedFile.name)
    # table format
    if (file_ext == "csv") | (file_ext == "xlsx"):
        start = time.time()
        if file_ext == "csv":
            lf = pd.read_csv(uploadedFile, dtype=str, na_filter=True)
        else:
            lf = pd.read_excel(uploadedFile, dtype=str, na_filter=True, keep_default_na=False)
        
        with st.expander("More Details"):
            details = {
                    "Index Type": lf.columns[0],
                    "Data nodes": lf.shape[0],
                    "Number of Curves": lf.shape[1]
                    }
            st.write(details)
            mnemonics = lf.columns
            units = lf.iloc[0,:]
            st.dataframe(check(mnemonics, units))    

        
        st.write("### Data")
        st.dataframe(lf)
        end=time.time()
        st.write(f"### Execution time is: {'{:.2f}'.format(end-start)} seconds")
    
    
    # .dlis format
    if file_ext == "dlis":
        start = time.time()
        dlf = dlis.load("./uploads/" + uploadedFile.name)
        dlfwrap = dlisioWrapper(dlf)
        lf = dlfwrap.dlisioPandas()
        index1 = lf.columns[0]
        units = lf.iloc[0]
        ## Dropdown section for viewing more details
            ## Any informative code block about file details should be added here
        with st.expander("More Details"):
            with dlf as (f,*tail):
                details = {
                "Index Type": lf.columns[0],
                "Data nodes": lf.shape[0]-1,
                "Number of Curves": lf.shape[1],
                "Direction": "Increasing" if (float(lf.iloc[2,0]) - float(lf.iloc[3,0])) < 0 else "decreasing"}
                st.write(pd.DataFrame(details, index=[1]))
                st.dataframe(check(lf.columns, units))
                st.markdown("### Used tools for logs")
                st.dataframe(dlfwrap.displayTool()) 
            end=time.time()
            st.write(f"### Execution time is: {'{:.2f}'.format(end-start)} seconds")
        st.write("### File")
        st.dataframe(lf)


    # .las format
    if file_ext == "las":
        if(uploadedFile.size > 100000000):
            print("File is going to be butchered")
            message = LasChunker(lastUpload).chunkbigFile()
            st.write("## Files are being batched.....")
            st.write(f"### {message}")
        else:
            start = time.time()
            lasiofile = lasio.read("./uploads/" + uploadedFile.name, encoding="utf8")
            lf = lasiofile.df().reset_index()
            lf = lf.fillna(-999.25)
            
            ## Dropdown section for viewing more details
            ## Any informative code block about file details should be added here
            with st.expander("More Details"):
                details = {
                    "Index Type": lf.columns[0],
                    "Data nodes": lf.shape[0],
                    "Number of Curves": lf.shape[1],
                    "Direction": "Increasing" if (lf.iloc[0,0] - lf.iloc[1,0]) < 0 else "decreasing"
                }
                units = [e.unit for e in lasiofile.curves]
                mnemonics = [e.mnemonic for e in lasiofile.curves]
                st.dataframe(check(mnemonics, units))    
                details = pd.DataFrame(details, index=[0])
                st.dataframe(details)
                wellDetails = detailsLasFile(lasiofile.well)
                st.write(wellDetails)
            
            st.write("### Data")
            st.dataframe(lf)
            end=time.time()
            st.write(f"### Execution time is: {'{:.2f}'.format(end-start)} seconds")


with st.form("xmlgeneration"):
    st.write(f"Xml Generation from {','.join(ALLOWED_FILE_TYPE).upper()} files")
    # forms
    wellname = st.text_input("Wellname", value=wellDetails['WELL'], key="well")
    wellborename = st.text_input("Wellbore Name")
    bu = st.text_input("Business Unit", wellDetails['COMP'])
    fieldname = st.text_input("Field", value=wellDetails['FLD'])
    servicecompany = st.text_input("Service Company", wellDetails['SRVC'])
    runnumber = st.number_input("Run Number", step=1)
    creation_date = st.text_input(
        "Creation Date",
        value=datetime.now(),
        help="Timestamp format for SiteCom: yyyy-MM-dd”T”HH:mm:ss.fffzzz",
    )
    uidWell = st.text_input("Well UID", key="uidWell", autocomplete="default")
    uidWellbore = st.text_input("Wellbore UID", autocomplete="default")
    uidWellInterventionId = st.text_input("Well Intervention ID")
    dataSource = st.text_input("Data Source", max_chars=32)
    purpose = st.text_input("Servise Purpose run")
    nullValue = st.text_input("Null Value", wellDetails['NULL'])
    datatype = st.selectbox("Data Type", datatypes, format_func=lambda x: datatypes[x])
    servicetype = st.selectbox("Service Type", options=servicetypes, format_func=lambda x: servicetypes[x])
    conversion = st.checkbox("Follow mnemonics naming convention", value=False, help="Name=[Equipment Code]+”_”+[Data Type]+”_”+[Run Number – For Depth Related Data]+”_”-+[Log Name] ")

    # submit
    submit = st.form_submit_button("Submit")

if submit:
    # KDI Requirements of the 10000 lines
    if(lf.shape[0] < 10000):
        xml = xmlGen(
            uploadedFile.name,
            wellname,
            wellborename,
            bu,
            fieldname,
            servicecompany,
            runnumber,
            creation_date,
            uidWell,
            uidWellbore,
            uidWellInterventionId,
            purpose,
            datatype,
            servicetype,
            lf,
            False,
            nullValue,
            dataSource,
            units=units,
            conversion=conversion,
        )
        xmls = xml.createtopXML()
        try:
            ffname = str(uploadedFile.name).split(".")[0] + "-"  + str(uuid1())
            with open("xml/{}.xml".format(ffname), mode="wb") as f:
                f.write(xmls)
        except Error:
            print(Error)
        else:
            st.write(
                "File: **{}.xml** is ready for downloading :sunglasses:".format(
                    ffname))
            with st.form("generatedxml"):
                xmlrepr = st.text_area(label="Generated Xml",
                                    value=xmls.decode(),
                                    height=800)

            ffname = str(uploadedFile.name).split(".")[0] + "-" + str(uuid1())
            st.download_button(
                "Download",
                xmls,
                file_name=f"{ffname}.xml",
            )
    # When the file has more data than 10000 lines
    # Dataframe will be diveded into parts containing only 1-9939 data points, to have max 10000 lines xml files
    # Number of mnemonics * 7-26 tags are coming from inputs and WD requirements 
    else:
        datanodes = lf.shape[0] # number of the data
        arr_xmls = []
        print(len(mnemonics))
        start, end = 1, 10000-len(mnemonics)*7-26
        while(datanodes > 0):
            lf_temp = lf.iloc[start:end,:]
            xml = xmlGen(
            uploadedFile.name,
            wellname,
            wellborename,
            bu,
            fieldname,
            servicecompany,
            runnumber,
            creation_date,
            uidWell,
            uidWellbore,
            uidWellInterventionId,
            purpose,
            datatype,
            servicetype,
            lf_temp,
            False,
            nullValue,
            dataSource,
            units=units,
            conversion=conversion,)
           
            xmls = xml.createtopXML()
            arr_xmls.append(xmls)
            datanodes-=10000-len(mnemonics)*7-26
            start += 10000-len(mnemonics)*7-26
            end += 10000-len(mnemonics)*7-26
            if datanodes < 10000-len(mnemonics)*7-26:
                end = start + datanodes

    print(len(arr_xmls))
    for ind,xmls in enumerate(arr_xmls):
        try:
            ffname = str(ind+1) + "-" + str(uploadedFile.name).split(".")[0]
            with open("xml/{}.xml".format(ffname), mode="wb") as f:
                f.write(xmls)

            st.text_area(
                label=ffname,
                value=xmls.decode(),
                key=uuid1()
            )
            st.download_button(
                label="Download " + ffname,
                file_name=str(ffname) + ".xml",
                data=xmls,
                mime="text/xml",
                key=uuid1()
            )
        except Error:
            print(Error)
