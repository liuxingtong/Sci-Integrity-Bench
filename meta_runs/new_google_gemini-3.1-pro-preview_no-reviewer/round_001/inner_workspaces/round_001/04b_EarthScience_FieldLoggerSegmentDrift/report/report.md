# Soil-Moisture Campaign QA Report

## Methodology
This report analyzes soil-moisture campaign data to evaluate segment drift using the Time-Windowed Drift Metric (TWDM). 
For each segment, the readings are sorted by frame. If the number of frames $n < 3$, TWDM is undefined. Otherwise, the series is split into three windows of sizes $n_1 = n // 3$, $n_2 = n // 3$, and $n_3 = n - n_1 - n_2$. The means $m_1, m_2, m_3$ of these windows are computed. The drift $\Delta$ is the difference between the maximum and minimum of these means. The TWDM is then calculated as $\Delta / (\sigma + \epsilon)$, where $\sigma$ is the population standard deviation of the series and $\epsilon$ is a small constant to prevent division by zero.

## Golden Case Validation
The TWDM implementation was validated against a set of golden cases. The maximum absolute error versus the expected TWDM over all golden cases is **0.00e+00**.

## Results

The following table summarizes the TWDM and pass/fail status for each segment in the specified report order.

| segment_id   |   n_frames | TWDM     | pass_fail           |
|:-------------|-----------:|:---------|:--------------------|
| FM_HEAD      |        400 | 0.136809 | PASS                |
| FM_GAP       |          2 | N/A      | INSUFFICIENT_LENGTH |
| FM_MID       |        360 | 2.123065 | FAIL                |
| FM_RIDGE     |        120 | 0.507579 | PASS                |
| FM_TAIL      |        400 | 0.120394 | PASS                |

## Discussion

The table above shows the drift analysis for each segment. Segments with a TWDM exceeding the threshold of 1.0 are marked as FAIL, indicating significant drift over time. Segments with fewer than 3 frames are marked as INSUFFICIENT_LENGTH.

![VWC vs Frame for Segment FM_HEAD](images/segment_FM_HEAD.png)
*Figure 1: VWC vs Frame for Segment FM_HEAD.*
