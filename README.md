<p align="center">
  <img src="logo.png" alt="pywilderlab Logo" width="300"/>
</p>

# WilderGRAB

A Python utility for downloading **eDNA results from the Wilderlab API** and saving them into an Excel workbook.  
The script handles authentication, fetches jobs, samples, taxa, and records, and automatically splits large record tables across multiple Excel sheets if needed.

---

## Features

- 🔑 Authenticates securely with **Wilderlab's AWS-signed API**  
- 📂 Downloads:
  - Jobs
  - Samples
  - Taxa
  - Records (per job, concatenated)  
- 📝 Saves everything into a single Excel workbook (`.xlsx`)  
- 🚦 Automatically splits large record tables if they exceed Excel’s row limit (1,048,576 rows)  
- ⚙️ Simple configuration at the top of the script  

---

## Requirements

- Python **3.9+**  
- Packages:
  - `pandas`
  - `requests`
  - `aws-requests-auth`
  - `xlsxwriter`

Install dependencies:

```bash
pip install pandas requests aws-requests-auth xlsxwriter
```

---

## Configuration

At the top of **`pywilderlab.py`**, adjust settings:

```python
save_location = 'eDNA_Data_September_2025.xlsx'  # output file
include_jobs    = True
include_samples = True
include_taxa    = True
include_records = True
```

### API Credentials

Set credentials via environment variables (recommended):

```bash
export WILDERLAB_AWS_ACCESS_KEY="your_access_key"
export WILDERLAB_AWS_SECRET_KEY="your_secret_key"
export WILDERLAB_XAPI_KEY="your_xapi_key"
```

Alternatively, edit `api_credentials()` in the script with your keys.

---

## Usage

Run the script:

```bash
python pywilderlab.py
```

The script will:

1. Authenticate with the Wilderlab API  
2. Download requested tables (`jobs`, `samples`, `taxa`, `records`)  
3. Write results into the Excel file specified in `save_location`  

---

## Output

Example output file structure:

- `Jobs`  
- `Samples`  
- `Taxa`  
- `records` (or multiple sheets: `records_part1`, `records_part2`, … if too large)  

---

## Notes

- **Large record queries** can take a while depending on the number of jobs.  
- If no outputs are requested (all `include_*` flags are `False`), the script will print `No outputs requested`.  

---

## License

This project is distributed for internal/research use. Check Wilderlab’s [API terms](https://wilderlab.co/api-instructions) before sharing results.
