# HDB Flats MOP 2026 – Property & Project Name Mapping

This project identifies **HDB flats in Singapore that were completed in 2021**, which means they will **reach their 5-year Minimum Occupancy Period (MOP) in 2026**.

It bridges a gap found in this article from *The Straits Times*:

> [Over 13,400 HDB flats to reach MOP in 2026; analysts say supply could moderate resale price growth](https://www.straitstimes.com/singapore/housing/over-13400-hdb-flats-to-reach-mop-in-2026-analysts-say-supply-could-moderate-resale-price-growth)

While the article breaks down the number of flats by **town**, it does **not** provide a breakdown by **HDB project name / estate**.
👉 **This project provides that missing granularity.**

---

## ✨ What This Project Produces

A dataset named:

```
data/hdb-property-info-with-name.csv
```

Each row represents **a block that meets ALL of the following criteria:**

✔ Completed in **2021**
✔ Classified as **residential**
✔ Contains **3-room and/or 4-room units**
✔ Mapped to its **HDB project / estate name**

If you don’t want to run the scripts — simply download this CSV from the `data/` folder.

---

## 🗺️ Data Sources

This project combines **three** public datasets / APIs:

| Purpose                                                               | Source                                                       |
| --------------------------------------------------------------------- | ------------------------------------------------------------ |
| Block-level property details (year completed, flat types, town, etc.) | HDB Property Information — data.gov.sg                       |
| Project-level geometry polygons & project names                       | HDB Public Housing Building Under-Construction — data.gov.sg |
| Convert block address to latitude/longitude                            | OneMap Singapore API                                         |

---

## 🔍 How It Works (Pipeline)

### 1️⃣ Download block-level HDB property info

We query the dataset for blocks that:

* were **completed in 2021**
* are **residential**
* have **3-room or 4-room units sold**

We also fetch the **town metadata mapping** and geocode each block address to **lat/lon using OneMap**.
Implementation: `utils.py` 

---

### 2️⃣ Download HDB project geometry & names

We retrieve polygons representing public housing projects and map:

```
Project Name  →  Polygon Coordinates
```

Implementation: `utils.py` 

---

### 3️⃣ Match each block to its project name

Using **Shapely geometry checks**, each block’s lat/lon point is tested to see which **HDB project polygon contains it**, and the HDB project **name** is assigned.

Implementation: `main.py` 

---

### 4️⃣ Save the final dataset

The resulting file is:

```
data/hdb-property-info-with-name.csv
```

---

## 📁 Repository Structure

```
.
├── main.py
├── utils.py
├── data/
│   ├── hdb-property-info.csv
│   ├── hdb_name_to_coords.json
│   └── hdb-property-info-with-name.csv   👈 Final dataset
├── .env                                  👈 Your OneMap credentials
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the repo

```bash
git clone <repo-url>
cd <repo-folder>
```

### 2️⃣ Install dependencies

```python
pip install -r requirements.txt
```

*(Ensure `shapely`, `pandas`, `requests`, and `python-dotenv` are included.)*

### 3️⃣ Add OneMap API credentials

Create a **.env** file:

```
ONEMAP_EMAIL=your_email@example.com
ONEMAP_EMAIL_PASSWORD=your_password
```

---

## ▶️ Running the Project

```python
python main.py
```

This will:

1. Download required datasets (only if not already present)
2. Geocode HDB block addresses
3. Match HDB blocks to HDB project polygons
4. Produce the final CSV

---

## 📊 Key Columns in Final CSV

| Column                  | Meaning                                 |
| ----------------------- | --------------------------------------- |
| blk_no                  | Block number                            |
| street                  | Street name                             |
| year_completed          | Year HDB block completed                |
| area                    | HDB town                                |
| 3room_sold / 4room_sold | Units sold                              |
| address                 | Combined address                        |
| lat / lon               | Geocoded coordinates                    |
| name                    | **HDB project / estate name**           |

---

## 🚧 Assumptions & Limitations

1. OneMap geocoding returns the **closest match**, so edge cases may mis-map
2. A block must fall **inside one and only one project polygon**
3. Only **2021 completion year** is included
4. Only **3-room & 4-room residential flats are considered**

---

## 🏛️ Data Attribution and References

Data is sourced from:

* Housing & Development Board. (2018). HDB Property Information (2025) [Dataset]. data.gov.sg. Retrieved December 28, 2025 from https://data.gov.sg/datasets/d_17f5382f26140b1fdae0ba2ef6239d2f/view
* Housing & Development Board. (2023). HDB Public Housing Building Under-Construction (2025) [Dataset]. data.gov.sg. Retrieved December 28, 2025 from https://data.gov.sg/datasets/d_930e662ac7e141fe3fd2a6efa5216902/view
* OneMap Singapore API from https://www.onemap.gov.sg/apidocs/

All data belongs to their respective owners.

---

## 📝 Disclaimer

> **Note on AI Use**
> This project contains content generated with the help of ChatGPT, including code scaffolding and documentation. The author has manually tested and validated the outputs where possible, but users should independently verify results before relying on them.




