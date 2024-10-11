import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib_inline
import seaborn as sns
import streamlit as st
from pathlib import Path


# Global plotting settings
matplotlib_inline.backend_inline.set_matplotlib_formats('svg')
sns.set_theme(style='whitegrid')
    

def set_output_dir(dir_name: str = './output'):
    output_dir = Path(dir_name)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    return output_dir    
    
# Output folder
output_dir = set_output_dir()


def get_color_mapping(column: str) -> dict:
    """
    Different color maps for plotting
    """
    # Okabe ito color map for categorial data: https://clauswilke.com/dataviz/color-basics.html#ref-Okabe-Ito-CUD 
    cmap_okabe_ito = {
        'Workshop': '#E69F00',           
        'Lehrveranstaltung': '#56B4E9', 
        'Interne Veranstaltung': '#009E73',
        'Veranstaltung': '#F0E442',     
        'Führung': '#0072B2',
    }
    
    # ColorBrew map for qualitative data (colorblind safe): https://colorbrewer2.org/?type=qualitative&scheme=Paired&n=4 
    cmap_cbrew = {
        'Uni': '#a6cee3',
        'UB': '#1f78b4',
        'Extern': '#b2df8a',
        'Studis': '#33a02c'
    }
    
    # ColorBrew map for qualitative data: https://colorbrewer2.org/?type=qualitative&scheme=Set2&n=6
    cmap_cbrew_equip = {
        'equip_monitor': '#66c2a5',
        'equip_clevertouch': '#fc8d62',
        'equip_vr': '#8da0cb',
        'equip_eyetracking': '#e78ac3',
        'equip_dt': '#a6d854',
        'equip': '#ffd92f'
    }

    if column == 'event_category':
        return cmap_okabe_ito  
    
    elif column == 'organiser':
        return cmap_cbrew
    
    elif column in ['equip']:
        return cmap_cbrew_equip


def create_img_title(title: str):
    return re.sub(r'[\s\W]+', '_', title.lower())[:-1]


def parse_and_verify_dates(df: pd.DataFrame, 
                           start_date: str,  
                           end_date: str) -> tuple[pd.Timestamp, str, pd.Timestamp, str]:
    """
    Converts the input start and end dates to timezone-aware datetime objects and their 
    corresponding string representations. Adjusts the dates to the first of the month 
    for start date and the last of the month for end date if they don't exist in the DataFrame.

    Parameters:
    start_date (str): The start date in the format 'DD.MM.YYYY'.
    end_date (str): The end date in the format 'DD.MM.YYYY'.

    Returns:
    tuple: A tuple containing:
        - start_date (pd.Timestamp): The start date as a timezone-aware datetime object.
        - start_date_str (str): The start date as a formatted string 'DD.MM.YYYY'.
        - end_date (pd.Timestamp): The end date as a timezone-aware datetime object.
        - end_date_str (str): The end date as a formatted string 'DD.MM.YYYY'.
    """
    # Timezone aware datetime objects are needed; otherwise DataFrame filtering would result in a TypeError
    start_date = pd.to_datetime(start_date, dayfirst=True).tz_localize('GMT')
    end_date = pd.to_datetime(end_date, dayfirst=True).tz_localize('GMT')
    
    # Adjust start date to the first of the month and end date to the last of the month
    start_date = start_date.replace(day=1)
    end_date = end_date + pd.offsets.MonthEnd(0)
    
    # Define datetime strings for easier plotting
    start_date_str = start_date.strftime('%d.%m.%Y')
    end_date_str = end_date.strftime('%d.%m.%Y')

    # Check if dates exist in the DataFrame
    if df is not None and not df.empty:
        df_start_date = df['event_start'].min()
        df_end_date = df['event_end'].max()
        
        # Adjust DataFrame start date to the first of the month
        df_start_date = df_start_date.replace(day=1)
        
        # Adjust DataFrame end date to the last of the month
        df_end_date = df_end_date + pd.offsets.MonthEnd(0)
        
        if start_date < df_start_date:
            start_date = df_start_date
            start_date_str = start_date.strftime('%d.%m.%Y')
        
        if end_date > df_end_date:
            end_date = df_end_date
            end_date_str = end_date.strftime('%d.%m.%Y')
                    
    return start_date, start_date_str, end_date, end_date_str


