import io

def to_excel_bytes(df):
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='xlsxwriter')
    return output.getvalue()

def to_excel_bytes_multiple_sheets(sheets: dict):
    """
    sheets: dict con formato {'nombre_hoja': dataframe}
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name)
    return output.getvalue()