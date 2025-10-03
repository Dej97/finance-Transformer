import streamlit as st
import pandas as pd
from io import BytesIO

def transpose_row(row, headers):
    """Transpose a single row into multiple rows"""
    transposed_rows = []
    
    # Fixed values that stay the same for all transposed rows
    fixed_columns = headers[:11]  # journal to Adjusted activity
    fixed_values = row[:11]
    
    # Activity columns start from index 11 (Balance) onwards
    activity_headers = headers[11:]
    activity_values = row[11:]
    
    for i, (activity_header, value) in enumerate(zip(activity_headers, activity_values)):
        # Skip if value is missing (represented as '-', empty, or NaN)
        if (isinstance(value, str) and value.strip() in ['-', '']) or pd.isna(value):
            continue
            
        # Skip if value is 0 or '0'
        if value == 0 or (isinstance(value, str) and value.strip() == '0'):
            continue
            
        # Create new row: fixed values + activity header + value
        new_row = fixed_values + [activity_header, value]
        transposed_rows.append(new_row)
    
    return transposed_rows

def to_excel(df):
    """Convert dataframe to Excel format"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transformed_Data')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.set_page_config(
        page_title="Data Transformer",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("🔄 Data Transformer")
    st.write("Upload your file to transpose and clean financial data")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'txt', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            # Read file based on extension
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                # Try different delimiters
                try:
                    df = pd.read_csv(uploaded_file, delimiter='\t')
                except:
                    df = pd.read_csv(uploaded_file, delimiter=',')
            
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
                
                # Also remove rows where Activity contains "Balance" (case insensitive)
                new_df = new_df[~new_df['Activity'].astype(str).str.contains('Balance', case=False, na=False)]
                
                # Convert Amount to numeric and remove rows with 0
                new_df['Amount'] = pd.to_numeric(new_df['Amount'], errors='coerce')
                new_df = new_df[new_df['Amount'] != 0]
                new_df = new_df.dropna(subset=['Amount'])
                
                filtered_count = len(new_df)
                removed_count = initial_count - filtered_count
                
                st.subheader("✅ Transformed Data")
                st.dataframe(new_df, use_container_width=True)
                
                # Show removal statistics
                st.info(f"**Transformation Statistics:**\n"
                       f"- Original transposed rows: {initial_count}\n"
                       f"- Removed rows (Balance/0 values): {removed_count}\n"
                       f"- Final valid rows: {filtered_count}")
                
                # Create two columns for download buttons
                col1, col2 = st.columns(2)
                
                # CSV Download button
                with col1:
                    csv = new_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="transformed_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                # Excel Download button
                with col2:
                    excel_data = to_excel(new_df)
                    st.download_button(
                        label="📊 Download as Excel",
                        data=excel_data,
                        file_name="transformed_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                st.success(f"🎉 Transformation complete! Created {len(new_df)} valid rows.")
                
            else:
                st.warning("No valid data found to transform")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("💡 Tip: Make sure your file has the correct format. For CSV files, use tab or comma delimiter.")

    else:
        st.markdown("""
        ### 📋 How to use:
        1. **Upload** your CSV, TXT, or Excel file
        2. **View** the original and transformed data
        3. **Download** the cleaned data in CSV or Excel format
        
        ### 🔄 What this app does:
        - Transposes activity columns into separate rows
        - Removes rows with 'Balance' in Activity column
        - Removes rows with 0 values in Amount column
        - Skips missing values (represented as '-')
        """)

if __name__ == "__main__":
    main()