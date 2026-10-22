import os
import glob
import pandas as pd

# Cesty k priečinkom
input_dir = '/Users/tomaskovac/Desktop/BC/Python/DATA/Bitcoin_row'
output_dir = '/Users/tomaskovac/Desktop/BC/Python/DATA'
output_file = os.path.join(output_dir, 'bitcoin_merged.csv')

# Získame všetky CSV súbory v zdrojovom adresári
csv_files = glob.glob(os.path.join(input_dir, '*.csv'))

# Pomocný zoznam pre načítané DataFrame-y
df_list = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        df_list.append(df)
        print(f'Načítané: {os.path.basename(file)} (riadkov: {len(df)})')
    except Exception as e:
        print(f'Chyba pri načítaní {file}: {e}')

# Skontrolujeme, či sme niečo načítali
if not df_list:
    raise ValueError("Žiadne CSV súbory neboli načítané. Skontrolujte cestu.")

# Zlúčime všetky DataFrame-y vertikálne (riadok pod riadkom)
merged_df = pd.concat(df_list, ignore_index=True)

# Voliteľne: tu môžete pridať ďalšie úpravy, napr.
# merged_df.drop_duplicates(inplace=True)
# merged_df.sort_values(by='timestamp', inplace=True)

# Uložíme zlúčený DataFrame do CSV súboru
merged_df.to_csv(output_file, index=False)
print(f'Zlúčený súbor uložený do: {output_file}')
