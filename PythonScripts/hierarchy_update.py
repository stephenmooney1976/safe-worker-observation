import pandas as pd
import numpy as np
from data_accuracy import df_equality_check

pd.set_option('display.expand_frame_repr', False, 'display.max_rows', None)


def dup_name_check():
    tmp_df = pd.read_excel('../excel/DO_ORG_Flat_Download.xls', sheet_name='Sheet 1', index_col=None)
    tmp_df['TitledName'] = tmp_df['Name'].str.title()
    tmp_df['DupName'] = tmp_df.duplicated(['TitledName'], keep=False)
    tmp_df['DupCount'] = tmp_df.sort_values(
        by=['TitledName', 'USER_ID']).groupby(by=tmp_df['TitledName'], sort=False).cumcount()
    tmp_df.insert(4, 'Name2', np.where(
        tmp_df['DupName'] == 0, tmp_df['Name'], tmp_df['Name'] + tmp_df['DupCount'].add(1).astype(str)))
    return tmp_df.iloc[:, :-3]


if __name__ == '__main__':
    dups = dup_name_check()
    do_org_flat = pd.read_excel('../excel/DO_ORG_Flat.xls', sheet_name='Sheet 1', index_col=None)
    results = df_equality_check(dups, do_org_flat)
    print(results)
    print('end of program')
