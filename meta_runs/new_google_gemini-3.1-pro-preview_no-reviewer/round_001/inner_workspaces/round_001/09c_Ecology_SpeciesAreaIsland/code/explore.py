import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/island_species.csv')
print(df.describe())

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
sns.histplot(df['area_km2'], kde=True)
plt.title('Distribution of Area')

plt.subplot(1, 2, 2)
sns.histplot(df['species_richness'], kde=True)
plt.title('Distribution of Species Richness')

plt.tight_layout()
plt.savefig('outputs/distributions.png')
plt.close()
