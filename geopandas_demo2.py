# Code adapted from: https://github.com/yohman/getting-started-with-gis (click on the file "Intro to GIS.ipynb")
# This code is explained in the workshop here: https://www.youtube.com/watch?v=rrGw6ct-Cbw

# Before running this code on Windows, I needed to install the geopandas and contextily packages.
# I failed to do this with pip and was only able to do it after installing Anaconda
# and using the conda package manager. Instructions for Windows 10:

# 1) Download and install Anaconda individual edition: https://www.anaconda.com/products/individual
# 2) Install geopandas in a virtual environment (instructions at https://geopandas.org/en/stable/getting_started/install.html)
#   a) Open Anaconda Prompt
#   b) Run these commands:

#    conda update -n base -c defaults conda
#    conda create -n geo_env
#    conda activate geo_env
#    conda config --env --add channels conda-forge
#    conda config --env --set channel_priority strict
#    conda install python=3 geopandas

# 3) Install contextily in the virtual environment with the commmand below (also in Anaconda Prompt):
    
#    conda install -c conda-forge contextily

# 4) Change environment to geo_env by clicking "Change default environment in Preferences..." within Spyder
#    and finding the path corresponding to geo_env under "Use the following Python interpreter"
# 5) Go to Consoles --> Restart kernel
# 6) Run the program. You shouldn't get any errors when importing the packages.

# If the kernel won't start, switch to default environment, exit Spyder, start again, switch to geo_env, restart kernel.

# Getting needed libraries

# to read and visualize spatial data
import geopandas as gpd

# to provide basemaps
#import contextily as ctx

# to give more power to your figures (plots)
import matplotlib.pyplot as plt

from itertools import combinations

def topn( n ):
    # Getting data as a .geojson file:
    # 1) Go to censusreporter.org
    # 2) Type in "Walworth County" in the "Profile" field and select Walworth County Wisconsin
    # 3) Type a variable such as population in the "Find data for this place" field and select "Table B01003 Total Population"
    # 4) On the left under "Divide Walworth County, WI into …" select "county subdivisions"
    # 5) Click on the top right "Download data" and select "GeoJSON"
    # 6) Extract the file in the zipped archive into the same directory as this program.
    # 7) I renamed the folder "acs2019_5yr_B01003_06000US5512719475" to "data", it contains a two files:
    #             "acs2019_5yr_B01003_06000US5512719475.geojson" and "metadata.json"
    
    #Import the .geojson file. I don't really care about the variables in this dataset, I just want the polygon data of each municipality. I'm going to add additional variables from a spreadsheet:
    gdf1 = gpd.read_file('data/acs2019_5yr_B01003_06000US5512719475.geojson')
    
    # Delete the first row, since it contains data for the entire county:
    # drop the row with index 0 (i.e. the first row)
    gdf1 = gdf1.drop([0])
    
    # Check out the column names:
    print( gdf1.columns )   
    
    # Import other data from spreadsheet:
    gdf2 = gpd.read_file('data/myvariables.csv')
    
    # Check out the column names:
    print( gdf2.columns )
    
    # Merge the data on the name column    
    gdf = gpd.GeoDataFrame( gdf1.merge(gdf2, on='name') )
        
    # Set the geometry to use the polygons from the original geojson file:
    gdf = gdf.set_geometry('geometry_x')    
    
    # Calculate need using the weighted model    
    # and add to table as a new column
    X = "Below 200% FPL"
    Y = "Having no health insurance"
    gdf[X] = gdf[X].astype('float')
    gdf[Y] = gdf[Y].astype('float')
    w = 1
    needs = []
    gdf['Weighted need'] = [0]*len(gdf)
    for i in range( len( gdf ) ):
        needs.append( w*gdf[X][i]+(1-w)*gdf[Y][i] )
    gdf['Weighted need'] = needs
    
    # Set this as the column to be plotted
    curcol = 'Weighted need'
    
    # If desiring to plot the last column in the excel sheet (after converting to float):    
    #est = 'Estimated percentage under 200% FPL with no health insurance'
    #gdf[est] = gdf[est].astype('float')
    #curcol = est   
    
    # Copy the data frame, sort by the column to be plotted, and remove all but the top n (so that we can highlight the top n at the very end)
    #n = 20
    gdf3 = gdf.set_geometry('geometry_x')
    gdf3 = gdf3.sort_values( curcol, ascending=False)
    curcolsorted = []
    for row in gdf3.iterrows():
        curcolsorted.append( row[1][curcol])
    gdf3 = gdf3[gdf3[curcol] >= curcolsorted[n-1]]
    
    # Plot the data
    fig, ax = plt.subplots(figsize = (12,10)) 
    gdf.plot(column=curcol, legend=True,  legend_kwds={'label': curcol,                        'orientation': "vertical"}, cmap='OrRd', ax=ax);
    # Highlight the boundary of the top n
    gdf3.boundary.plot(  ax=ax);
    
    # Label by municipality
    gdf3.apply(lambda x: ax.annotate(text=x['name'].split(",")[0], xy=x.geometry_x.centroid.coords[0], ha='center'), axis=1);    
    
    ################################

