import datetime
from lib2to3.pgen2.tokenize import untokenize
from google.protobuf.descriptor import Error
from numpy.core.fromnumeric import std
import pandas as pd
import streamlit as st
from wrapper import dlisioWrapper, xmlGen, LasChunker, detailsLasFile, check
from dlisio import dlis
import lasio
import numpy as np
#Time
import time

ALLOWED_FILE_TYPE=['las','dlis']
wellDetails = {"WELL": '', 
                "COMP": "",
                "FLD": "",
                "SRVC": "",
                "NULL": "",}
def get_binary_file_downloader_html(bin_file, file_label="File"):
    with open(bin_file, "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download: {file_label}</a>'
    return href


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

    # """
    # when uploaded file size is bigger than 100mb
    # seperate into multiple files
    # when it is not we gonna directly process them
    # """
    lastUpload = initFile(uploadedFile, uploadedFile.name)
    # .dlis format
    if str(uploadedFile.name).split(".")[1] == "dlis":
        dlf = dlis.load("./uploads/" + uploadedFile.name)
        dlfwrap = dlisioWrapper(dlf)
        lf = dlfwrap.dlisioPandas()
        index1 = lf.columns[0]
        units = lf.iloc[0]
        st.write("### File")
        st.dataframe(lf)

    # .las format
    if str(uploadedFile.name).split(".")[1] == "las":
        if(uploadedFile.size > 100000000):
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
        value=datetime.datetime.now(),
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
        ffname = str(uploadedFile.name).split(".")[0]
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
        # st.markdown(
        #     get_binary_file_downloader_html(f"xml/{ffname}.xml", f"{ffname}"),
        #     unsafe_allow_html=True,
        # )
        st.download_button(
            "Download",
            xmls,
            file_name=f"{ffname}.xml",
        )
