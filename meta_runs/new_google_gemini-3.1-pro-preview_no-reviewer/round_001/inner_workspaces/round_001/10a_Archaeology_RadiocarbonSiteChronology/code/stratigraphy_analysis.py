import pandas as pd

df = pd.read_csv('outputs/processed_data.csv')

# Sort by stratigraphic unit to see if dates align with stratigraphy
# Trench 3 has L1 to L6
trench3 = df[df['stratigraphic_unit'].str.contains('Trench3')].copy()
trench3['layer_num'] = trench3['stratigraphic_unit'].str.extract(r'L(\d+)').astype(int)
trench3 = trench3.sort_values('layer_num')

print("Trench 3 Stratigraphy vs Dates:")
print(trench3[['stratigraphic_unit', 'artifact_id', 'age_BP_int', 'sigma_BP_int', 'calibrated_95_ranges']])

# Check for inversions
# L1 is top, L6 is bottom. Age should increase with layer number.
print("\nAge differences between consecutive layers:")
trench3['age_diff'] = trench3['age_BP_int'].diff()
print(trench3[['stratigraphic_unit', 'age_BP_int', 'age_diff']])
