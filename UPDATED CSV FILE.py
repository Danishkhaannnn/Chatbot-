import pandas as pd
import re

# Load the CSV file
df = pd.read_csv('cleaned_data.csv')

# Define the patterns to match and remove unwanted text
pattern_1 = r'contact us.*?particles_67dab947d6237.*?px'
pattern_2 = r'jQuerydocument\.readyfunction.*?Digital Innovation'

# Apply regex to remove both unwanted text patterns
df['content'] = df['content'].apply(lambda x: re.sub(pattern_1, '', str(x)))
df['content'] = df['content'].apply(lambda x: re.sub(pattern_2, '', str(x)))

# Clean any extra spaces left after the removal
df['content'] = df['content'].str.replace(r'\s+', ' ', regex=True).str.strip()

# Save the updated file
df.to_csv('cleaned_data_updated.csv', index=False)

print("Text removed and file saved as 'cleaned_data_updated.csv'.")