def mclp1( n = 5, r = 10000, colname = "need1" ):
    # n is the number of clinics
    # r is the threshold for mclp in meters. all munis are less than 30000m from elkhorn so this defaults to a third of that.
    
    
    #Import the .geojson file. I don't really care about the variables in this dataset, I just want the polygon data of each municipality. I'm going to add additional variables from a spreadsheet:
    gdf1 = gpd.read_file('data/acs2019_5yr_B01003_06000US5512719475.geojson')
    
    # Delete the first row, since it contains data for the entire county:
    # drop the row with index 0 (i.e. the first row)
    gdf1 = gdf1.drop([0])
    
     # Get the data from file. Assume need is in second column
    gdf2 = gpd.read_file('data/mclpneed.csv')
    
    # Check out the column names:
    #print( gdf2.columns )
    #return
    
    # Merge the data on the name column    
    gdf = gpd.GeoDataFrame( gdf1.merge(gdf2, on='name') )
        
    # Set the geometry to use the polygons from the original geojson file:
    gdf = gdf.set_geometry('geometry_x')
    
    # Get the centroids
    centroids = gdf.geometry_x.to_crs('+proj=cea').centroid#.to_crs( gdf.geometry_x.crs)
    gdf['centroid']= centroids
    
    # Find the distance between two centroids
    d =  centroids[4].distance( centroids[5] )
    print( d )
    
    # Print distances from lake geneva to whitewater city
    print( gdf["name"][14], gdf["name"][26] )
    print( centroids[14].distance( centroids[26] ) )
        
    #print( len( centroids ) )
     
    # Create distance matrix
    #mat = []
    #for i in range( len( centroids )):
    #    mat.append( list( centroids.distance( centroids[i] ) ) )
        
    #print( mat )
    
    # print need
    # print( gdf["need"] )
            
    # range over possible locations, calculate need
    maxneed = 0
    bestloc = None
    bestcovered = {}
    bestdistances = []
    for locs in combinations(range( len( centroids )), n):
        #print( locs )
        need = 0
        dists = []
        covered = {}
        for i in locs:
            dist = centroids.distance( centroids[ i ] )
            #print( dist )
            dists.append( dist )
            
        for j in range( len( gdf[colname] ) ):
            for k in range( n ):
                if dists[k][j] <= r:
                    #print( gdf["need"][j] )
                    need += float( gdf[colname][j] )
                    covered[gdf["name"][j].split(",")[0]]=gdf[colname][j]
                    #print( gdf["name"][j].split(",")[0], "with need", gdf["need"][j])
                    break
        
        #print( "total need", need )
        if need > maxneed:
            #print( "Found better locs", need, locs)
            maxneed = need
            bestloc = locs
            bestcovered = covered
            bestdistances = dists
        
    print( "\nFinal:", maxneed, bestloc, bestcovered, "\n" )
    
    #return
        
        
    gdf4 = gdf.set_geometry('geometry_x')
    gdf4 = gdf4.sort_values( colname, ascending=False)
    curcolsorted = []
    for row in gdf4.iterrows():
        curcolsorted.append( row[1][colname])
    gdf4 = gdf4[gdf4[colname] >= curcolsorted[3-1]]

    
    # Set this as the column to be plotted
    #curcol = 'need'
    
    # Copy the data frame and highlight the chosen locations
    #m = 20
    gdf3 = gdf.set_geometry('geometry_x')
    #gdf3 = gdf3.sort_values( curcol, ascending=False)
    #curcolsorted = []
    #for row in gdf3.iterrows():
    #    curcolsorted.append( row[1][curcol])
    if n > 0:
        gdf3 = gdf3.iloc[list(bestloc)]
    #print( gdf3['need'] )

    # Plot the data
    fig, ax = plt.subplots(figsize = (12,10)) 
    gdf.plot(column=colname, legend=False, categorical=True,   legend_kwds={"loc": "center left", "bbox_to_anchor": (1, 0.5)}, cmap='OrRd', ax=ax);
    #legend_kwds={'label': curcol,                        'orientation': "vertical"}
    #gdf.plot(column=colname, legend=True, legend_kwds={'label': colname,                        'orientation': "vertical"}, cmap='OrRd', ax=ax);
    
    #ax.plot([1, 2, 3], label='Inline label')
    #ax.legend(gdf[colname])
    
    #"labels":list(range(len(gdf["name"]))),
    #ax.legend(gdf["name"])
    #  ,'orientation': "vertical"
    # Highlight the boundary of the top n
    
    # plot centroids
    #gdf.geometry_x.centroid.plot( ax = ax, color='blue', markersize=40)
    
    gdf.geometry_x.to_crs('+proj=cea').centroid.to_crs( gdf.geometry_x.crs).plot( ax = ax, color='blue', markersize=40)
    
    # plot coverage radius for solution
    # conversion ratio: 39885m is approximately 419000 marker size
    #gdf3.geometry_x.to_crs('+proj=cea').centroid.to_crs( gdf.geometry_x.crs).plot( ax = ax, color='green', markersize=r*419000/(2*39885), alpha=.5)
    
    if n > 0:
        gdf3.geometry_x.to_crs('+proj=cea').centroid.to_crs( gdf.geometry_x.crs).buffer( r/100000*1.12 ).plot( ax = ax, color='green', alpha=.5)
    
    

    
    #plot boundaries solution
    gdf.boundary.plot(  ax=ax);
    
    # Label by municipality
    gdf.apply(lambda x: ax.annotate(text=x['name'].split(",")[0], fontsize = 'small', fontweight = "bold", xy=x.geometry_x.centroid.coords[0], ha='center'), axis=1); 
    
    plt.axis("off")
    
    # Label all centroids with a .
    #gdf.plot(column = 'centroid', ax=ax);
    #gdf.apply(lambda x: ax.annotate(text='.', xy=x.geometry_x.centroid.coords[0], ha='center'), axis=1); 
   
    #ax.plot('o', data = centroids)
    
