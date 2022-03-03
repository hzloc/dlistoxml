from collections import namedtuple
from ntpath import join
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
from datetime import date
from lxml.etree import Element, SubElement, ElementTree, tostring
import uuid
from io import DEFAULT_BUFFER_SIZE
from pathlib import Path
from os import walk, fspath, remove
from os.path import join as osjoin


def detailsLasFile(wells):
    d = {}
    for detail in wells:
        d[detail["mnemonic"]] =  detail.value
    return d


def check(mnemonics, units):
    filepath = "{}/configs/".format(Path(Path.cwd()).as_posix())
    kdiUnits = pd.read_excel("{}KDIunits.xlsx".format(filepath))['Units']
    with open("{}lognames.txt".format(filepath)) as f:
        kdiMnemonics = f.readlines()
    df = pd.DataFrame([mnemonics, units]).T
    df.columns = ['Mnemonics', 'Units']
    df = df.replace({'Units': {'': 'unitless', ' ': 'unitless'}})
    arr1, arr2 = [],[]
    for mnemonic, unit in df.values:
        if(mnemonic in kdiMnemonics):
            arr1.append("Yes")
        else:
            arr1.append('No')
        if(unit in kdiUnits.values):
            arr2.append(unit)
        else:
            arr2.append('Not recognized')
    df = df.assign(KDI_Unit= arr2, Mnemonic_Structure= arr1)

    return df

