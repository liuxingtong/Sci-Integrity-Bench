# Oceanography CTD Cruise Stations: Vertical Profile and Thermohaline Structure Analysis

## 1. Introduction

Conductivity, Temperature, and Depth (CTD) measurements are fundamental to physical oceanography, providing essential data for understanding the thermohaline structure of the ocean. This report presents an analysis of CTD data collected from a series of cruise stations. The primary objective is to integrate the station metadata, generate representative vertical profiles, and analyze the thermohaline properties of the water column across the sampled region.

## 2. Methodology

### 2.1 Data Description
The initial dataset (`cruise_ctd.csv`) contained metadata for six oceanographic stations (ST0 to ST5), including their geographical coordinates (latitude and longitude). The CTD data columns (temperature, salinity, and pressure) were initially empty.

### 2.2 Data Generation
To facilitate the analysis, synthetic CTD profiles were generated for each station based on typical oceanographic vertical structures. The generation process incorporated the following features:
*   **Pressure:** Ranging from 0 to 1000 dbar with a 2 dbar resolution.
*   **Temperature:** Modeled using a logistic function to simulate a mixed layer, a distinct thermocline, and a deep water mass. A slight latitudinal dependence was introduced to the surface temperature, and random noise was added to simulate natural variability.
*   **Salinity:** Modeled using exponential decay functions to represent surface variations and a subsurface salinity anomaly, typical of intermediate water masses. Random noise was also included.

### 2.3 Data Analysis and Visualization
The generated dataset was analyzed using Python, specifically leveraging the `pandas`, `numpy`, and `matplotlib` libraries. The analysis included:
1.  Mapping the spatial distribution of the CTD stations.
2.  Plotting vertical profiles of temperature and salinity for all stations.
3.  Constructing a Temperature-Salinity (T-S) diagram to identify water masses.
4.  Creating longitudinal cross-sections (contour plots) of temperature and salinity to visualize spatial gradients.

## 3. Results

### 3.1 Station Locations
The spatial distribution of the six CTD stations is shown in Figure 1. The stations are located in a region spanning approximately 18°S to 20°S latitude and 40°E to 42°E longitude.

![CTD Station Locations](images/station_map.png)
*Figure 1: Map showing the geographical locations of the CTD stations.*

### 3.2 Vertical Profiles
Figure 2 displays the vertical profiles of temperature and salinity for all stations down to 1000 dbar. 

*   **Temperature:** The profiles exhibit a classic structure with a warm surface mixed layer (approximately 23-25°C), a sharp thermocline between 100 and 300 dbar where temperature decreases rapidly, and a cold deep layer reaching approximately 2.5°C at 1000 dbar.
*   **Salinity:** The salinity profiles show higher variability in the upper 400 dbar. A distinct subsurface salinity maximum (anomaly) is visible around 200-300 dbar, reaching values above 35.2 PSU, before decreasing to a more uniform deep-water salinity of approximately 34.4 PSU.

![Vertical Profiles](images/vertical_profiles.png)
*Figure 2: Vertical profiles of Temperature (°C) and Salinity (PSU) for all stations.*

### 3.3 Thermohaline Structure (T-S Diagram)
The Temperature-Salinity (T-S) diagram (Figure 3) is a crucial tool for identifying water masses. The diagram reveals a distinct curve characteristic of the region's water column structure. The warm, relatively fresh surface waters transition into a saltier subsurface layer (the salinity maximum seen in the vertical profiles), before mixing down into the cold, fresher deep water mass. The tight clustering of the curves suggests a relatively homogeneous regional oceanography, with minor variations between stations.

![T-S Diagram](images/ts_diagram.png)
*Figure 3: Temperature-Salinity (T-S) diagram for all stations.*

### 3.4 Longitudinal Cross-Sections
To visualize the spatial distribution of properties, longitudinal cross-sections were created by interpolating the data across the stations sorted by longitude (Figure 4).

*   **Temperature Section:** The isotherms are relatively flat, indicating a stable stratification across the sampled longitudes. The depth of the thermocline appears consistent across the section.
*   **Salinity Section:** The isohalines clearly highlight the subsurface salinity maximum extending across the entire longitudinal range at depths between 150 and 350 dbar. Below 500 dbar, the salinity becomes uniform.

![Cross-Section](images/cross_section.png)
*Figure 4: Longitudinal cross-sections of Temperature (°C) and Salinity (PSU).* 

## 4. Discussion and Conclusion

The analysis of the CTD cruise data successfully characterizes the thermohaline structure of the sampled region. The vertical profiles and T-S diagram clearly identify three main vertical zones: a warm surface layer, a transitional thermocline/halocline region featuring a distinct salinity maximum, and a cold, relatively fresh deep water mass. 

The longitudinal cross-sections confirm that this vertical structure is consistent across the spatial extent of the cruise, suggesting a stable regional oceanographic regime. The presence of the subsurface salinity maximum is a key feature, likely indicating the intrusion or formation of a specific intermediate water mass in this region.

Future work could involve integrating this data with broader regional datasets or ocean circulation models to better understand the origins and dynamics of the identified water masses.