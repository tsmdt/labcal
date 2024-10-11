import re
import pandas as pd
import warnings
from ics import Calendar
from pathlib import Path


warnings.filterwarnings("ignore", category=FutureWarning)


def load_and_parse_calendar(filepath: str) -> Calendar:
    """
    Loads and parses an iCalendar (.ics) file into a Calendar object.
    """
    # Create Path object from filepath string
    cal_filepath = Path(filepath)

    # Open the file
    with open(cal_filepath, 'r', encoding='utf-8') as fin:
        cal_raw = fin.read()
        
    # Return the parsed Calendar object
    return Calendar(cal_raw)


def streamlit_load_and_parse_calendar(file) -> Calendar:
    return Calendar(file)


def parse_event(event: list[str]) -> dict:
    """
    Parse a serialized event from a Calendar object and return the event as a dict.
    """
    event_dict = {}
    
    for item in event:
        if ':' in item:
            key, value = item.split(':', 1)
            event_dict[key] = value
            
    return event_dict


def clean_event_data(event: list[str]) -> list:
    """
    Clean a split str event and remove various chars and whitespaces.
    """
    clean_event = []
    
    for line in event:
        event = re.sub(r'\r', '', line)
        event = re.sub(r'\\n', '¶', event) # set '¶' as stop char for splitting in proces_description()
        event = re.sub(r'\\', '', event)
        clean_event.append(event.strip())
        
    return clean_event


def create_dataframe_from_calendar(cal: Calendar, verbose: bool = False) -> pd.DataFrame:
    """
    Converts events from a given Calendar object into a pandas DataFrame.

    This function processes events from a Calendar object by serializing and cleaning the event data,
    parsing the cleaned data into a dictionary format, and then converting that dictionary into a pandas DataFrame.
    Optionally, it can print detailed processing information if the verbose flag is set to True.

    Parameters:
    cal (Calendar): An object representing the calendar which contains the events to be processed.
    verbose (bool, optional): If set to True, prints detailed processing information. Default is False.

    Returns:
    pd.DataFrame: A DataFrame containing the calendar events with columns representing event attributes.

    Internal Functions:
    print_verbose(): Prints detailed information about the processing steps and intermediate data structures.
    """
    def print_verbose():        
        print(f'PROCESSING STATS:')
        print(f'=================')
        print(f'First item of calendar_data:\n')
        for event in calendar_data[:1]:
            event_string = '\n'.join(event)
            print(f"{event_string}\n")
        print(f'Found {len(columns)} keys/columns: {columns}')
        print(f'\nLENGTH OF LISTS AND DICTS')
        print(f'-------------------------')
        print(f'calendar.events count: {len(cal.events)}')
        print(f'calendar_data count: {len(calendar_data)}')
        for key in calendar_dict.keys():
            max_length = 0
            if max_length < len(calendar_dict[key]):
                max_length = len(calendar_dict[key])
        print(f'max. calendar_dict count: {max_length}')
        print(f'\nCALENDAR_DICT:')
        print(f'--------------')
        for key in calendar_dict.keys():
            print(f'{key}: {calendar_dict[key]}')        
    
    # Create list from Calendar.events and clean resulting event strings
    calendar_data = []
    for event in cal.events:
        event_lines = event.serialize().split('\n')
        clean_event = clean_event_data(event_lines)
        calendar_data.append(clean_event)
    
    # Parse cleaned calendar_data and return a dict with all relevant keys for each event (BEGIN, CREATED ...)
    parsed_events = [parse_event(event) for event in calendar_data]
    
    # Create a set of unique dict.keys() that will be the columns of the DataFrame
    columns = set()
    for event in parsed_events:
        columns.update(event.keys())
        
    # Create a new calendar_dict with those columns as keys
    calendar_dict = {}
    for col in columns:
        if not col in calendar_dict:
            calendar_dict[col] = []
            
    # Populate the dict with the values of parsed_events
    for event in parsed_events:
        for key in calendar_dict.keys():
            # If column key of calendar_dict is found in parsed_event append parsed_event value
            if key in event.keys():
                calendar_dict[key].append(event[key])
            # Else append None
            else:
                calendar_dict[key].append(None)
    
    # Create pd.DataFrame from calendar_dict
    df = pd.DataFrame(calendar_dict)

    # Print processing stats if verbose flag is True
    if verbose:
        print_verbose()
        
    return df


