import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="My Supplements",
    page_icon="💊",
)

st.title("My Supplements")

st.divider()

# Define the data
mock_data = {
    'Drug Id': [1, 2, 3, 4, 5],
    'Drug Name': ['Ibuprofen', 'Amoxicillin', 'Lisinopril', 'Metformin', 'Atorvastatin'],
    'Dosages Left': [20, 10, 15, 25, 30],
    'Next Refill Date': ['2024-07-01', '2024-07-15', '2024-07-20', '2024-08-01', '2024-08-15'],
    'Instructions': [
        'Take one tablet every 6 hours as needed for pain',
        'Take one capsule three times a day with food',
        'Take one tablet daily in the morning',
        'Take one tablet twice a day with meals',
        'Take one tablet daily in the evening'
    ]
}

# Create the DataFrame
df = pd.DataFrame(mock_data)

# Updates df with a value in a specified column and drug id
def update_table(supp_id, col, new_val):
    # supp id has to be a valid drug id, param has to be valid col
    df.loc[df['Drug Id'] == supp_id, col] = new_val

def add_rows():
    pass

# to_remove is an array of drug id's to remove
def remove_rows(to_remove):
    pass

# can perform CRUD operations on data editor
editable_table = st.data_editor(df, num_rows='dynamic')

