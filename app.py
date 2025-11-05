from flask import Flask, render_template, request, send_file
import pandas as pd
import os
from io import BytesIO, StringIO
import json

app = Flask(__name__)

# --- Clean and Merge Logic ---
def clean_and_merge_feedspot_files(files):
    """Clean and merge multiple Feedspot Excel/CSV files."""
    cleaned_dfs = []

    for i, file in enumerate(files):
        filename = file.filename
        ext = os.path.splitext(filename)[-1].lower()
        print(f"📂 Reading file {i+1}/{len(files)}: {filename}")

        try:
            # 🟢 Read based on file type
            if ext == ".xlsx":
                df = pd.read_excel(file, skiprows=1, header=0)
            elif ext == ".csv":
                df = pd.read_csv(file, skiprows=1, header=0)
            else:
                print(f"⚠️ Skipping unsupported file type: {filename}")
                continue

            # 🔴 Drop rows containing "TOTAL" in any column
            df = df[~df.astype(str).apply(lambda row: row.str.contains("TOTAL", case=False, na=False)).any(axis=1)]

            # 🧹 Drop empty rows
            df = df.dropna(how="all").reset_index(drop=True)

            # 🔴 Drop the first column
            if df.shape[1] > 1:
                df = df.iloc[:, 1:]

            print(f"   ➜ Cleaned rows: {len(df)} | Columns: {len(df.columns)}")
            cleaned_dfs.append(df)

        except Exception as e:
            print(f"❌ Error reading {filename}: {str(e)}")

    if not cleaned_dfs:
        return None

    # 🔹 Merge vertically
    merged_df = pd.concat(cleaned_dfs, ignore_index=True)
    print(f"\n✅ Merged successfully: {len(merged_df)} rows, {len(merged_df.columns)} columns.")
    return merged_df


# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/merge', methods=['POST'])
def merge_files():
    uploaded_files = request.files.getlist('files')

    if not uploaded_files:
        return "⚠️ No files uploaded!", 400

    merged_df = clean_and_merge_feedspot_files(uploaded_files)
    if merged_df is None:
        return "⚠️ No valid files to merge!", 400

    # Collect metadata
    meta = {
        "files": [f.filename for f in uploaded_files],
        "rows": [],
        "total_rows": len(merged_df),
        "total_cols": len(merged_df.columns)
    }

    for f in uploaded_files:
        try:
            ext = os.path.splitext(f.filename)[-1].lower()
            if ext == ".xlsx":
                df = pd.read_excel(f, skiprows=1, header=0)
            elif ext == ".csv":
                df = pd.read_csv(f, skiprows=1, header=0)
            else:
                continue
            meta["rows"].append(f"{f.filename}: {len(df)} rows")
        except:
            meta["rows"].append(f"{f.filename}: error reading")

    # Decide format
    download_type = request.form.get('download_type')
    metadata_json = json.dumps(meta)

    if download_type == 'excel':
        output = BytesIO()
        merged_df.to_excel(output, index=False)
        output.seek(0)
        response = send_file(
            output,
            as_attachment=True,
            download_name="merged_feedspot.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif download_type == 'csv':
        output = StringIO()
        merged_df.to_csv(output, index=False)
        mem = BytesIO(output.getvalue().encode('utf-8'))
        response = send_file(
            mem,
            as_attachment=True,
            download_name="merged_feedspot.csv",
            mimetype="text/csv"
        )
    else:
        return "Invalid download type", 400

    # Add metadata as custom header
    response.headers["X-Metadata"] = metadata_json
    return response



if __name__ == '__main__':
    # For local testing
    app.run(debug=True)