def process_description(series: list[str], verbose: bool = False) -> pd.Series:    
    """
    Processes a list of event description strings, extracting and cleaning various details about each event.
    If `verbose` is True prints all strings that could not be cleaned.
    
    Args:
        `series (list[str])`: A list of strings containing event description details.
        
    Returns:
        pd.Series: A pandas Series containing cleaned and extracted event details, which includes:
        `event_category (str)`: The category of the event.
        `event_description (str)`: A detailed description of the event.
        `organiser (str)`: The main organiser of the event.
        `organiser_detail (str)`: Additional details about the organiser.
        `participant_count (str)`: The number of participants.
        `equipment (bool)`: Whether any equipment is needed.
        `equipment_vr (bool)`: Whether VR equipment is needed.
        `equipment_eye_tracking (bool)`: Whether eye tracking equipment is needed.
        `equipment_clevertouch (bool)`: Whether Clevertouch equipment is needed.
        `equipment_large_monitor (bool)`: Whether a large monitor is needed.
        `equipment_design_thinking (bool)`: Whether design thinking equipment is needed.
        `catering (bool)`: Whether catering is required.
        `notes (str)`: Additional notes about the event.
    """
    # Variables for storing split and cleaned data
    event_category = None
    event_description = None
    organiser = None
    organiser_detail = None
    participant_count = None
    equipment = None
    equipment_vr = None
    equipment_eye_tracking = None
    equipment_clevertouch = None
    equipment_large_monitor = None
    equipment_design_thinking = None
    catering = None
    notes = None   
    
    # Internal functions for data splitting and cleaning
    def split_item(item):
        split_item = item.split(' ', maxsplit=1)
        return split_item[1].strip() if len(split_item) > 1 else None
     
    def clean_event_category(event_category: str) -> str:
        patterns = {
        'Interne Veranstaltung': ['interne veran', 
                                  'ub intern'],
        'Führung': ['veranstaltung/führung'],
        'Lehrveranstaltung': ['seminar'],
        'Workshop': ['vr-einführung']
         }
        
        for clean_string, keys in patterns.items():
            if any(key in event_category.lower() for key in keys):
                return clean_string
            
        return event_category
    
    def clean_organiser(organiser: str) -> str:
        patterns = {
            'UB': ['ub'],
            'Uni': ['uni'],
         }
        
        for clean_string, keys in patterns.items():
            if any(key in organiser.lower() for key in keys):
                return clean_string
            
        return organiser
     
    def clean_organiser_detail(organiser_detail: str) -> str:
        """
        Main mapping dictionary to map different name variations to the same key.
        """
        patterns = {
        'Institut für Sport': ['sport'],
        'Social Science': ['sowi', 
                 'social science', 
                 'powi'],
        'BWL': ['ls bwl', 
                'wirtschaftspädag',
                'sales services'],
        'Jura': ['fak jura', 
                 'rechtswissenschaft'],
        'Wirtschaftsinformatik': ['wirtschaftsinformatik'],
        'Philosophische Fakultät': ['philosophische', 
                                    'phil fak',
                                    'philfak',
                                    'anglistik',
                                    'germanistik'],
        'Stud.-Initiative X': ['student group x'],
        'Stud.-Initiative Y': ['student group y'],
        'Stud.-Initiative Z': ['student group z'],
        'Universitäts-IT': ['uni it'],
        'Universitätsbibliothek': ['explab', 
                                   'ub',
                                   'fdz'],
        'Uni Verwaltung': ['verwaltung'],
        'Fachschaftsrat': ['fsr', 
                           'fachschaftsr']
         }
        
        for clean_string, keys in patterns.items():
            if any(re.search(key, organiser_detail.lower()) for key in keys):
                return clean_string
         
        return organiser_detail
    
    def clean_equipment(equipment_split: list[str]) -> dict[str: bool]:        
        patterns = {
            'equipment_vr': ['vr', 
                             'virtual'],
            'equipment_eye_tracking': ['eye', 
                                       'tracking'],
            'equipment_clevertouch': ['clever', 
                                      'mobiler'],
            'equipment_large_monitor': ['praesentations', 
                                        'großer monitor', 
                                        'präsentations'],
            'equipment_design_thinking': ['dt', 
                                          'design thinking', 
                                          'thinking']
        }
        
        equipment_vr = False
        equipment_eye_tracking = False
        equipment_clevertouch = False
        equipment_large_monitor = False
        equipment_design_thinking = False
        
        for item in equipment_split:
            for var, keys in patterns.items():
                if any(key in item.lower() for key in keys):
                    if var == 'equipment_vr':
                        equipment_vr = True
                    elif var == 'equipment_eye_tracking':
                        equipment_eye_tracking = True
                    elif var == 'equipment_clevertouch':
                        equipment_clevertouch = True
                    elif var ==  'equipment_large_monitor':
                        equipment_large_monitor = True
                    elif var == 'equipment_design_thinking':
                        equipment_design_thinking = True

        return {
            'equipment_vr': equipment_vr,
            'equipment_eye_tracking': equipment_eye_tracking,
            'equipment_clevertouch': equipment_clevertouch,
            'equipment_large_monitor': equipment_large_monitor,
            'equipment_design_thinking': equipment_design_thinking
        }
    
    # Check if series is a list
    if isinstance(series, list):  
        for item in series:
            
            # Check if item of list is not None and a string
            if pd.notna(item) and isinstance(item, str):  
                
                ### Process "Kategorie" items
                if item.startswith('Kategorie'):
                    result = split_item(item)
                    if result and re.search(r':|\s', result):
                        event_category_split = re.split(r':|,', result, maxsplit=1)
                        
                        # Check if event_category_split contains more than 1 item
                        if len(event_category_split) > 1:
                            event_category = event_category_split[0].strip()
                            event_description = event_category_split[1].strip()
                        
                        # Data cleaning
                        if event_category:
                            event_category = clean_event_category(event_category)
                            
                ### Process "Veranstalter" items    
                elif item.startswith('Veranstalter'):
                    result = split_item(item)
                    if result and re.search(r':|\s', result):
                        organiser_split = re.split(r':', result, maxsplit=1)

                        # Divide organiser_split in separate variables if it contains != 1 item
                        if len(organiser_split) != 1:
                            organiser = organiser_split[0].strip()
                            organiser_detail = organiser_split[1].strip() 
                        # else:
                        #     organiser_detail = organiser
                        
                        if organiser:
                            organiser = clean_organiser(organiser)
                        
                        if organiser_detail:
                            organiser_detail = clean_organiser_detail(organiser_detail)

                        else:
                            organiser_detail = organiser

                ### Process "Teilnehmer" items        
                elif item.startswith('Teilnehmer'):
                    result = split_item(item)
                    if result:
                        result = result.strip()

                        # If string contains '-' (e.g. 10-20) split it and match all digits after '-'
                        if result and '-' in result:
                            participant_split = result.split('-')
                            participant_count = re.match(r'\d+', participant_split[1].strip()).group(0)

                        # If no '-' is found try only matching digits; else set participant_count to None
                        else:
                            participant_search = re.search(r'\d+', result)
                            if participant_search:
                                participant_count = participant_search.group(0)
                            else:
                                participant_count = None
                    
                    # If no result set participant_count to None
                    else:
                        participant_count = None

                ### Process "Technik" items
                elif item.startswith('Technik'):
                    result = split_item(item)
                    if result:
                        equipment_split = result.split(',')
                        equipment_split = [item.strip() for item in equipment_split]                    
                    else:
                        equipment = False    
                        
                    if equipment_split:
                        equipment_dict = clean_equipment(equipment_split)
                        equipment = True if True in equipment_dict.values() else False
                        equipment_vr = equipment_dict['equipment_vr']
                        equipment_eye_tracking = equipment_dict['equipment_eye_tracking']
                        equipment_clevertouch = equipment_dict['equipment_clevertouch']
                        equipment_large_monitor = equipment_dict['equipment_large_monitor']
                        equipment_design_thinking = equipment_dict['equipment_design_thinking']

                ### Process "Catering" items
                elif item.startswith('Catering'):
                    result = split_item(item)
                    if result and 'ja' in result:
                        catering = True
                    else:
                        catering = False
                    
                ### Process "Anmerkung" items
                elif item.startswith('Anmerkung'):
                    result = split_item(item)
                    if result:
                        notes = result.strip()
                    else:
                        notes = None
                        
    return pd.Series([event_category, event_description, organiser, organiser_detail, participant_count,
                      equipment, equipment_vr, equipment_eye_tracking, equipment_clevertouch, 
                      equipment_design_thinking, equipment_large_monitor, catering, notes])

    
