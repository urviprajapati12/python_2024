##  Create a visualization which includes

## - A selector for time interval included in the analysis

## - Consumption, bill, average price and average temperature over selected period

## - Selector for grouping interval 

## - Line graph of consumption, bill, average price and average temperature over the range selected using the grouping interval selected. 



##Price data is from here:  https://porssisahko.net/tilastot and the consumption data from energiatili.fi (requires personal login). If you like to use your own consumption data, feel free to do so!
##Porssisahko.net also allows API connection, but it is very slow. 



import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#open file
comsumption_data = pd.read_csv('new_2022-2024_consumption.csv',delimiter= ';')
new_price_data = pd.read_csv('new_sahkon-hinta-010121-231024.csv',delimiter= ';')
#display(comsumption_data.head())
#display(new_price_data.head())


#check datatype
#print('comsumption_data',type(comsumption_data['Time'][3]))
#print('new_price_data',type(new_price_data['Time'][3]))

#Change time format of both files to Pandas datetime
comsumption_data['Time'] = pd.to_datetime(comsumption_data['Time'], format = '%d.%m.%Y %H:%M' ,errors='coerce')
new_price_data['Time'] = pd.to_datetime(new_price_data['Time'], format='%d/%m/%Y %H.%M', errors='coerce').dt.round('h')

# display(comsumption_data.head())
# display(new_price_data.head())


# Replace commas with dots and convert to numeric for energy consumption
comsumption_data['Energy(kWh)'] = comsumption_data['Energy(kWh)'].str.replace(',', '.').astype(float)

new_price_data['Price (cent/kWh)']  = new_price_data['Price (cent/kWh)'].str.replace(',', '.').astype(float)

comsumption_data['Temperature'] = comsumption_data['Temperature'].str.replace(',', '.').astype(float)

# print('Show')
# display(comsumption_data['Energy(kWh)'])

# Merge the datasets on the 'Time' column
data_merge = pd.merge(comsumption_data, new_price_data, on='Time', how='outer')

# print('data_merge')
# display(data_merge)


# Calculate the hourly bill (convert price from cents to euros)
data_merge['Hourly Bill (€)'] = data_merge['Energy(kWh)'] * (data_merge['Price (cent/kWh)'] / 100)

# Ensure the relevant columns are numeric, handling any conversion issues
data_merge['Energy(kWh)'] = pd.to_numeric(data_merge['Energy(kWh)'], errors='coerce')
data_merge['Price (cent/kWh)'] = pd.to_numeric(data_merge['Price (cent/kWh)'], errors='coerce')
data_merge['Hourly Bill (€)'] = pd.to_numeric(data_merge['Hourly Bill (€)'], errors='coerce')
data_merge['Temperature'] = pd.to_numeric(data_merge['Temperature'], errors='coerce')



# Title for the Streamlit app
st.title("Electricity Consumption Analysis")


# 1. Selector for time interval
start_date = pd.to_datetime("1-04-2022",format = '%d-%m-%Y',errors='coerce')
end_date = pd.to_datetime("1-10-2024",format = '%d-%m-%Y',errors='coerce')

#st.write('Start time:')
input_start_date = st.text_input('Start time:',start_date.strftime ('%Y/%m/%d'))
#st.write('End time:')
input_end_date = st.text_input('End time:',end_date.strftime ('%Y/%m/%d'))

st.write('Showing range:' ,start_date.date(), '-', end_date.date())


#Filter data with date range
filtered_data = data_merge[(data_merge['Time'] >= input_start_date) & (data_merge['Time'] <= input_end_date)]




# Function to resample data by the specified frequency
def resample_data(data_merge, frequency):
    return data_merge.groupby(pd.Grouper(freq=frequency, key='Time')).agg({
        'Energy(kWh)': 'sum',
        'Hourly Bill (€)': 'sum',
        'Price (cent/kWh)': 'mean',
        'Temperature': 'mean'
    }).reset_index()

st.write('Total consumption over the period:', round(filtered_data['Energy(kWh)'].sum()),'kWh')
st.write('Total Bill over the period:', round(filtered_data['Hourly Bill (€)'].sum()),'£')
st.write('Average hourly price:', round(filtered_data['Price (cent/kWh)'].mean()),'cents')
st.write('Average paid price:', round((filtered_data['Hourly Bill (€)'].sum() / filtered_data['Energy(kWh)'].sum() * 100)), 'cents')



# Selector for grouping interval (Daily, Weekly, Monthly)
group_interval = st.selectbox("Average period:", ['Daily', 'Weekly', 'Monthly'])

# Map the selected interval to Pandas resample rules
if group_interval == 'Daily':
    resample_rule = 'D'
elif group_interval == 'Weekly':
    resample_rule = 'W'
else:
    resample_rule = 'Me'




# Resample the data based on the selected interval
grouped_data = resample_data(filtered_data, resample_rule)




def plot_with_custom_y(data, y_column, y_label, y_min=None, y_max=None):
    fig,ax = plt.subplots(figsize=(10, 3))
    
    ax.plot(data['Time'] , data[y_column], label=y_label, color='tab:blue', linewidth=1)
    
    # Set the  labels
    ax.set_xlabel('Time', fontsize=12,labelpad=15)
    ax.set_ylabel(y_label, fontsize=12,labelpad=15)

    # Set major ticks for each quarter (January, April, July, October) for month display
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))  # Display only month names
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[ 4, 7, 10]))
    
    ax.xaxis.set_minor_locator(mdates.YearLocator())
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%Y'))
    

    # Add end-of-year labels
    

    # Customize tick appearance and padding
    ax.tick_params(axis='x', which='major',labelsize=10, pad=0)  # Space for month labels
    ax.tick_params(axis='x', which='minor', pad=0, labelsize=10)  # Space for year labels

    

    # Remove the top, right, left, and bottom spines (border) around the plot
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Set grid with subtle lines
    ax.grid(visible=True, which='both', axis='y', color='lightgrey', alpha=0.7)
    
    ax.set_ylim(y_min, y_max)  # Set custom y-axis range
   

    
    st.pyplot(fig)

# Display line charts for each metric using Streamlit

#st.line_chart(grouped_data,x='Time',y='Energy(kWh)', y_label='Electricity Consumption[kWh]', x_label='Time')
plot_with_custom_y(grouped_data, 'Energy(kWh)', 'Electricity Consumption[kWh]', y_min=0,y_max=400)


#st.line_chart(grouped_data,x='Time',y='Price (cent/kWh)', y_label='Electricity Bill [€]', x_label='Time')
plot_with_custom_y(grouped_data, 'Hourly Bill (€)',  'Electricity Bill [€]', y_min=0,y_max=40)


#st.line_chart(grouped_data,x='Time',y='Hourly Bill (€)', y_label='Electricity Price [cents]', x_label='Time')
plot_with_custom_y(grouped_data, 'Price (cent/kWh)',  'Electricity Price [cents]', y_min=-20,y_max=100)


#st.line_chart(grouped_data,x='Time',y='Temperature', y_label='Temperature [°C]', x_label='Time')
plot_with_custom_y(grouped_data, 'Temperature',  'Temperature [°C]', y_min=-30, y_max=30)








