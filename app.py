import streamlit as st
import pandas as pd
import zipfile
from labcal import process_cal, plot_cal


def reset_session_state():
    """
    Reset the session state.
    """
    st.session_state.button_clicked = False
    st.session_state.uploaded_file = None
    st.session_state.date_start = None
    st.session_state.date_end = None


def process():
    st.session_state.button_clicked = True
    
    # Set output_dir to save plots
    output_dir = plot_cal.set_output_dir()

    # Start processing calendar file
    ics_file = st.session_state.uploaded_file
    st.subheader(f':blue[**Kalender** wird bearbeitet ⏳]')
    
    # Load calendar
    ics_content = ics_file.read().decode('utf-8')
    cal = process_cal.streamlit_load_and_parse_calendar(ics_content)
    st.write(f':green[**{len(cal.events)} Einträge** in *{ics_file.name}* gefunden.]')
    
    # Create pd.DataFrame from Calendar object
    df = process_cal.create_dataframe_from_calendar(cal=cal, verbose=False)
    
    # Clean the DataFrame
    clean_df = process_cal.clean_calendar_dataframe(df, verbose=False)
    
    # Parse provided start and end date and check if they exist in the DataFrane
    start_date, start_date_str, end_date, end_date_str = plot_cal.parse_and_verify_dates(clean_df, 
                                                                                         st.session_state.date_start, 
                                                                                         st.session_state.date_end)
    
    # Create DataFrame for provided time period
    select_df = clean_df.loc[(clean_df['event_start'] >= start_date) & (clean_df['event_end'] <= end_date)].reset_index(drop=True).copy()

    # Print adjustments for start_date and end_date if applicable
    start_date_session = pd.to_datetime(st.session_state.date_start).tz_localize('GMT').date()
    end_date_session = pd.to_datetime(st.session_state.date_end).tz_localize('GMT').date()

    if start_date.date() != start_date_session:
        st.write(f"Das Startdatum **{start_date_session.strftime('%d.%m.%Y')}** wurde im Kalender nicht gefunden und auf den ersten verfügbaren Kalenderzeitpunkt **{start_date.date().strftime('%d.%m.%Y')}** festgelegt.")
    
    if end_date.date() != end_date_session:
        st.write(f"Das Enddatum **{end_date_session.strftime('%d.%m.%Y')}** wurde im Kalender nicht gefunden und auf den letzten verfügbaren Kalenderzeitpunkt **{end_date.date().strftime('%d.%m.%Y')}** festgelegt.")

    st.write(f':green[Für den Zeitraum {start_date_str} bis {end_date_str} existieren **{len(select_df)}** Kalendereinträge.]')
    
    # Define tabs for displaying the plots
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(['Plot 1',
                                                                           'Plot 2',
                                                                           'Plot 3',
                                                                           'Plot 4',
                                                                           'Plot 5', 
                                                                           'Plot 6',
                                                                           'Plot 7',
                                                                           'Plot 8',
                                                                           'Tabelle',
                                                                           '⬇️ Download'])
        
    with tab1:
        # Plot event_categories
        eventcat_title = plot_cal.plot_calendar(select_df, 
                                                start_date=start_date_str, 
                                                end_date=end_date_str,
                                                func='event_category', 
                                                streamlit=True)
    with tab2:
        # Plot organiser
        organiser_title = plot_cal.plot_calendar(select_df, 
                                                 start_date=start_date_str, 
                                                 end_date=end_date_str,
                                                 func='organiser', 
                                                 streamlit=True)
    with tab3:
        # Plot event_categories by organiser
        eventcat_by_organiser_title = plot_cal.plot_calendar(select_df, 
                                                             start_date=start_date_str, 
                                                             end_date=end_date_str, 
                                                             func='event_category_by_organiser', 
                                                             streamlit=True)
    with tab4:
        # Plot organiser_detail
        organiser_detail_title = plot_cal.plot_calendar(select_df, 
                                                        start_date=start_date_str, 
                                                        end_date=end_date_str, 
                                                        func='organiser_detail',
                                                        top_k=20, 
                                                        streamlit=True)
    
    with tab5:
        # Plot overall equipment stats
        all_equip_title = plot_cal.plot_calendar(select_df, 
                                                 start_date=start_date_str, 
                                                 end_date=end_date_str, 
                                                 func='equip_overall', 
                                                 streamlit=True)
    
    with tab6:
        # Plot specific equipment stats
        equip_stats_title = plot_cal.plot_calendar(select_df, 
                                                   start_date=start_date_str, 
                                                   end_date=end_date_str, 
                                                   func='equip_details', 
                                                   streamlit=True)
    with tab7:
        # Plot overall participant stats
        participants_title = plot_cal.plot_calendar(select_df, 
                                                    start_date=start_date_str, 
                                                    end_date=end_date_str, 
                                                    func='participant_stats', 
                                                    streamlit=True)
    
    with tab8:
        # Plot monthly participant stats
        participants_per_month_title = plot_cal.plot_calendar(select_df, 
                                                              start_date=start_date_str, 
                                                              end_date=end_date_str, 
                                                              func='participants_per_month', 
                                                              streamlit=True)

    with tab9:
        st.dataframe(select_df)

    with tab10:
        # Create a .zip archive to download all plot at once 
        zip_filename = f"explab_plots_{start_date_str.replace('.', '_')}_{end_date_str.replace('.', '_')}.zip"
        
        # Include a .xlsx with the selected DataFrame in the zip
        excel_filename = f"explab_{start_date_str.replace('.', '_')}_{end_date_str.replace('.', '_')}.xlsx"
        
        with zipfile.ZipFile(str(output_dir.joinpath(zip_filename)), 'w') as zip_f:
            if eventcat_title:
                zip_f.write(eventcat_title)
            if organiser_title:
                zip_f.write(organiser_title)
            if eventcat_by_organiser_title:
                zip_f.write(eventcat_by_organiser_title)
            if organiser_detail_title:
                zip_f.write(organiser_detail_title)
            if all_equip_title:
                zip_f.write(all_equip_title)
            if equip_stats_title:
                zip_f.write(equip_stats_title)
            if participants_title:
                zip_f.write(participants_title)
            if participants_per_month_title:
                zip_f.write(participants_per_month_title)
            
            # Convert timezone aware columns to time stamps as Excel can't handle them
            df_xlsx = pd.DataFrame()
            
            for col in select_df.columns:
                if isinstance(select_df[col].dtype, pd.DatetimeTZDtype):
                    df_xlsx[col] = select_df[col].dt.strftime('%d.%m.%Y %H:%M:%S')
                else:
                    df_xlsx[col] = select_df[col]

            df_xlsx.to_excel(str(output_dir.joinpath(excel_filename)), index=False)
            zip_f.write(str(output_dir.joinpath(excel_filename)))
        
        # Provide a download button for downloading the .zip
        with open(str(output_dir.joinpath(zip_filename)), 'rb') as file:
            st.download_button(label='Alle Plots herunterladen', data=file, file_name=zip_filename, 
                               mime='application/zip', on_click=download_finished)
                    
            