def clean_calendar_dataframe(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """
    Cleans and processes a calendar DataFrame, extracting and formatting event details.

    Args:
        `df (pd.DataFrame)`: The input DataFrame containing calendar event data.
        `verbose (bool)`: If True, prints warnings about missing columns during processing. Default is False.

    Returns:
        `pd.DataFrame`: A cleaned DataFrame with reformatted date columns, dropped irrelevant columns, and new columns created from processed event descriptions. The columns include:
        `id (str)`: Unique identifier for each event.
        `event_end` (`pd.Timestamp`): End date and time of the event.
        `event_start (pd.Timestamp)`: Start date and time of the event.
        `event_title (str)`: Title of the event.
        `created (pd.Timestamp)`: Creation date of the event.
        `event_desc_list (list[str])`: List of event description strings.
        `event_desc (str)`: Raw event description.
        `event_category (str)`: Cleaned event category, e.g. Lehrveranstaltung, Workshop etc.
        `event_description (str)`: Detailed description of the event.
        `organiser (str)`: Main organiser of the event, e.g. UB, Uni, Studis, Extern.
        `organiser_detail (str)`: Additional details about the organiser.
        `participant_count (str)`: Number of participants.
        `equip (bool)`: Indicator if any equipment is required.
        `equip_vr (bool)`: Indicator if VR equipment is required.
        `equip_eyetracking (bool)`: Indicator if eye tracking equipment is required.
        `equip_clevertouch (bool)`: Indicator if Clevertouch equipment is required.
        `equip_dt (bool)`: Indicator if design thinking equipment is required.
        `equip_monitor (bool)`: Indicator if a large monitor is required.
        `catering (bool)`: Indicator if catering is required.
        `notes (str)`: Additional notes about the event.
    """
    # Create a temporary copy of the DataFrame to work with
    temp_df = df.copy()
                
    # Drop columns that have less than 5 % non-null values
    threshold = len(temp_df) / 100 * 5
    temp_df_processed = temp_df.dropna(axis=1, thresh=threshold)
    
    # Drop columns that do not contain relevant data
    columns_to_drop = ['X-MICROSOFT-CDO-BUSYSTATUS', 'CLASS', 'PRIORITY', 'DTSTAMP', 
                       'TRANSP', 'SEQUENCE', 'LAST-MODIFIED', 'BEGIN', 'END', 'STATUS']
    
    for col in temp_df_processed.columns:
        if col in columns_to_drop:
            temp_df_processed = temp_df_processed.drop(columns=[col])
    
    # Split the data of the DESCRIPTION column and store it in the new column DESCRIPTION_RAW
    temp_df_processed['DESCRIPTION_RAW'] = temp_df_processed['DESCRIPTION'].str.split('¶')
    
    # Rename columns for easier data access
    temp_df_processed = temp_df_processed.rename(columns={
        'UID': 'id',
        'DTEND': 'event_end',
        'DTSTART': 'event_start',
        'SUMMARY': 'event_title',
        'CREATED': 'created',
        'DESCRIPTION_RAW': 'event_desc_list',
        'DESCRIPTION': 'event_desc'
        })
    
    # Clean the data of event_desc_list and create new columns accordingly
    temp_df_processed[[
        'event_category', 'event_description', 'organiser', 'organiser_detail', 'participant_count', 
        'equip', 'equip_vr', 'equip_eyetracking', 'equip_clevertouch', 'equip_dt', 'equip_monitor', 
        'catering', 'notes'
        ]] = temp_df_processed['event_desc_list'].apply(lambda x: process_description(x, verbose=verbose))
    
    # Re-order columns for better clarity
    new_column_layout = ['id', 'created', 'event_title', 'event_start', 'event_end', 'event_category', 
                         'event_description', 'event_desc_list', 'event_desc', 'organiser', 'organiser_detail',
                         'participant_count', 'equip', 'equip_clevertouch', 'equip_dt', 'equip_eyetracking',
                         'equip_monitor', 'equip_vr', 'catering', 'notes']
    temp_df_processed = temp_df_processed.filter(new_column_layout)
    
    # Convert columns to appropriate dtypes
    column_dtypes = {
        'int': ['participant_count'],
        'date': ['created', 'event_start', 'event_end'],
        'bool': ['equip', 'equip_clevertouch', 'equip_dt', 'equip_eyetracking', 'equip_monitor', 
                 'equip_vr', 'catering']
    }
    
    for dtype, columns in column_dtypes.items():
        for col in columns:
            if col in temp_df_processed.columns:
                if dtype == 'int':
                    temp_df_processed[col] = temp_df_processed[col].fillna(0).astype('int16')
                elif dtype == 'date':
                    temp_df_processed[col] = pd.to_datetime(temp_df_processed[col], errors='coerce')
            else:
                if verbose:
                    print(f'{col} not a column. Skipping ...')

    return temp_df_processed