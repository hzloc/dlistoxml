# Data Handler Tool  

**Tool enables to handle `.csv, .xlsx, .las, .dlis` file types, convert them into WITSML 1.4.1.1 competible xml files**.  
Software has been builded by using [Streamlit](https://streamlit.io/). 
## Functionality
- [x] Handling large files up to 1.5 gb, batching them into the generateLas folder. Each batch will have ~= 75mb file sizes after split
- [x] .dlis file type support added
- [x] .csv and .xlsx file type support
- [x] .las file type support enhanced
- [x] UI is more interactive
- [ ] Building communication with KDI Sitecom


| Command | Description |
| --- | --- |
| pip install -r requirements.txt | Download all the required requirements for the software |
| streamlit run app.py | Run the web server |