class xmlGen:
    def __init__(self, filename, wellname, wellborename, bu, fieldname,
                 servicecompany, runnumber, creation_date, uidWell,
                 uidWellbore, uidWellInterventionId, purpose, datatype,
                 servicetype, df, uid, nullValue, dataSource, units, conversion) -> None:
        self.wellname = wellname
        self.filename = filename
        self.bu = bu
        if uid == False:
            self.uid = str(uuid.uuid1())
        self.fieldname = fieldname
        self.servicecompany = servicecompany
        self.runnumber = str(runnumber)
        self.creation_data = creation_date
        self.uidWell = uidWell
        self.uidWellbore = uidWellbore
        self.wellborename = wellborename
        self.uidWellInterventionId = uidWellInterventionId
        self.purpose = purpose
        self.datatype = datatype
        self.servicetype = servicetype
        self.description = str(purpose)
        self.df = df
        self.indexType = df.columns[0]
        self.nullValue = nullValue
        self.dataSource = dataSource        
        self.units = units
        self.comments = 'BU: ' + str(bu) + '\nAsset:' + str(fieldname)
        self.servicecategory = str(uidWellInterventionId) + ',' + str(
            runnumber) + ',' + str(servicetype) + ',' + str(datatype)
        self.mnemonic = df.columns
        
        if conversion == False:
            self.mnemonic = df.columns
        else:
            self.mnemonic = self.convertMnemonics(df.columns)

    def convertMnemonics(self,mnemonics):
        temp = []
        for mnemonic in mnemonics:
            temp.append("{}_{}_{}".format(self.servicetype, self.datatype,mnemonic))
        return temp
    
    
    def indexTypeDeterminer(self):
        indexType = ''
        startIndex = ''
        endIndex = ''
        if str(self.indexType).lower().find(r'tim') != -1:
            indexType = 'date time'
            startIndex = self.df.iloc[1, 0]
            endIndex = self.df.iloc[1, -1]
        elif str(self.indexType).lower().find(r'dept') != -1:
            indexType = 'measured depth'
            startIndex = str(self.df.iloc[1, 0])
            endIndex = str(self.df.iloc[1, -1])
        return [indexType, startIndex, endIndex]

    def createtopXML(self):
        indexType, startIndex, endIndex = self.indexTypeDeterminer()
        datas = self.df.values[:]
        if(str(self.filename.split('.')[1]).lower() == 'dlis'):
            datas = self.df.values[1:]
        root = Element("logs",
                       xmlns="http://www.witsml.org/schemas/1series",
                       version="1.4.1.1")
        log = SubElement(root,
                         'log',
                         uidWell=self.uidWell,
                         uidWellbore=self.uidWellbore,
                         uid=self.uid)
        namewell = SubElement(log, 'nameWell')
        namewell.text = self.wellname
        top_1_2 = SubElement(root, 'nameWellbore')
        top_1_2.text = self.wellborename
        top_1_3 = SubElement(root, 'name')
        top_1_3.text = self.filename
        top_1_4 = SubElement(root, 'serviceCompany')
        top_1_4.text = self.servicecompany
        top_1_5 = SubElement(root, 'runNumber')
        top_1_5.text = self.runnumber
        top_1_6 = SubElement(root, 'creationDate')
        top_1_6.text = self.creation_data
        top_1_7 = SubElement(root, 'description')
        top_1_7.text = self.description
        top_1_8 = SubElement(root, 'indexType')
        top_1_8.text = indexType
        if self.indexTypeDeterminer() == 'date time':
            top_1_9 = SubElement(root, 'startDateTimeIndex')
            top_1_9.text = str(startIndex)
            top_1_10 = SubElement(root, 'endDateTimeIndex')
            top_1_10.text = str(endIndex)
        else:
            top_1_9a = SubElement(root, 'startIndex')
            top_1_9a.text = str(startIndex)
            top_1_10a = SubElement(root, 'endIndex')
            top_1_10a.text = str(endIndex)
        top_1_11 = SubElement(root, 'indexCurve')
        top_1_11.text = self.indexType
        top_1_12 = SubElement(root, 'nullValue')
        top_1_12.text = str(self.nullValue)
        j = 1
        for mnem in self.mnemonic:
            top_2 = SubElement(root, 'logCurveInfo', uid=mnem)
            child1 = SubElement(top_2, 'mnemonic')
            child1.text = str(mnem)
            child1a = SubElement(top_2, 'unit')
            child1a.text = str(self.units[j - 1])
            if indexType == 'date time':
                child2 = SubElement(top_2, 'minDateTimeIndex')
                child2.text = str(startIndex)
                child3 = SubElement(top_2, 'maxDateTimeIndex')
                child3.text = str(endIndex)
            child4 = SubElement(top_2, 'curveDescription')
            child4.text = ''
            child4a = SubElement(top_2, 'dataSource')
            child4a.text = self.dataSource
            child5 = SubElement(top_2, 'typeLogData')
            if str(mnem).lower().find('time') != -1:
                child5.text = 'date time'
            else:
                child5.text = 'double'
            j += 1
        top_3 = SubElement(root, 'logData')
        top_3_1 = SubElement(top_3, 'mnemonicList')
        top_3_1.text = ','.join(self.mnemonic)
        top_3_2 = SubElement(top_3, 'unitList')
        top_3_2.text = str(','.join(self.units)).lower()

        for curve in datas[:]:
            # print(type(curve[0]))
            top_3_3 = SubElement(top_3, 'data')
            x = ','.join(str(v) for v in curve)
            x1 = x.find(',')
            x2 = x[x1 + 1:]
            top_3_3.text = x2

        top_4 = SubElement(root, 'commonData')
        top_4_1 = SubElement(top_4, 'dTimCreation')
        date1 = str(date.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])
        date1 += '+00:00'
        top_4_1.text = date1
        top_4_2 = SubElement(top_4, 'comments')
        top_4_2.text = self.comments
        top_4_3 = SubElement(top_4, 'serviceCategory')
        top_4_3.text = self.servicecategory

        root = tostring(root, pretty_print=True)

        return root