def plot_calendar(df: pd.DataFrame = None, start_date: str = '01.01.2024', end_date: str  = '01.02.2024', 
                  func: str = 'organiser', top_k: int = 10, streamlit: bool = False, list_func: bool = False):
    """
    Plots various types of visualizations based on the input event data within a specified date range.
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        DataFrame containing event data with necessary columns depending on the selected `func`.
        Default is None.
    start_date : str, optional
        The start date for filtering events in the format 'DD.MM.YYYY'.
        Default is '01.01.2024'.
    end_date : str, optional
        The end date for filtering events in the format 'DD.MM.YYYY'.
        Default is '01.02.2024'.
    func : str, optional
        The type of plot to generate. Must be one of the following:
        ['organiser', 'organiser_detail', 'event_category', 'event_category_by_organiser',
         'equip_details', 'equip_overall', 'participant_stats', 'participants_per_month'].
        Default is 'organiser'.
    top_k : int, optional
        The number of top categories to display in the plot for certain functions.
        Default is 10.
    streamlit : bool, optional
        If True, the plot will be displayed using Streamlit's `st.pyplot()`.
        Default is False.
    list_func : bool, optional
        If True, prints the available plotting functions and returns without generating a plot.
        Default is False.
        
    Returns:
    --------
    None or str
        If `streamlit` is True, returns the file path of the saved plot image.
        Otherwise, displays the plot using matplotlib.
    
    Raises:
    -------
    ValueError
        If `func` is not one of the available plotting functions.
    
    Notes:
    ------
    This function generates different types of plots based on the selected `func` parameter:
    - 'organiser': Plots events by organiser.
    - 'organiser_detail': Plots top `top_k` events by organiser details.
    - 'event_category': Plots events by event category.
    - 'event_category_by_organiser': Plots event categories grouped by organisers.
    - 'equip_details': Plots usage of different equipment types in events.
    - 'equip_overall': Plots overall tool usage in events.
    - 'participant_stats': Plots total participants by event category.
    - 'participants_per_month': Plots total participants per month.
    
    Example:
    --------
    >>> plot_calendar(df=events_df, start_date='01.01.2024', end_date='31.01.2024', func='organiser')
    """    
    # Define available plotting functions
    all_funcs = ['organiser', 
                 'organiser_detail', 
                 'event_category', 
                 'event_category_by_organiser',
                 'equip_details', 
                 'equip_overall', 
                 'participant_stats', 
                 'participants_per_month']
    
    if list_func:
        print(f"Available plotting functions: {all_funcs}")
        return
        
    if not func in all_funcs:
        print(f"Plotting function {func} not available. Check available functions by passing the 'list_func' parameter.")
        return
    
    # Parse dates and check if they exist in the DataFrame
    start_date, start_date_str, end_date, end_date_str = parse_and_verify_dates(df, start_date, end_date)
    
    # Define color map
    color_mapping = get_color_mapping('organiser')
    
    # Plot data for different functions
    if func == 'organiser_detail':
        # Filter data
        temp_df = df[(df['event_start'] >= start_date) & (df['event_end'] <= end_date)].copy()
        result_counts = temp_df['organiser_detail'].value_counts().head(top_k)
        result_counts = result_counts.sort_values(ascending=True)
        
        # Get colors from map for key in dict
        bar_colors = [color_mapping.get(df[df['organiser_detail'] == detail]['organiser'].iloc[0], '#333333') for detail in result_counts.index]

        # Define labels
        title = f"""Anzahl Veranstaltungen nach Veranstalterdetails (Top {top_k})
({start_date_str} bis {end_date_str}) | n={result_counts.values.sum()}"""
        xlabel = 'Anzahl Veranstaltungen'
        ylabel = 'Veranstalterdetails'
    
    elif func == 'organiser':
        result_counts = df[(df['event_start'] >= start_date) & (df['event_end'] <= end_date)]['organiser'].value_counts()
        bar_colors = [color_mapping.get(cat, '#333333') for cat in result_counts.index]
        title = f"Anzahl Veranstaltungen nach Veranstaltern ({start_date_str} bis {end_date_str}) | n={result_counts.values.sum()}"
        xlabel = 'Veranstalter'
        ylabel = 'Anzahl Veranstaltungen'
      
    elif func == 'event_category':
        result_counts = df[(df['event_start'] >= start_date) & (df['event_end'] <= end_date)]['event_category'].value_counts()
        color_mapping = get_color_mapping('event_category')
        bar_colors = [color_mapping.get(cat, '#333333') for cat in result_counts.index]
        title = f"Anzahl Veranstaltungen nach Veranstaltungstyp ({start_date_str} bis {end_date_str}) | n={result_counts.values.sum()}"
        xlabel = 'Veranstaltungstyp'
        ylabel = 'Anzahl Veranstaltungen'
    
    elif func == 'event_category_by_organiser':
        # Filter data
        temp_df = df[(df['event_start'] >= start_date) & (df['event_end'] <= end_date)].copy()
        result_counts = temp_df.groupby(['organiser', 'event_category']).size().unstack(fill_value=0)
        result_counts['total_events'] = result_counts.sum(axis=1)
        result_counts = result_counts.sort_values(by='total_events', ascending=False)
        result_counts = result_counts.drop('total_events', axis=1)
        
        # Define color mapping
        color_mapping = get_color_mapping(column='event_category')
        bar_colors = [color_mapping.get(cat, '#333333') for cat in result_counts.columns]
        
        # Define labels
        title = f"Anzahl Veranstaltungen nach Veranstaltungstyp und Veranstalter ({start_date_str} bis {end_date_str}) | n={result_counts.values.sum()}"
        xlabel = 'Veranstalter'
        ylabel = 'Anzahl Veranstaltungen'
        
    elif func == 'equip_details':        
        # Filter data
        equip_cols = {
            'equip_clevertouch': 'Clevertouch',
            'equip_dt': 'Design Thinking',
            'equip_eyetracking': 'Eye Tracking',
            'equip_monitor': 'Präsentationsmonitor',
            'equip_vr': 'VR'
        }    
        
        result_counts = (
            df
            [(df['event_start'] >= start_date) & (df['event_end'] <= end_date)][list(equip_cols.keys())]
            .sum()
            .sort_values(ascending=False)
            )
        
        # Define color mapping
        color_mapping = get_color_mapping('equip')
        bar_colors = [color_mapping.get(key, '#333333') for key in color_mapping]
        
        # Define labels
        title = f"Toolnutzung in Veranstaltungen nach Tooltyp ({start_date_str} bis {end_date_str}) | n={result_counts.values.sum()}‡"   
        ylabel = 'Anzahl Veranstaltungen'
        xlabel = """Tooltyp\n
‡ Nutzung mehrerer Tools pro Veranstaltung möglich"""
        
    elif func == 'equip_overall':
        result_counts = df[(df['event_start'] >= start_date) & (df['event_end'] <= end_date)]['equip'].value_counts()        
        bar_colors = ['#e5c494', '#b3b3b3']
        title = f"Toolnutzung in Veranstaltungen\n({start_date_str} bis {end_date_str}) | n={result_counts.values.sum()}"
        ylabel = 'Anzahl Veranstaltungen'
        xlabel = 'Toolnutzung'
        
    elif func == 'participant_stats':
        result_counts = (
            df[(df['event_start'] >= start_date) & (df['event_end'] <= end_date)]
            .groupby(['event_category'])['participant_count']
            .sum()
            .sort_values(ascending=False)
        )
        color_mapping = get_color_mapping('event_category')
        bar_colors = [color_mapping.get(key, '#333333') for key in result_counts.index]
        title = f"Anzahl Teilnehmende nach Veranstaltungstyp ({start_date_str} bis {end_date_str})‡ | n={result_counts.values.sum()}"
        xlabel = f"""Veranstaltungstyp\n
‡ Teilnehmendenzahl basiert auf Angabe der Veranstalter vor Durchführung einer Veranstaltung"""
        ylabel = 'Anzahl Teilnehmende'
        
    elif func == 'participants_per_month':
        result_counts = (
            df.groupby([df['event_start'].dt.year, df['event_start'].dt.month])['participant_count']
            .sum()
            )
        bar_colors = ['#e5c494']
        title = f"Anzahl Teilnehmende pro Monat ({start_date_str} bis {end_date_str})‡ | n={result_counts.values.sum()}"
        xlabel = f"""Monat\n
‡ Teilnehmendenzahl basiert auf Angabe der Veranstalter vor Durchführung einer Veranstaltung"""
        ylabel = 'Anzahl Teilnehmende'
        
    # Plot data
    if func in ['organiser', 'event_category', 'equip_details', 'participant_stats', 'participants_per_month']:
        plt.figure(figsize=(10, 8))
        plt.grid(True, which='both', linestyle='-', linewidth=0.2)
        
        bars = plt.bar(list(range(1, len(result_counts) + 1)), result_counts.values, color=bar_colors)
        for bar in bars:
            bar_height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, bar_height, int(bar_height), ha='center', va='bottom')
        
        # xticks
        if func in ['equip_details']:
            plt.xticks(ticks=list(range(1, len(result_counts) + 1)), labels=[equip_cols[key] for key in result_counts.index], rotation=0, ha='center') 
        elif func in ['participant_stats', 'event_category', 'organiser']:
            plt.xticks(ticks=list(range(1, len(result_counts) + 1)), labels=result_counts.index, rotation=0, ha='center') 
        else:
            plt.xticks(ticks=list(range(1, len(result_counts) + 1)), labels=result_counts.index, rotation=45, ha='right') 
    
    elif func in ['organiser_detail']:    
        plt.figure(figsize=(12, 8))
        plt.grid(True, which='both', linestyle='-', linewidth=0.2)
        bars = plt.barh(list(range(1, len(result_counts) + 1)), result_counts.values, color=bar_colors)
        for bar in bars:
            bar_width = bar.get_width()
            plt.text(bar_width + 0.1, bar.get_y() + bar.get_height() / 2, int(bar_width), ha='left', va='center')
        plt.yticks(ticks=list(range(1, len(result_counts) + 1)), labels=result_counts.index)
        plt.ylim(0.3, len(result_counts) + 0.7)
        
    elif func in ['event_category_by_organiser']:
        ax = result_counts.plot(kind='bar', stacked=False, figsize=(12, 8), color=bar_colors)
        plt.grid(True, which='both', linestyle='-', linewidth=0.2)
        for container in ax.containers:
            ax.bar_label(container)
        plt.xticks(rotation=0, ha='center')
        
    elif func in ['equip_overall']:
        plt.figure(figsize=(6, 9))
        plt.grid(True, which='both', linestyle='-', linewidth=0.2)
        bars = plt.bar(list(range(1, len(result_counts) + 1)), result_counts.values, color=bar_colors)
        for bar in bars:
            bar_height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, bar_height, int(bar_height), ha='center', va='bottom')
        plt.xticks(ticks=list(range(1, len(result_counts) + 1)), labels=['Toolnutzung', 'Keine Toolnutzung'], rotation=0, ha='center') 
        plt.xlim(0.5, len(result_counts) + 0.5)
        
    # Plot labels
    plt.title(title, weight='bold', fontsize=13, pad=10)
    plt.xlabel(xlabel, weight='bold', labelpad=25)
    plt.ylabel(ylabel, weight='bold', labelpad=10)
    
    # Plot legends
    if func == 'organiser_detail':
        handles = [plt.Rectangle((0,0),1,1, color=color_mapping[key]) for key in color_mapping]    
        labels = color_mapping.keys()
        plt.legend(handles, labels, title="Veranstalter", loc='lower right')
        
    elif func in ['event_category_by_organiser']:
        plt.legend(title='Veranstaltungstyp')    
    
    # Tight layout
    plt.tight_layout()
    
    # Save and show plot
    img_title = create_img_title(title)
    plt.savefig(f"{str(output_dir.joinpath(img_title))}", dpi=300, bbox_inches='tight')
    
    # If running the function via the streamlit app use st.pyplot()
    if streamlit:
        st.pyplot(plt)
        return f"{output_dir.joinpath(img_title)}.png"
    
    plt.show() 