def download_finished():
    st.subheader(':blue[✅ Download abgeschlossen.]')
    st.button('Zurück zur Startseite', on_click=reset_session_state)
        
  
def main():    
    if 'button_clicked' not in st.session_state:
        st.session_state.button_clicked = False

    # Site header
    if not st.session_state.button_clicked:
        col_logo, col_title = st.columns(2, vertical_alignment='center')
        
        with col_logo:
            st.image('./assets/lab_logo.svg', width=200)
        with col_title:
            st.subheader(':blue[Kalenderauswertung]')
            with st.expander('Anleitung'):
                st.write("""
                        1. Über den Button **Browse files** kann die Kalenderdatei im `.ics` Format hochgeladen werden.
                        2. Anschließend erfolgt die Auswahl des Auswertungszeitraums über die Felder **Von** und **Bis**.
                        3. Ein Klick auf den Button **Auswertung starten** generiert die Statistiken.
                        4. Über den Reiter **⬇️ Downloads** können alle Statistiken im `.png` Format heruntergeladen werden.
                        """)
        
        # File upload
        st.session_state.uploaded_file = st.file_uploader('Kalenderdatei (**.ics**) auswählen', type=['ics'])

        # Filter for time period
        col1, col2 = st.columns(2)

        with col1:
            st.session_state.date_start = st.date_input('**Von**', format='DD.MM.YYYY')
        with col2:
            st.session_state.date_end = st.date_input('**Bis**', format='DD.MM.YYYY')

        # Processing
        if st.session_state.uploaded_file is not None:
            st.button('Auswertung starten', on_click=process)
              

if __name__ == '__main__':
    main()