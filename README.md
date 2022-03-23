# Data Handler Tool  

**Tool enables to handle `.csv, .xlsx, .las, .dlis` file types, convert them into WITSML 1.4.1.1 competible xml files**.  
Software has been builded by using [Streamlit](https://streamlit.io/). 
Splitted:  
- .LAS files will be stored in /generateLas folder
- xml files with more than 10000 lines is not possible, when this is the case xml files will be splitted into parts and will be saved to xml folder.
  
## Functionality
- [x] Handling large files up to 1.5 gb, batching them into the generateLas folder. Each batch will have ~= 75mb file sizes after split
- [x] .dlis file type support added
- [x] .csv and .xlsx file type support
- [x] .las file type support enhanced
- [x] UI is more interactive
- [x] Information about the uploaded file is displayed to the user for QC purposes
- [ ] Building communication with KDI Sitecom

## Screenshot of the tool

![Image](Web%20capture_23-3-2022_151641_localhost.jpeg)

| Command | Description |
| --- | --- |
| pip install -r requirements.txt | Download all the required requirements for the software |
| streamlit run app.py | Run the web server |