def plotcentroids():
    gdf1 = gpd.read_file('data/acs2019_5yr_B01003_06000US5512719475.geojson')
    
    # Delete the first row, since it contains data for the entire county:
    # drop the row with index 0 (i.e. the first row)
    gdf1 = gdf1.drop([0])
    
    # Import other data from spreadsheet:
    gdf2 = gpd.read_file('data/myvariables.csv')
    
    
    # Merge the data on the name column    
    gdf = gpd.GeoDataFrame( gdf1.merge(gdf2, on='name') )
    
    # Set the geometry to use the polygons from the original geojson file:
    gdf = gdf.set_geometry('geometry_x')
    
    # plot centroids
    
    
    # Plot the data
    fig, ax = plt.subplots(figsize = (12,10)) 
    #plot boundaries of mclp solution
    gdf.boundary.plot(  ax=ax);
    gdf.geometry_x.centroid.plot( ax = ax, color='blue', markersize=40)
    
    plt.axis("off")
    
    # Label by municipality
   # gdf.apply(lambda x: ax.annotate(text=x['name'].split(",")[0], xy=x.geometry_x.centroid.coords[0], ha='center'), axis=1); 
    
    
def countyplot():
    gdf1 = gpd.read_file('data/acs2019_5yr_B01003_06000US5512719475.geojson')
    
    # Delete the first row, since it contains data for the entire county:
    # drop the row with index 0 (i.e. the first row)
    gdf1 = gdf1.drop([0])
    
    # Import other data from spreadsheet:
    gdf2 = gpd.read_file('data/myvariables.csv')
    
    
    # Merge the data on the name column    
    gdf = gpd.GeoDataFrame( gdf1.merge(gdf2, on='name') )
    
    # Set the geometry to use the polygons from the original geojson file:
    gdf = gdf.set_geometry('geometry_x')
    
    # Plot the data
    fig, ax = plt.subplots(figsize = (12,10)) 
    #plot boundaries of mclp solution
    gdf.boundary.plot(  ax=ax);
    
    plt.axis("off")
    
    # Label by municipality
    gdf.apply(lambda x: ax.annotate(text=x['name'].split(",")[0], xy=x.geometry_x.centroid.coords[0], ha='center'), axis=1); 
    
    
