import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import calendar
import numpy as np
from datetime import datetime, timedelta, date
import io

st.set_page_config(layout="wide", page_title="Sprint Calendar Visualizer")

def parse_sprint_data(text):
    """Parse sprint data from text input."""
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    # Skip the header line
    data_lines = lines[1:]
    
    sprints = []
    for line in data_lines:
        parts = line.split()
        if len(parts) >= 3:
            sprint_name = parts[0]
            start_date = parts[1]
            end_date = parts[2]
            
            sprints.append({
                'Sprint': sprint_name,
                'Start Date': pd.to_datetime(start_date),
                'End Date': pd.to_datetime(end_date)
            })
    
    return pd.DataFrame(sprints)

def generate_wall_calendar(df):
    """Generate a wall-style calendar visualization of sprints."""
    if df.empty:
        return None
    
    # Get the min and max dates to determine the calendar range
    min_date = df['Start Date'].min()
    max_date = df['End Date'].max()
    
    # Get the range of months to display
    start_month = (min_date.year, min_date.month)
    end_month = (max_date.year, max_date.month)
    
    # Generate list of all months to display
    months_to_display = []
    current_year, current_month = start_month
    while (current_year, current_month) <= end_month:
        months_to_display.append((current_year, current_month))
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    # Determine the grid layout
    num_months = len(months_to_display)
    cols = min(3, num_months)  # Maximum 3 columns
    rows = (num_months + cols - 1) // cols
    
    # Create figure with appropriate size
    fig = plt.figure(figsize=(5*cols, 4*rows))
    
    # Create a GridSpec layout for the months
    gs = gridspec.GridSpec(rows, cols, figure=fig)
    
    # Day names for the header (shortened)
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Generate colors for each sprint
    colors = plt.cm.tab10(np.linspace(0, 1, len(df)))
    sprint_colors = {row['Sprint']: colors[i] for i, (_, row) in enumerate(df.iterrows())}
    
    # Create calendar for each month
    for i, (year, month) in enumerate(months_to_display):
        row = i // cols
        col = i % cols
        
        # Create subplot
        ax = fig.add_subplot(gs[row, col])
        
        # Set month title
        month_name = calendar.month_name[month]
        ax.set_title(f"{month_name} {year}", fontweight='bold', fontsize=14)
        
        # Remove axis spines
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Get the calendar information for this month
        cal = calendar.monthcalendar(year, month)
        
        # Create a table for the calendar
        # First row is for day names
        cell_text = [[day_names[day] for day in range(7)]]
        
        # Add the day numbers from the calendar
        for week in cal:
            # Replace zeros with empty strings (days not in this month)
            cell_text.append(['' if day == 0 else str(day) for day in week])
        
        # Create the table
        table = ax.table(
            cellText=cell_text,
            loc='center',
            cellLoc='center',
            bbox=[0, 0, 1, 0.85]  # Position the table within the subplot
        )
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        
        # Style the day names row
        for j in range(7):
            table[(0, j)].set_text_props(weight='bold')
            table[(0, j)].set_facecolor('#e6e6e6')
        
        # Highlight weekends
        for week_idx in range(1, len(cell_text)):
            for day_idx in [5, 6]:  # Saturday and Sunday
                if cell_text[week_idx][day_idx]:  # If the cell has a day number
                    table[(week_idx, day_idx)].set_facecolor('#f2f2f2')
        
        # Get the days that belong to each sprint for this month
        for _, sprint in df.iterrows():
            sprint_name = sprint['Sprint']
            sprint_start = sprint['Start Date']
            sprint_end = sprint['End Date']
            
            # For each day in the month
            for week_idx, week in enumerate(cal, 1):  # Start from index 1 as row 0 is for day names
                for day_idx, day in enumerate(week):
                    if day == 0:  # Skip days not in this month
                        continue
                    
                    # Check if this day is in the sprint
                    current_date = date(year, month, day)
                    if sprint_start.date() <= current_date <= sprint_end.date():
                        # Color the cell based on the sprint
                        cell = table[(week_idx, day_idx)]
                        cell.set_facecolor(sprint_colors[sprint_name])
                        
                        # Adjust text color for better visibility
                        if np.mean(sprint_colors[sprint_name][:3]) < 0.5:  # If color is dark
                            cell.get_text().set_color('white')
        
        # Hide axes
        ax.axis('off')
    
    # Add a legend for sprints
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=sprint_colors[sprint]) 
                     for sprint in sprint_colors]
    fig.legend(legend_handles, sprint_colors.keys(), 
              loc='lower center', bbox_to_anchor=(0.5, 0), 
              ncol=min(5, len(sprint_colors)), title="Sprints")
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # Make room for the legend
    
    return fig

# App title and description
st.title("Sprint Calendar Visualizer")
st.write("Input your sprint schedule below to visualize it in a wall calendar format.")

# Sample data for demonstration
sample_data = """Sprint Name Start Date End Date
0 2025-03-10 2025-03-21
1 2025-03-24 2025-04-11
2 2025-04-14 2025-05-02"""

# User input area
user_input = st.text_area("Enter your sprint schedule (format: Sprint Name, Start Date, End Date):", 
                         value=sample_data, height=150)

# Parse button
if st.button("Generate Calendar"):
    sprint_df = parse_sprint_data(user_input)
    
    # Show the parsed data
    st.subheader("Parsed Sprint Data")
    st.dataframe(sprint_df)
    
    # Generate and show the calendar visualization
    st.subheader("Sprint Calendar Visualization")
    fig = generate_wall_calendar(sprint_df)
    if fig:
        st.pyplot(fig)
        
        # Add download button for the calendar
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        st.download_button(
            label="Download Calendar Image",
            data=buffer,
            file_name="sprint_calendar.png",
            mime="image/png"
        )
    else:
        st.error("Could not generate calendar. Please check your input format.")

# Additional customization options
st.sidebar.header("Customization Options")
st.sidebar.write("(Future enhancement: Add color schemes, display options, etc.)")

# Instructions
with st.expander("How to Use"):
    st.write("""
    1. Enter your sprint schedule in the text area. Use the format:
       ```
       Sprint Name Start Date End Date
       0 2025-03-10 2025-03-21
       1 2025-03-24 2025-04-11
       ```
    2. Click "Generate Calendar" to visualize your sprints.
    3. Download the calendar image if needed.
    
    Notes:
    - Dates should be in YYYY-MM-DD format
    - Each sprint should be on a new line
    - The calendar shows each month separately in a traditional wall calendar style
    - Weekends are lightly shaded
    - Days that belong to sprints are colored according to the sprint
    """) 