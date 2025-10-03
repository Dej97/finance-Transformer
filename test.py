import streamlit as st
import pandas as pd
from io import BytesIO

# Check for available Excel engines
try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

def transpose_row(row, headers):
    """Transpose a single row into multiple rows"""
    transposed_rows = []
    
    # Fixed values that stay the same for all transposed rows
    fixed_values = row[:11] if len(row) >= 11 else row + [None] * (11 - len(row))
    
    # Activity columns start from index 11 onwards
    activity_headers = headers[11:] if len(headers) > 11 else []
    activity_values = row[11:] if len(row) > 11 else []
    
    for activity_header, value in zip(activity_headers, activity_values):
        # Skip if value is missing
        if pd.isna(value) or (isinstance(value, str) and value.strip() in ['-', '']):
            continue
            
        # Skip if value is 0
        try:
            if float(value) == 0:
                continue
        except (ValueError, TypeError):
            continue
            
        # Create new row
        new_row = fixed_values + [activity_header, value]
        transposed_rows.append(new_row)
    
    return transposed_rows

def to_excel(df):
    """Convert dataframe to Excel format with fallback engines"""
    output = BytesIO()
    
    if OPENPYXL_AVAILABLE:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transformed_Data')
    elif XLSXWRITER_AVAILABLE:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Transformed_Data')
    else:
        raise ImportError("No Excel writer available. Install openpyxl or xlsxwriter.")
    
    return output.getvalue()

def main():
    st.set_page_config(
        page_title="Data Transformer",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("🔄 Data Transformer")
    st.write("Upload your file to transpose and clean financial data")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'txt'])
    
    if uploaded_file is not None:
        try:
            # Read file - only CSV/TXT for now to avoid Excel dependency issues
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                if not OPENPYXL_AVAILABLE and not XLSXWRITER_AVAILABLE:
                    st.error("❌ Cannot read Excel files - no Excel library installed")
                    st.info("Please upload CSV or TXT files instead, or check requirements.txt")
                    return
                # Try to read Excel if libraries available
                try:
                    df = pd.read_excel(uploaded_file)
                except Exception as e:
                    st.error(f"Cannot read Excel file: {e}")
                    return
            else:
                # Try different delimiters for CSV/TXT
                file_content = uploaded_file.read().decode('utf-8')
                uploaded_file.seek(0)  # Reset file pointer
                
                for delimiter in ['\t', ',', ';']:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, delimiter=delimiter)
                        st.success(f"✅ File read successfully with '{delimiter}' delimiter")
                        break
                    except Exception:
                        continue
                else:
                    st.error("❌ Could not read the file. Please check the format.")
                    return
            
            st.subheader("📊 Original Data")
            st.dataframe(df, use_container_width=True)
            
            # Get headers
            headers = df.columns.tolist()
            
            # Process data
            all_transposed_rows = []
            
            for _, row in df.iterrows():
                transposed_rows = transpose_row(row.tolist(), headers)
                all_transposed_rows.extend(transposed_rows)
            
            # Create new dataframe
            if all_transposed_rows:
                new_headers = headers[:11] + ['Activity', 'Amount']
                new_df = pd.DataFrame(all_transposed_rows, columns=new_headers)
                
                # Remove rows where Activity is "Balance"
                initial_count = len(new_df)
                new_df = new_df[new_df['Activity'] != 'Balance']
                new_df = new_df[~new_df['Activity'].astype(str).str.contains('Balance', case=False, na=False)]
                
                # Convert Amount to numeric and remove rows with 0
                new_df['Amount'] = pd.to_numeric(new_df['Amount'], errors='coerce')
                new_df = new_df[new_df['Amount'] != 0]
                new_df = new_df.dropna(subset=['Amount'])
                
                filtered_count = len(new_df)
                
                st.subheader("✅ Transformed Data")
                st.dataframe(new_df, use_container_width=True)
                
                st.info(f"**Transformation Statistics:**\n"
                       f"- Original transposed rows: {initial_count}\n"
                       f"- Final valid rows: {filtered_count}")
                
                # Download options
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = new_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="transformed_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    try:
                        excel_data = to_excel(new_df)
                        st.download_button(
                            label="📊 Download as Excel",
                            data=excel_data,
                            file_name="transformed_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.button(
                            "📊 Excel Export Unavailable",
                            disabled=True,
                            help=f"Excel export disabled: {str(e)}",
                            use_container_width=True
                        )
                
                st.success(f"🎉 Transformation complete! Created {len(new_df)} valid rows.")
                
            else:
                st.warning("No valid data found to transform")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

    else:
        st.markdown("""
        ### 📋 How to use:
        1. **Upload** your CSV or TXT file (Excel support coming soon)
        2. **View** the original and transformed data  
        3. **Download** the cleaned data in CSV format
        
        ### 🔄 What this app does:
        - Transposes activity columns into separate rows
        - Removes rows with 'Balance' in Activity column
        - Removes rows with 0 values in Amount column
        - Skips missing values (represented as '-')
        """)

if __name__ == "__main__":
    main()
