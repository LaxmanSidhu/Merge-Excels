from flask import Flask, render_template, request, send_file
import pandas as pd
from io import BytesIO, StringIO

app = Flask(__name__)

# --- Clean function ---
def clean_excel(file):
    """Cleans one Excel file (skips garbage rows)."""
    df = pd.read_excel(file, skiprows=1, header=0)
    df = df[~df.astype(str).apply(lambda row: row.str.contains("TOTAL", case=False, na=False)).any(axis=1)]
    df = df.dropna(how="all").reset_index(drop=True)
    return df


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/merge', methods=['POST'])
def merge_files():
    uploaded_files = request.files.getlist('files')

    if not uploaded_files:
        return "⚠️ No files uploaded!", 400

    all_dfs = []
    for file in uploaded_files:
        df = clean_excel(file)
        all_dfs.append(df)

    merged_df = pd.concat(all_dfs, ignore_index=True)

    # Store merged dataframe in session memory (not on disk)
    # But since Render disables server sessions, we just hold it in memory for this request
    # Instead, we regenerate file in memory when user clicks download

    # Convert to Excel in memory
    excel_buffer = BytesIO()
    merged_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    # Convert to CSV in memory
    csv_buffer = StringIO()
    merged_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Store in global variables temporarily (not disk)
    app.config['MERGED_EXCEL'] = excel_buffer
    app.config['MERGED_CSV'] = csv_buffer.getvalue()

    return render_template('index.html', success=True)


@app.route('/download/<filetype>')
def download(filetype):
    if filetype == "excel":
        excel_buffer = app.config.get('MERGED_EXCEL')
        if not excel_buffer:
            return "⚠️ No merged Excel available yet!", 400
        excel_buffer.seek(0)
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name="merged_feedspot.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif filetype == "csv":
        csv_data = app.config.get('MERGED_CSV')
        if not csv_data:
            return "⚠️ No merged CSV available yet!", 400
        return send_file(
            BytesIO(csv_data.encode()),
            as_attachment=True,
            download_name="merged_feedspot.csv",
            mimetype="text/csv"
        )

    else:
        return "Invalid file type!", 400


if __name__ == '__main__':
    app.run(debug=True)
