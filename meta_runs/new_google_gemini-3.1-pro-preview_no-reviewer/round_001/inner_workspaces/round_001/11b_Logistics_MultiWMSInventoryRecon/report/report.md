# Inventory Reconciliation Report: WMS Alpha vs. WMS Beta

## 1. Introduction
This report presents the reconciliation of inventory data between two Warehouse Management Systems (WMS): Alpha and Beta. The objective is to identify discrepancies in inventory records, summarize Key Performance Indicators (KPIs) for management, and provide actionable insights to improve data consistency across systems.

## 2. Methodology
### 2.1 Data Sources
- **WMS Alpha (`wms_alpha.csv`)**: Contains inventory records with columns `sku`, `qty`, `warehouse`, and `as_of_utc`.
- **WMS Beta (`wms_beta.csv`)**: Contains inventory records with columns `SKU`, `Quantity`, `Site`, and `timestamp_local`.

### 2.2 Data Standardization and Preprocessing
To enable accurate comparison, the datasets were standardized:
- **Column Mapping**: Beta's `SKU`, `Quantity`, and `Site` were mapped to Alpha's `sku`, `qty`, and `warehouse`.
- **Site Mapping**: Beta's site `Warehouse-01` was mapped to Alpha's warehouse `WH1`.
- **Date Alignment**: Timestamps were converted to dates. Alpha's `as_of_utc` and Beta's `timestamp_local` were truncated to their respective dates for daily reconciliation.

### 2.3 Reconciliation Logic
The standardized datasets were merged using a full outer join on `sku`, `warehouse`, and `date`. Discrepancies were calculated as the difference in quantity between Alpha and Beta (`qty_alpha` - `qty_beta`). A record was considered a "match" if the difference was zero.

## 3. Results and KPIs
### 3.1 Key Performance Indicators (KPIs)
The reconciliation process yielded the following KPIs:
- **Total Records Evaluated**: 2
- **Matched Records**: 1
- **Match Rate**: 50.00%
- **Records Missing in Beta**: 1
- **Records Missing in Alpha**: 0

### 3.2 Discrepancy Analysis
The analysis revealed a discrepancy on 2026-03-02. While WMS Alpha reported a quantity of 10 for SKU A-1 at WH1, WMS Beta had no corresponding record for this date. The records for 2026-03-01 matched perfectly with a quantity of 10 in both systems.

### 3.3 Visualizations
The following figures illustrate the inventory comparison and discrepancies:

![Inventory Quantity Comparison](images/qty_comparison.png)
*Figure 1: Comparison of inventory quantities between WMS Alpha and WMS Beta by date.*

![Inventory Difference](images/qty_difference.png)
*Figure 2: Difference in inventory quantities (Alpha - Beta) by date.*

## 4. Discussion and Recommendations
The 50% match rate is primarily driven by missing data in WMS Beta for 2026-03-02. The exact match on 2026-03-01 suggests that the systems are capable of alignment, but there may be issues with data synchronization, batch processing delays, or missing exports from WMS Beta on subsequent days.

**Recommendations for Management:**
1. **Investigate Data Export Processes**: Verify if the export job for WMS Beta failed or was delayed on 2026-03-02.
2. **Timezone Standardization**: Ensure both systems log timestamps in a unified timezone (e.g., UTC) to prevent potential date-boundary mismatches in the future.
3. **Automated Daily Reconciliation**: Implement an automated daily reconciliation script based on this methodology to proactively identify and alert on discrepancies.