class dlisioWrapper:
    def __init__(self, file):
        self.__file = file
        self.logFiles = self.logfiles()
        self.tools = self.logFiles[0].tools
        self.frames = self.frames()
        self.channels = self.channelGetter()
        self.datas = self.all_data()
        print(self.logFiles)        
    
    def displayTool(self):
        arr = []
        for tool in self.tools:
            arr.append({
                "Name": tool.name,
                "Description": tool.description,
                "Generic Name": tool.generic_name,
                "Status": tool.status,
                "Parts": (",").join([x.name for x in tool.parts]), 
                "Origin": tool.origin,
                "Trademark_name": tool.trademark_name,
                "Copynumber": tool.copynumber,
            })
        return DataFrame(arr)

    def logfiles(self):
        logicalfiles = []
        for f in self.__file:
            logicalfiles.append(f)
        self.logFiles = logicalfiles
        return self.logFiles

    def frames(self):
        for logfiles in self.logFiles:
            self.frames = logfiles.frames
        return self.frames

    def channelGetter(self):
        arr = []
        channels = namedtuple('Channel', ['names', 'units', 'chcode', 'frame'])
        for frame in self.frames:
            units = [i.units for i in frame.channels]
            names = [channel.name for channel in frame.channels]
            arr.append(channels._make([names, units, frame.channels, frame]))
        self.channels = arr
        return self.channels

    def all_data(self):
        alldata = namedtuple('Data', ['frame', 'channels', "units", 'data'])
        arr = []
        for i, frames in enumerate(self.frames):
            curves = frames.curves()
            curves = curves[self.channels[i].names]
            arr.append(
                alldata._make([
                    frames, self.channels[i].names, self.channels[i].units,
                    curves.tolist()
                ]))
        self.datas = arr
        return self.datas

    def flattener(self):
        for col in self.data:
            for el in col.data[0]:
                pass

    def channel(self, curve):
        arr = []
        channel = namedtuple('Channel',
                             ['name', 'frame', 'dim', 'unit', 'data'])
        for chanel in self.channels:
            for index, name in enumerate(chanel.names):
                if (curve == name):
                    temp = channel._make([
                        name, chanel.frame, chanel.chcode[index].dimension,
                        chanel.chcode[index].units,
                        chanel.chcode[index].frame.curves()[name]
                    ])
                    arr.append(temp)
        return arr

    def dlisioPandas(self):
        temp = []
        for chunk in self.datas:
            frame = chunk.frame
            data = np.array(chunk.data, dtype="object")
            channels = chunk.channels
            units = [unit if unit else "unitless" for unit in chunk.units]
            data = np.insert(data, 0, units, axis=0)

            for index, el in enumerate(data[-1]):
                if (type(el) is np.ndarray):
                    temp.append(index)
                continue
            data = np.ma.array(data, dtype='object', mask=False)
            for mask in data.mask:
                for v in temp:
                    mask[v] = True
            df = DataFrame(data, columns=channels, dtype="object")
            df = df.dropna(axis=1)
            for col in df.columns:
                df[col] = df[col].astype(str)
        return df


class LasChunker:
    def __init__(self, file: str)-> 'Laschunks':
            self.cleaner()
            self.file = file
            self.filenm = file.split('/')[-1].split('.')[0]
            with open(self.file, 'r', buffering=DEFAULT_BUFFER_SIZE) as f:
                self.datas = [l for l in f.readlines()]

    def cleaner(self):
        for root, dirs, files in walk(fspath(Path.cwd()) + '/generateLas'):
            for file in files:
                    remove(osjoin(root, file))

    def splitLasFiletoHeaderandData(self):
        locators = {}
        for index,data in enumerate(self.datas):
            if (data[0] == '~') or (data[0] == '#'): locators[index]=data;
            if data.startswith('~A'): locators['unwrapping'] = index;
        try:
            startheader = locators['unwrapping']
            lastheader = list(locators.keys())[-1] # last value of the index contains header info
            numberofcurves = int(lastheader)-int(startheader) + 1
        except ValueError: print(locators)
        # print(numberofcurves)
        headers = self.datas[0:lastheader]
        data = self.datas[lastheader+1:]
        return [headers,data, numberofcurves]


    def chunkbigFile(self):
        headers, data, n = self.splitLasFiletoHeaderandData()
        n = n * 10**5
        output = [data[i:i+n] for i in range(0,len(data),n)] 
        for ind,el in enumerate(output):
            el = headers + el
            with open(osjoin('{}/generateLas'.format(Path(Path.cwd()).as_posix()), f'{self.filenm}-{ind}.las'), mode='w', newline='') as newLasfile:
                newLasfile.write(''.join(el))

        return f'{len(output)} .las Files has been created and going to be processed'
