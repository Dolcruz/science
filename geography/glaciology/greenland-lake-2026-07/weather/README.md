# Weather near the Greenland lake

At the KAN_M automatic weather station, 15.38 km from the lake centroid, every hourly upper-sensor air temperature between 10:00 UTC on 22 July and 14:00 UTC on 23 July 2026 was above freezing. The 29 readings ranged from +0.26 to +2.22 °C and averaged +1.12 °C. These measurements describe regional air conditions during the satellite observation gap. Temperature and ice formation can differ at the lake.

The hourly CSV preserves the public PROMICE/GC-Net measurements for 16–27 July and includes GPS coordinates, radiation and wind speed. The source file records the exact subset query, time origin and variable metadata. The script calculates distance on the WGS84 ellipsoid. Install Python with requests, numpy, pandas and pyproj and run `python weather.py` in this directory to retrieve the series and regenerate the summary. [GEUS hourly data for KAN_M](https://thredds.geus.dk/thredds/dodsC/aws/l3sites/netcdf/hour/KAN_M_hour.nc.html)
