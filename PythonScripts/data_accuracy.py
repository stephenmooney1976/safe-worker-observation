import pandas as pd


def df_equality_check(df1=None, df2=None):
    merge_df = df1.merge(df2, how='outer', indicator=True)
    diff1 = merge_df.query('_merge != "both"')
    diff2 = pd.concat([df1, df2]).drop_duplicates(keep=False)
    col_diff = set(df1.columns).symmetric_difference(df2.columns)
    return f'''Lengths of diffs: {len(diff1)}, {len(diff2)}\nColumn diff: {col_diff}\nComparison: {df1.compare(df2)}\nIs Equal: {df1.equals(df2)}'''


if __name__ == '__main__':
    script_df = pd.read_csv('../data/csv/script_results.csv', index_col='NAME').sort_values(by=['NAME'])
    access_df = pd.read_csv('../data/csv/access_results.csv', index_col='NAME').sort_values(by=['NAME'])
    results = df_equality_check(script_df, access_df)
    print(results)
    print('end')