def delavanplot():
    gdf1 = gpd.read_file('data/acs2019_5yr_B01003_06000US5512719475.geojson')
    
    # Delete the first row, since it contains data for the entire county:
    # drop the row with index 0 (i.e. the first row)
    gdf1 = gdf1.drop([0])
    
    # Import other data from spreadsheet:
    gdf2 = gpd.read_file('data/delavanonly.csv')
    
    
    # Merge the data on the name column    
    gdf = gpd.GeoDataFrame( gdf1.merge(gdf2, on='name') )
    
    # Set the geometry to use the polygons from the original geojson file:
    gdf = gdf.set_geometry('geometry_x')
    
    # Plot the data
    fig, ax = plt.subplots(figsize = (12,10)) 
    #plot boundaries of mclp solution
    gdf.boundary.plot(  ax=ax);
    
    plt.axis("off")
    
    # Label by municipality
    gdf.apply(lambda x: ax.annotate(text=x['name'].split(",")[0], fontsize = 20, fontweight = "bold", xy=x.geometry_x.centroid.coords[0], ha='center'), axis=1); 
    
def equivclinics():
    gdf1 = gpd.read_file('data/acs2019_5yr_B01003_06000US5512719475.geojson')
    
    # Delete the first row, since it contains data for the entire county:
    # drop the row with index 0 (i.e. the first row)
    gdf1 = gdf1.drop([0])
    
    # Import other data from spreadsheet:
    gdf2 = gpd.read_file('data/myvariables.csv')
    
    
    # Merge the data on the name column    
    gdf = gpd.GeoDataFrame( gdf1.merge(gdf2, on='name') )
    
    # Set the geometry to use the polygons from the original geojson file:
    gdf = gdf.set_geometry('geometry_x')
    
    # Plot the data
    fig, ax = plt.subplots(figsize = (12,10)) 
    #plot boundaries of mclp solution
    gdf.boundary.plot(  ax=ax);
    
    plt.axis("off")
    
    # Label by municipality
    gdf.apply(lambda x: ax.annotate(text=x['lab2'], fontsize = 40, fontweight = "bold", xy=x.geometry_x.centroid.coords[0], ha='center'), axis=1); 
    

def main():
    #delavanplot()
    #topn( 5 )
    mclp1( n = 3, r = 4500, colname = "need1" )
    #equivclinics()
    #plotcentroids()
main()

