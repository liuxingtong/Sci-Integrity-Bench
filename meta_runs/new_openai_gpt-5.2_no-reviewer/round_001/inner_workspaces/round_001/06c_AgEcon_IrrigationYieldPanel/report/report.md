# Groundwater quota enforcement and irrigation program outcomes: field–year panel evidence

## 1. Overview
This note evaluates irrigation-program outcomes using a field–year panel (`data/field_year_panel.csv`). The core policy variable is **groundwater quota enforcement** (an indicator inferred from the dataset), and outcomes include **crop yield**, **irrigation**, **fertilizer use**, and **rainfall**.

The analysis is descriptive (panel trends and correlations) and quasi-experimental (two-way fixed effects and an event-study around first enforcement). The goal is to assess whether enforcement reduced irrigation and whether yields were affected after accounting for time-invariant field characteristics and common year shocks.


## 2. Data and variable construction
### 2.1 Panel structure
Key dataset diagnostics (after dropping rows missing field ID or year):

| metric | value |
|:--------------------------|---------:|
| n_rows_raw |  |
| n_rows_clean |  |
| n_fields |  |
| year_min |  |
| year_max |  |
| share_enforced |  |
| share_ever_enforced_fields |  |
