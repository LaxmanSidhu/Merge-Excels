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
        try:
            df = clean_excel(file)
            all_dfs.append(df)
        except Exception as e:
            return f"Error processing {file.filename}: {str(e)}", 500

    merged_df = pd.concat(all_dfs, ignore_index=True)

    # Decide format based on button clicked
    download_type = request.form.get('download_type')

    if download_type == 'excel':
        output = BytesIO()
        merged_df.to_excel(output, index=False)
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="merged_feedspot.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif download_type == 'csv':
        output = StringIO()
        merged_df.to_csv(output, index=False)
        mem = BytesIO(output.getvalue().encode('utf-8'))
        return send_file(
            mem,
            as_attachment=True,
            download_name="merged_feedspot.csv",
            mimetype="text/csv"
        )

    else:
        return "Invalid download type", 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
