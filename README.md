# Medical School Curriculum Analysis - Learning Objectives

Tools for extracting and analyzing action verbs from educational learning objectives using Bloom's Taxonomy, with optional biomedical concept recognition via MetaMap.

## Overview

This repository contains scripts for:

1. **Action Verb Extraction** - Identifying action verbs in learning objectives and mapping them to Bloom's Taxonomy cognitive levels
2. **Statistical Analysis** - R scripts for analyzing action verb distributions across courses, modules, and disciplines
3. **Biomedical Concept Recognition** - Mapping learning objectives to UMLS concepts using MetaMap (requires additional setup)

## Data Files

### BloomsLists_NewtonEtAL_2020.csv

A curated list of action verbs with their corresponding Bloom's Taxonomy cognitive level scores. This data is summarized from:

> Newton, P. M., Da Silva, A., & Peters, L. G. (2020). A Pragmatic Master List of Action Verbs for Bloom's Taxonomy. *Frontiers in Education*, 5, 107. https://doi.org/10.3389/feduc.2020.00107

The file contains three columns:
- `id` - Unique identifier
- `verb` - The action verb
- `bloomlvl` - Numeric Bloom's Taxonomy level (1-6 scale)

### objectives.csv

Your input file containing learning objectives. Required column layout:

| Column | Description |
|--------|-------------|
| course | Course identifier |
| module | Module identifier |
| discipline | Discipline/subject area |
| lecture | Lecture code |
| title | Lecture title |
| code | Unique objective code |
| objective | The learning objective text |

## Installation

### Prerequisites

- Python 3.7+
- R (for analysis scripts)

### Python Dependencies

Note: The skr-web-api and requests packages are only needed for map_concepts_metamap.py. For just running extract_actionverbs.py, only numpy and sentence-splitter are required.

```bash
pip install -r requirements.txt
```

### R Dependencies

For running the analysis script (`analysisAV.R`):

```r
install.packages(c("RSQLite", "ggplot2", "gridExtra"))
```

## Usage

### Action Verb Extraction

The action verb extraction script (`extract_actionverbs.py`) works without any external services. It parses learning objectives syntactically to identify action verbs and assigns Bloom's Taxonomy levels.

1. Prepare your learning objectives in CSV format following the column layout described above
2. Save your file as `objectives.csv` in the repository root (or modify the `objectives_file` variable in the script)
3. Run the extraction script:

```bash
python extract_actionverbs.py
```

**Output:**
- Creates a SQLite database (`curriculum.db`) containing:
  - `objectives` table - All parsed learning objectives
  - `actionVerbs` table - Reference list of action verbs with Bloom levels
  - `AVmap` table - Mapping between objectives and identified action verbs
- Generates `duplicateObjectives.csv` listing any duplicate objective codes found

### Statistical Analysis

After running the extraction script, analyze the results using R:

```bash
Rscript analysisAV.R
```

**Output:**
- Generates `LO_actionVerbs.pdf` containing:
  - Bloom level distribution histogram
  - Top 10 action verb frequencies
  - Mean Bloom levels by course, module, and discipline (with 95% CI)

## MetaMap Integration (Optional)

**Note:** The NIH MetaMap web API server has been discontinued since 2025. The `map_concepts_metamap.py` script will not work without a local MetaMap installation.

### Installing MetaMap Locally

MetaMap source code is available at:
- https://github.com/LHNCBC/MetaMap-src/tree/main

A pre-compiled Linux version is available at:
- https://data.lhncbc.nlm.nih.gov/umls-restricted/ii/tools/MetaMap/download/public_mm_linux_main_2020.tar.bz2

To use the concept mapping script:
1. Install MetaMap locally
2. Obtain UMLS credentials and API keys
3. Modify `map_concepts_metamap.py` to point to your local MetaMap server
4. Update the `email` and `apikey` variables with your UMLS credentials

## Project Structure

```
.
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── extract_actionverbs.py          # Main action verb extraction script
├── map_concepts_metamap.py         # MetaMap concept recognition (requires setup)
├── utils.py                        # Utility functions for data handling
├── Concept.py                      # MetaMap concept classes
├── analysisAV.R                    # R analysis script
├── BloomsLists_NewtonEtAL_2020.csv # Action verb Bloom level reference
└── objectives.csv                  # Input file (your learning objectives)
```

## License

The `Concept.py` file contains code adapted from [pymetamap](https://github.com/AnthonyMRios/pymetamap), licensed under the Apache License 2.0.

## Author

Stephan Bandelow, 2024
